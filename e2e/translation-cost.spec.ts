import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Cost accounting: the summary after a chapter run, the «Вартість» dialog, the price table,
// reasoning level and batch size in ⚙. e2e/server.py answers every LLM call with 10 input and
// 5 output tokens. Needs WORKBENCH_CREDENTIALS_KEY.

async function createProjectWithBook(request: APIRequestContext, title: string) {
    const created = await request.post('/api/projects', { data: { title, status: 'translation' } });
    expect(created.ok()).toBeTruthy();
    const project = await created.json();
    const epubPath = path.join(__dirname, '..', 'test-data', 'sample-without-cover.epub'); // two paragraphs
    const upload = await request.post('/upload', {
        headers: { 'X-Project-Id': project.projectId },
        multipart: { file: { name: 'sample-without-cover.epub', mimeType: 'application/epub+zip', buffer: fs.readFileSync(epubPath) } },
    });
    expect(upload.ok()).toBeTruthy();
    return project;
}

async function createConnection(request: APIRequestContext, providerId: string) {
    const response = await request.post('/api/connections', {
        data: { providerId, displayName: `${providerId} cost e2e`, credentials: { apiKey: `${providerId}-e2e-key` } },
    });
    expect(response.ok(), await response.text()).toBeTruthy();
    const connection = await response.json();
    expect((await request.post(`/api/connections/${connection.connectionId}/test`)).ok()).toBeTruthy();
    return connection;
}

