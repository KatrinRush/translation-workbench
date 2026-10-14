import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// «Обрати для файлу весь розділ з…» and «Показувати весь розділ у варіанті X».
// sample-without-cover.epub has two paragraphs; e2e/server.py answers "Claude переклад" / "GPT переклад".
// Needs WORKBENCH_CREDENTIALS_KEY.

async function createProjectWithBook(request: APIRequestContext, title: string) {
    const created = await request.post('/api/projects', { data: { title, status: 'translation' } });
    expect(created.ok()).toBeTruthy();
    const project = await created.json();
    const epubPath = path.join(__dirname, '..', 'test-data', 'sample-without-cover.epub');
    const upload = await request.post('/upload', {
        headers: { 'X-Project-Id': project.projectId },
        multipart: { file: { name: 'sample-without-cover.epub', mimeType: 'application/epub+zip', buffer: fs.readFileSync(epubPath) } },
    });
    expect(upload.ok()).toBeTruthy();
    return project;
}

async function createConnection(request: APIRequestContext, providerId: string) {
    const response = await request.post('/api/connections', {
        data: { providerId, displayName: `${providerId} bulk e2e`, credentials: { apiKey: `${providerId}-e2e-key` } },
    });
    expect(response.ok(), await response.text()).toBeTruthy();
    const connection = await response.json();
    expect((await request.post(`/api/connections/${connection.connectionId}/test`)).ok()).toBeTruthy();
    return connection;
}

