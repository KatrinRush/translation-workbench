import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// «Перекласти кілька розділів…»: a server-side queue with a budget limit, progress, pause/resume,
// the summary and «Скасувати перекладене чергою». long-chapter.epub has 12 chapters.
// e2e/server.py answers every call with 10 input + 5 output tokens; "[[slow]]" in the project's
// translation rules makes each call take ~0.6 s. Needs WORKBENCH_CREDENTIALS_KEY.

async function createProjectWithBook(request: APIRequestContext, title: string) {
    const created = await request.post('/api/projects', { data: { title, status: 'translation' } });
    expect(created.ok()).toBeTruthy();
    const project = await created.json();
    const epubPath = path.join(__dirname, '..', 'test-data', 'long-chapter.epub');
    const upload = await request.post('/upload', {
        headers: { 'X-Project-Id': project.projectId },
        multipart: { file: { name: 'long-chapter.epub', mimeType: 'application/epub+zip', buffer: fs.readFileSync(epubPath) } },
    });
    expect(upload.ok()).toBeTruthy();
    return project;
}

async function createConnection(request: APIRequestContext, providerId: string) {
    const response = await request.post('/api/connections', {
        data: { providerId, displayName: `${providerId} queue e2e`, credentials: { apiKey: `${providerId}-e2e-key` } },
    });
    expect(response.ok(), await response.text()).toBeTruthy();
    const connection = await response.json();
    expect((await request.post(`/api/connections/${connection.connectionId}/test`)).ok()).toBeTruthy();
    return connection;
}

async function openProject(page: Page, title: string) {
    await page.goto('/');
    await page.locator('.project-card').filter({ hasText: title }).getByRole('button', { name: 'Відкрити проєкт' }).click();
    await page.getByRole('button', { name: 'Переклад', exact: true }).click();
    const showStructure = page.getByRole('button', { name: 'Переглянути структуру книги' });
    const firstChapter = page.locator('.chapter-button').first();
    await expect(showStructure.or(firstChapter).first()).toBeVisible();
    if (!(await firstChapter.isVisible())) await showStructure.click();
    await firstChapter.click();
    await expect(page.locator('.translation-row').first()).toBeVisible();
}

// «Ще ▾» holds the secondary chapter actions: open it, then press the item.
async function openChapterMore(page: Page, item: string) {
    await page.locator('#chapter-more-button').click();
    await page.getByRole('menuitem', { name: item }).click();
}

async function selectEngine(page: Page, label: string) {
    const toggle = page.locator('#translation-provider-toggle');
    await toggle.getByText(label, { exact: true }).click();
    await expect(toggle.getByLabel(label)).toBeChecked();
}

async function openDialog(page: Page) {
    await openChapterMore(page, 'Перекласти кілька розділів…');
    const dialog = page.locator('#queue-dialog');
    await expect(dialog).toBeVisible();
    await expect(dialog.locator('#queue-estimate .bulk-select-summary')).toBeVisible();
    return dialog;
}