async function openFirstChapter(page: Page, title: string) {
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

async function translateChapter(page: Page) {
    const button = page.locator('#translate-chapter-button');
    await button.click();
    await expect(button).toHaveText('Перекласти розділ');
    await expect(button).toBeEnabled();
}

async function selectEngine(page: Page, label: string) {
    const toggle = page.locator('#translation-provider-toggle');
    await toggle.getByText(label, { exact: true }).click();
    await expect(toggle.getByLabel(label)).toBeChecked();
}

test('chapter run shows the cost; the «Вартість» dialog and the price table follow the stored tokens', async ({ page, request }) => {
    test.setTimeout(90_000);
    const title = `Cost ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    const connections = [await createConnection(request, 'claude'), await createConnection(request, 'openai')];
    const summary = page.locator('#translation-run-summary');

    try {
        await openFirstChapter(page, title);

        // Claude: priced in the initial table (2 / 10 per 1M): 10 in + 5 out = $0.00007.
        await selectEngine(page, 'Claude');
        await translateChapter(page);
        await expect(summary).toHaveText('≈ $0.0001 · 1 батч · 15 токенів');

        // GPT answers as gpt-4.1-nano, which has no price: the tokens are counted, the cost is not.
        await selectEngine(page, 'GPT');
        await translateChapter(page);
        await expect(summary).toHaveText('ціну не задано · 1 батч · 15 токенів');

        await page.locator('#project-cost-button').click();
        const dialog = page.locator('#project-cost-dialog');
        await expect(dialog).toBeVisible();
        await expect(dialog.locator('.project-cost-total')).toContainText('2 виклики · 30 токенів');
        await expect(dialog.locator('.project-cost-table').first()).toContainText('claude / claude-sonnet-5-5');
        await expect(dialog.locator('.project-cost-table').first()).toContainText('openai / gpt-4.1-nano');
        await expect(dialog.locator('.project-cost-table').first().locator('tr', { hasText: 'gpt-4.1-nano' })).toContainText('ціну не задано');
        await expect(dialog.getByText('Ціну не задано для: gpt-4.1-nano')).toBeVisible();
        await expect(dialog.locator('.project-cost-table').nth(1)).toContainText('01 · Chapter 1');
        await expect(dialog.locator('.project-cost-table').nth(2)).toContainText('Переклад');
        expect(await dialog.innerText()).not.toContain('This is a test EPUB'); // never the book text

        // Set the missing price: cost is computed from the stored tokens, nothing is re-run.
        await dialog.getByRole('button', { name: 'Змінити ціни' }).click();
        const settings = page.locator('#translation-settings-dialog');
        await expect(settings).toBeVisible();
        const row = settings.locator('.model-price-row[aria-label="gpt-4.1-nano"]');
        await expect(row).toHaveCount(1);
        await row.getByLabel('Вхід · gpt-4.1-nano').fill('100');
        await row.getByLabel('Вихід · gpt-4.1-nano').fill('400');
        await settings.getByRole('button', { name: 'Зберегти' }).click();
        await expect(settings).toBeHidden();
        await page.locator('#project-cost-button').click();
        await expect(dialog.locator('.project-cost-table').first().locator('tr', { hasText: 'gpt-4.1-nano' })).toContainText('≈ $0.0030'); // 10·100 + 5·400 per 1M
        await expect(dialog.getByText('Ціну не задано для')).toHaveCount(0);
        await dialog.getByRole('button', { name: 'Закрити', exact: true }).click();
    } finally {
        await request.put('/api/model-prices', { data: { prices: [{ model: 'gpt-4.1-nano', inputPerMTok: null, outputPerMTok: null }] } });
        await request.delete(`/api/projects/${project.projectId}`);
        for (const connection of connections) await request.delete(`/api/connections/${connection.connectionId}`);
    }
});

test('reasoning level (GPT, Gemini) and batch size are project settings in ⚙', async ({ page, request }) => {
    test.setTimeout(90_000);
    const title = `Cost settings ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    const connections = [await createConnection(request, 'claude')];
    const settings = page.locator('#translation-settings-dialog');

    try {
        await openFirstChapter(page, title);
        await page.locator('#translation-settings-button').click();
        await expect(settings).toBeVisible();
        await expect(settings.locator('[data-engine="claude"] .translation-reasoning-select')).toHaveCount(0);
        const gpt = settings.locator('[data-engine="openai"] .translation-reasoning-select');
        const gemini = settings.locator('[data-engine="gemini"] .translation-reasoning-select');
        await expect(gpt).toHaveValue('low'); // default
        await expect(gemini).toHaveValue('low');
        await expect(gpt.locator('option')).toHaveText(['Мінімальний', 'Низький', 'Середній']);

        // Out-of-range batch size is refused with a message, nothing is saved.
        await settings.locator('#translation-batch-paragraphs').fill('0');
        await settings.getByRole('button', { name: 'Зберегти' }).click();
        await expect(settings.locator('#translation-settings-error')).toContainText('від 1 до 20');
        await expect(settings).toBeVisible();

        await gpt.selectOption('minimal');
        await gemini.selectOption('medium');
        await settings.locator('#translation-batch-paragraphs').fill('1');
        await settings.locator('#translation-batch-chars').fill('800');
        await settings.getByRole('button', { name: 'Зберегти' }).click();
        await expect(settings).toBeHidden();
        await expect.poll(async () => {
            const saved = await (await request.get(`/api/projects/${project.projectId}`)).json();
            return [saved.aiConfiguration.translationReasoning, saved.aiConfiguration.translationBatch];
        }).toEqual([{ openai: 'minimal', gemini: 'medium' }, { maxChars: 800, maxParagraphs: 1 }]);

        // One paragraph per batch: the two-paragraph chapter takes two batches.
        await selectEngine(page, 'Claude');
        await translateChapter(page);
        await expect(page.locator('#translation-run-summary')).toHaveText('≈ $0.0001 · 2 батчі · 30 токенів');

        // The saved values come back when ⚙ is opened again.
        await page.locator('#translation-settings-button').click();
        await expect(settings.locator('[data-engine="openai"] .translation-reasoning-select')).toHaveValue('minimal');
        await expect(settings.locator('#translation-batch-chars')).toHaveValue('800');
        await settings.getByRole('button', { name: 'Скасувати' }).click();
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
        for (const connection of connections) await request.delete(`/api/connections/${connection.connectionId}`);
    }
});

test('the price table and the cost dialog fit a phone', async ({ page, request }) => {
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 390, height: 844 });
    const title = `Cost phone ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    try {
        await openFirstChapter(page, title);
        await page.locator('#translation-settings-button').click();
        const settings = page.locator('#translation-settings-dialog');
        await expect(settings.locator('.model-price-row').first()).toBeVisible();
        for (const control of await settings.locator('.model-price-row input').all()) {
            const box = await control.boundingBox();
            expect(box?.height ?? 0).toBeGreaterThanOrEqual(44);
            expect((box?.x ?? 0) + (box?.width ?? 0)).toBeLessThanOrEqual(390);
        }
        await settings.getByRole('button', { name: 'Скасувати' }).click();
        await page.locator('#project-cost-button').click();
        await expect(page.locator('#project-cost-status')).toContainText('ще немає записаних викликів');
        const box = await page.locator('#project-cost-dialog .project-cost-content').boundingBox();
        expect((box?.x ?? 0) + (box?.width ?? 0)).toBeLessThanOrEqual(390);
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});