// «Ще ▾» holds the secondary chapter actions: open it, then press the item.
async function openChapterMore(page: Page, item: string) {
    await page.locator('#chapter-more-button').click();
    await page.getByRole('menuitem', { name: item }).click();
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

async function translateChapter(page: Page, engine: string) {
    const toggle = page.locator('#translation-provider-toggle');
    await toggle.getByText(engine, { exact: true }).click();
    await expect(toggle.getByLabel(engine)).toBeChecked();
    const button = page.locator('#translate-chapter-button');
    await button.click();
    await expect(button).toHaveText('Перекласти розділ');
    await expect(button).toBeEnabled();
}

const activeTab = (row: ReturnType<Page['locator']>) => row.locator('.variant-tab[aria-selected="true"]');

async function paragraphs(request: APIRequestContext, projectId: string) {
    const structure = await (await request.get(`/api/projects/${projectId}/book/structure`)).json();
    return structure.chapters[0].elements.filter((element: any) => element.type === 'paragraph');
}

const fileState = async (request: APIRequestContext, projectId: string) =>
    (await paragraphs(request, projectId)).map((paragraph: any) => [paragraph.translationText, paragraph.reviewed]);

test('the whole chapter in one engine: dialog with examples, skipped proofread, undo and redo in one step', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Bulk select ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    const connections = [await createConnection(request, 'claude'), await createConnection(request, 'openai')];
    try {
        await openFirstChapter(page, title);
        await translateChapter(page, 'Claude');
        await translateChapter(page, 'GPT'); // both paragraphs: Claude (in the file) and GPT
        const [, second] = await paragraphs(request, project.projectId);
        // the second paragraph is proofread meanwhile
        expect((await request.put(`/api/paragraphs/${second.paragraphId}`, { data: { translationText: second.translationText, reviewed: true } })).ok()).toBeTruthy();
        await page.reload();
        await openFirstChapter(page, title);
        const rows = page.locator('.translation-row');

        // Dialog: only engines that have variants, with counts; nothing is changed by opening it
        await openChapterMore(page, 'Обрати для файлу весь розділ з…');
        const dialog = page.locator('#bulk-select-dialog');
        await expect(dialog).toBeVisible();
        await expect(dialog.locator('input[name="bulk-engine"]')).toHaveCount(2);
        await expect(dialog.getByText('Claude · 2 абзаци з варіантом')).toBeVisible();
        await expect(dialog.getByText('GPT · 2 абзаци з варіантом')).toBeVisible();
        await dialog.getByLabel(/GPT/).check();
        // the preview names what will happen and shows examples (was → will be)
        await expect(dialog.locator('.bulk-select-summary')).toHaveText('Буде: змінено 1, без варіанта 0, пропущено перевірених чи вичитаних 1.');
        await expect(dialog.locator('.bulk-select-examples li')).toHaveCount(1);
        await expect(dialog.locator('.bulk-select-examples li').first()).toHaveText('№1: Claude переклад → GPT переклад');
        expect(await fileState(request, project.projectId)).toEqual([['Claude переклад', false], ['Claude переклад', true]]);

        await dialog.getByRole('button', { name: 'Обрати для файлу', exact: true }).click();
        await expect(dialog).toBeHidden();
        await expect(page.locator('#chapter-bulk-status')).toHaveText('Змінено 1, без варіанта 0, пропущено перевірених чи вичитаних 1.');
        await expect(activeTab(rows.nth(0))).toHaveText('✓ GPT');
        expect(await fileState(request, project.projectId)).toEqual([['GPT переклад', false], ['Claude переклад', true]]); // the proofread one is untouched

        // one undo step restores the whole action, redo applies the very same variants again
        await page.locator('#undo-translation').click();
        await expect.poll(() => fileState(request, project.projectId)).toEqual([['Claude переклад', false], ['Claude переклад', true]]);
        await expect(page.locator('#chapter-bulk-status')).toContainText('Масовий вибір скасовано');
        await expect(rows.nth(0).locator('.variant-tab[data-in-file="true"]')).toHaveText('✓ Claude');
        await page.locator('#redo-translation').click();
        await expect.poll(() => fileState(request, project.projectId)).toEqual([['GPT переклад', false], ['Claude переклад', true]]);
        await expect(page.locator('#chapter-bulk-status')).toContainText('Масовий вибір повторено');
        await expect(page.locator('#undo-translation')).toBeEnabled();

        // Including proofread paragraphs: a warning in the dialog and one confirmation that clears «Перевірено»
        await openChapterMore(page, 'Обрати для файлу весь розділ з…');
        await dialog.getByLabel(/GPT/).check();
        await dialog.getByLabel('включно з перевіреними й вичитаними').check();
        await expect(dialog.locator('.bulk-select-summary')).toHaveText('Буде: змінено 1, без варіанта 0, пропущено перевірених чи вичитаних 0, вже обрано 1.');
        await expect(dialog.locator('.bulk-select-warning')).toContainText('З 1 перевіреного абзацу буде знято «Перевірено»');
        let asked = '';
        page.once('dialog', (d) => { asked = d.message(); void d.accept(); });
        await dialog.getByRole('button', { name: 'Обрати для файлу', exact: true }).click();
        await expect(dialog).toBeHidden();
        expect(asked).toContain('буде знято «Перевірено»');
        expect(await fileState(request, project.projectId)).toEqual([['GPT переклад', false], ['GPT переклад', false]]);
        await page.locator('#undo-translation').click();
        await expect.poll(() => fileState(request, project.projectId)).toEqual([['GPT переклад', false], ['Claude переклад', true]]); // «Перевірено» is back
        await expect(rows.nth(1).getByLabel('Перевірено', { exact: true })).toBeChecked(); // the checkbox in the paragraph itself
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
        for (const connection of connections) await request.delete(`/api/connections/${connection.connectionId}`);
    }
});