test('DeepL explains why the queue is not available', async ({ page, request }) => {
    const title = `Queue deepl ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    try {
        await openProject(page, title);
        let message = '';
        page.once('dialog', (alert) => { message = alert.message(); void alert.dismiss(); });
        await openChapterMore(page, 'Перекласти кілька розділів…');
        expect(message).toContain('лише для Claude, GPT і Gemini');
        await expect(page.locator('#queue-dialog')).toBeHidden();
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});

test('estimate, reminder, run to the summary, then undo what the queue translated', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Queue run ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    const connection = await createConnection(request, 'claude');
    try {
        await openProject(page, title);
        await selectEngine(page, 'Claude');
        const dialog = await openDialog(page);
        await expect(dialog.getByText('Перевір баланс у консолі провайдера')).toBeVisible();
        await expect(dialog.locator('#queue-estimate')).toContainText('Буде перекладено: 12 розділів');
        await expect(dialog.locator('#queue-estimate')).toContainText('Оцінка вартості: ≈ $');
        await expect(dialog.locator('#queue-budget')).toBeEnabled();

        // a range of two chapters narrows the estimate
        await dialog.getByLabel('Діапазон розділів').check();
        await dialog.locator('#queue-from').selectOption('1');
        await dialog.locator('#queue-to').selectOption('2');
        await expect(dialog.locator('#queue-estimate')).toContainText('Буде перекладено: 2 розділи');
        await dialog.getByRole('button', { name: 'Запустити чергу' }).click();
        await expect(dialog).toBeHidden();

        const panel = page.locator('#queue-panel');
        await expect(panel).toBeVisible();
        await expect(panel.locator('#queue-panel-summary')).toContainText('Розділів: перекладено 2', { timeout: 60_000 });
        await expect(panel.locator('#queue-panel-title')).toContainText('Завершено');
        await expect(panel.locator('#queue-panel-line')).toContainText('≈ $');
        await expect(panel.getByRole('button', { name: 'Пауза' })).toBeHidden();

        // the open chapter shows the new translation without a reload
        const state = await (await request.get(`/api/projects/${project.projectId}/translation-queues/latest`)).json();
        expect(state.queue.status).toBe('completed');
        expect(state.queue.summary.chapters.done).toBe(2);
        await expect(page.locator('.translation-row').first().locator('.translation-paragraph')).toHaveText('Claude переклад');
        await expect(page.locator('.translation-row').first().locator('.variant-tab').first()).toHaveText('✓ Claude');

        // after a reload the finished queue is still shown
        await page.reload();
        await openProject(page, title);
        await expect(page.locator('#queue-panel-summary')).toContainText('Розділів: перекладено 2');

        // undo: confirm shows the counts; the translations go away
        page.once('dialog', (confirm) => {
            expect(confirm.message()).toContain('Буде видалено варіантів, створених чергою');
            void confirm.accept();
        });
        await page.getByRole('button', { name: 'Скасувати перекладене чергою…' }).click();
        await expect(page.locator('#queue-panel-summary')).toContainText('Перекладене чергою скасовано.');
        await expect(page.locator('.translation-row').first().locator('.variant-tab')).toHaveCount(0);
        await expect(page.locator('.translation-row').first().locator('.translation-paragraph')).toHaveText('');
        const structure = await (await request.get(`/api/projects/${project.projectId}/book/structure`)).json();
        const translated = structure.chapters.flatMap((chapter: any) => chapter.elements).filter((element: any) => element.translationText);
        expect(translated).toHaveLength(0);
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
        await request.delete(`/api/connections/${connection.connectionId}`);
    }
});

test('pause, resume and stop; the budget limit stops the queue at a batch boundary', async ({ page, request }) => {
    test.setTimeout(180_000);
    const title = `Queue control ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    const connection = await createConnection(request, 'claude');
    try {
        expect((await request.put(`/api/projects/${project.projectId}/translation-rules`, { data: { translationRules: '[[slow]]' } })).ok()).toBeTruthy();
        await openProject(page, title);
        await selectEngine(page, 'Claude');

        let dialog = await openDialog(page);
        await dialog.getByLabel('Діапазон розділів').check();
        await dialog.locator('#queue-from').selectOption('1');
        await dialog.locator('#queue-to').selectOption('3');
        await dialog.getByRole('button', { name: 'Запустити чергу' }).click();
        const panel = page.locator('#queue-panel');
        await expect(panel.locator('#queue-panel-line')).toContainText(/розділ \d+\/3 · батч \d+\/\d+ · ≈ \$/);

        await panel.getByRole('button', { name: 'Пауза' }).click();
        await expect(panel.locator('#queue-panel-title')).toContainText('На паузі');
        await page.waitForTimeout(1200); // the batch that was already running is finished first
        const paused = await (await request.get(`/api/projects/${project.projectId}/translation-queues/latest`)).json();
        await page.waitForTimeout(1800);
        const still = await (await request.get(`/api/projects/${project.projectId}/translation-queues/latest`)).json();
        expect(still.queue.progress.batchesDone).toBe(paused.queue.progress.batchesDone);

        await panel.getByRole('button', { name: 'Продовжити' }).click();
        await expect(panel.locator('#queue-panel-title')).toContainText('Іде переклад');
        page.once('dialog', (confirm) => { void confirm.accept(); });
        await panel.getByRole('button', { name: 'Зупинити' }).click();
        await expect(panel.locator('#queue-panel-title')).toContainText('Зупинено', { timeout: 15_000 });
        await expect(panel.locator('#queue-panel-summary')).toContainText('Розділів:');
        await panel.getByRole('button', { name: 'Закрити' }).click();
        await expect(panel).toBeHidden();

        // budget: the limit is a few fake calls; the queue stops with the remaining chapters skipped
        await request.put(`/api/projects/${project.projectId}/translation-rules`, { data: { translationRules: '' } });
        dialog = await openDialog(page);
        await dialog.getByLabel('Діапазон розділів').check();
        await dialog.locator('#queue-from').selectOption('1');
        await dialog.locator('#queue-to').selectOption('12');
        await dialog.getByLabel('перекласти й ті, що мають переклад').check();
        await expect(dialog.locator('#queue-estimate')).toContainText('Буде перекладено:');
        await dialog.locator('#queue-budget').fill('0.0003');
        await dialog.getByRole('button', { name: 'Запустити чергу' }).click();
        await expect(panel.locator('#queue-panel-title')).toContainText('досягнуто межі', { timeout: 60_000 });
        const limited = await (await request.get(`/api/projects/${project.projectId}/translation-queues/latest`)).json();
        expect(limited.queue.status).toBe('budget_reached');
        expect(limited.queue.spentUsd).toBeLessThanOrEqual(0.0003);
        expect(limited.queue.summary.chapters.skipped + limited.queue.summary.chapters.partial).toBeGreaterThan(0);
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
        await request.delete(`/api/connections/${connection.connectionId}`);
    }
});