test('unsaved edits: the action offers to save first, declining cancels it', async ({ page, request }) => {
    test.setTimeout(90_000);
    const title = `Bulk unsaved ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    const connections = [await createConnection(request, 'claude'), await createConnection(request, 'openai')];
    try {
        await openFirstChapter(page, title);
        await translateChapter(page, 'Claude');
        await translateChapter(page, 'GPT');
        const row = page.locator('.translation-row').first();
        await row.getByRole('tab', { name: 'Вручну' }).click();
        const editor = row.locator('.translation-paragraph');
        await editor.click();
        await editor.pressSequentially(' ✎');
        await expect(page.locator('#save-translation')).toBeEnabled();

        // declining: no dialog, nothing saved
        page.once('dialog', (d) => { expect(d.message()).toContain('незбережені зміни'); void d.dismiss(); });
        await openChapterMore(page, 'Обрати для файлу весь розділ з…');
        await expect(page.locator('#bulk-select-dialog')).toBeHidden();
        await expect(page.locator('#save-translation')).toBeEnabled();
        expect((await fileState(request, project.projectId))[0][0]).toBe('Claude переклад');

        // accepting: the chapter is saved (the edit becomes «Вручну»), then the dialog opens
        page.once('dialog', (d) => { void d.accept(); });
        await openChapterMore(page, 'Обрати для файлу весь розділ з…');
        await expect(page.locator('#bulk-select-dialog')).toBeVisible();
        await expect.poll(async () => (await fileState(request, project.projectId))[0][0]).toBe('Claude переклад ✎');
        await page.locator('#bulk-select-dialog').getByLabel(/GPT/).check();
        await page.locator('#bulk-select-dialog').getByRole('button', { name: 'Обрати для файлу', exact: true }).click();
        await expect.poll(async () => (await fileState(request, project.projectId)).map((item: any) => item[0])).toEqual(['GPT переклад', 'GPT переклад']);

        // Undo of the whole action brings back the «Вручну» text that was in the file before it
        const undo = page.locator('#undo-translation');
        await expect(undo).toBeEnabled();
        await undo.click();
        await expect.poll(async () => (await fileState(request, project.projectId)).map((item: any) => item[0])).toEqual(['Claude переклад ✎', 'Claude переклад']);
        await expect(row.locator('.variant-tab[data-in-file="true"]')).toHaveText('✓ Вручну');
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
        for (const connection of connections) await request.delete(`/api/connections/${connection.connectionId}`);
    }
});

test('«Показувати весь розділ у варіанті X» only changes what is shown', async ({ page, request }) => {
    test.setTimeout(90_000);
    const title = `Bulk view ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    const connections = [await createConnection(request, 'claude'), await createConnection(request, 'openai')];
    try {
        await openFirstChapter(page, title);
        await translateChapter(page, 'Claude');
        const [, second] = await paragraphs(request, project.projectId);
        expect((await request.put(`/api/paragraphs/${second.paragraphId}`, { data: { translationText: second.translationText, reviewed: true } })).ok()).toBeTruthy();
        await page.reload();
        await openFirstChapter(page, title);
        await translateChapter(page, 'GPT'); // the proofread paragraph is skipped: it has no GPT variant
        const rows = page.locator('.translation-row');
        const view = page.locator('#chapter-view-select');
        await expect(view.locator('option')).toHaveText(['Як обрано для файлу', 'Claude — найновіша версія Claude', 'GPT — найновіша версія GPT']);
        const before = await fileState(request, project.projectId);

        await view.selectOption('openai');
        await expect(page.locator('#chapter-view-hint')).toContainText('найновішу версію GPT');
        await expect(activeTab(rows.nth(0))).toHaveText('GPT');
        await expect(rows.nth(0).locator('.variant-preview')).toHaveText('GPT переклад');
        await expect(rows.nth(0).locator('.variant-differs')).toHaveText('≠ у файлі інша версія');
        await expect(rows.nth(0)).toHaveClass(/translation-row--shows-other/);
        // no GPT variant here: the chosen text is shown, nothing is marked
        await expect(activeTab(rows.nth(1))).toHaveText('Вручну');
        await expect(rows.nth(1).locator('.translation-paragraph')).toHaveText('Claude переклад');
        await expect(rows.nth(1).locator('.variant-differs')).toHaveCount(0);
        // nothing was changed for the file and the chapter is not dirty
        expect(await fileState(request, project.projectId)).toEqual(before);
        await expect(page.locator('#save-translation')).toBeDisabled();

        // Claude is the file's engine: the shown newest version is the one in the file, so no mark
        await view.selectOption('claude');
        await expect(activeTab(rows.nth(0))).toHaveText('✓ Claude');
        await expect(rows.nth(0).locator('.variant-differs')).toHaveCount(0);

        // the mode survives leaving and re-opening the chapter in this session, and goes with «Як обрано»
        await view.selectOption('openai');
        await page.locator('.chapter-button').first().click();
        await expect(view).toHaveValue('openai');
        await expect(activeTab(rows.nth(0))).toHaveText('GPT');
        await view.selectOption('');
        await expect(rows.nth(0).locator('.variant-differs')).toHaveCount(0);
        await expect(activeTab(rows.nth(0))).toHaveText('Вручну');

        // a reload shows the default tabs again
        await view.selectOption('openai');
        await page.reload();
        await openFirstChapter(page, title);
        await expect(page.locator('#chapter-view-select')).toHaveValue('');
        await expect(activeTab(page.locator('.translation-row').first())).toHaveText('Вручну');
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
        for (const connection of connections) await request.delete(`/api/connections/${connection.connectionId}`);
    }
});
