import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// ⚙ → «Інструкції рушіїв»: own translation instructions for Claude / GPT / Gemini, global and per project,
// the read-only final prompt and the short hash shown with a translated version. e2e/server.py answers the
// engines locally. Needs WORKBENCH_CREDENTIALS_KEY (a connection is stored). The global texts are shared by
// every project, so each test clears the ones it set.

async function createProjectWithBook(request: APIRequestContext, title: string) {
    const created = await request.post('/api/projects', { data: { title, status: 'translation' } });
    expect(created.ok()).toBeTruthy();
    const project = await created.json();
    const upload = await request.post('/upload', {
        headers: { 'X-Project-Id': project.projectId },
        multipart: { file: { name: 'sample-without-cover.epub', mimeType: 'application/epub+zip', buffer: fs.readFileSync(path.join(__dirname, '..', 'test-data', 'sample-without-cover.epub')) } },
    });
    expect(upload.ok()).toBeTruthy();
    return project;
}

async function createConnection(request: APIRequestContext, providerId: string) {
    const response = await request.post('/api/connections', {
        data: { providerId, displayName: `${providerId} instructions e2e`, credentials: { apiKey: `${providerId}-e2e-key` } },
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

async function openSettings(page: Page) {
    await page.locator('#translation-settings-button').click();
    await expect(page.locator('#translation-settings-dialog')).toBeVisible();
    await expect(page.locator('#engine-instructions-text')).toBeEnabled();
}

async function clearGlobal(request: APIRequestContext) {
    for (const engine of ['claude', 'openai', 'gemini']) {
        await request.put(`/api/engine-instructions/${engine}`, { data: { text: '' } });
    }
}

test('write, save and reopen: tabs and the scope switch keep separate texts; counter and limit', async ({ page, request }) => {
    test.setTimeout(90_000);
    const title = `Instructions ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    try {
        await page.setViewportSize({ width: 1440, height: 900 });
        await openFirstChapter(page, title);
        await openSettings(page);
        const text = page.locator('#engine-instructions-text');
        const counter = page.locator('#engine-instructions-counter');
        const status = page.locator('#engine-instructions-status');
        const save = page.locator('#save-engine-instructions');

        await expect(page.locator('#engine-instructions-settings')).toContainText('надсилається провайдеру');
        await expect(page.locator('#engine-instructions-tabs button')).toHaveText(['Claude', 'GPT', 'Gemini']);
        await expect(counter).toContainText('0 / 4000');
        await expect(save).toBeDisabled();

        // global text for Claude: the counter shows characters and approximate tokens
        await text.fill('Глобально: пиши стисло.');
        await expect(counter).toContainText('23 / 4000');
        await expect(counter).toContainText('≈ 8 токенів');
        await expect(status).toContainText('незбережені');
        await expect(save).toBeEnabled();

        // the project's addition is a different text; GPT has none yet
        await page.locator('#engine-instructions-scope').getByText('Лише для цього проєкту').click();
        await expect(text).toHaveValue('');
        await text.fill('Проєкт: герої на «ти».');
        await page.locator('#engine-instructions-tabs').getByText('GPT').click();
        await expect(text).toHaveValue('');
        await page.locator('#engine-instructions-tabs').getByText('Claude').click();
        await expect(text).toHaveValue('Проєкт: герої на «ти».');
        await page.locator('#engine-instructions-scope').getByText('Для всіх проєктів').click();
        await expect(text).toHaveValue('Глобально: пиши стисло.');

        // one button saves every changed text
        await save.click();
        await expect(status).toContainText('Збережено');
        await expect(save).toBeDisabled();
        expect((await (await request.get('/api/engine-instructions/claude')).json()).text).toBe('Глобально: пиши стисло.');
        expect((await (await request.get(`/api/projects/${project.projectId}/engine-instructions/claude`)).json()).text).toBe('Проєкт: герої на «ти».');
        expect((await (await request.get('/api/engine-instructions/openai')).json()).text).toBe('');

        // reopen after a reload: still there
        await page.reload();
        await openFirstChapter(page, title);
        await openSettings(page);
        await expect(text).toHaveValue('Глобально: пиши стисло.');
        await page.locator('#engine-instructions-scope').getByText('Лише для цього проєкту').click();
        await expect(text).toHaveValue('Проєкт: герої на «ти».');

        // the limit: over 4000 characters cannot be saved
        await text.fill('x'.repeat(4001));
        await expect(counter).toContainText('4001 / 4000');
        await expect(counter).toHaveClass(/over-limit/);
        await expect(save).toBeDisabled();
        const refused = await request.put(`/api/projects/${project.projectId}/engine-instructions/claude`, { data: { text: 'x'.repeat(4001) } });
        expect(refused.status()).toBe(400);
    } finally {
        await clearGlobal(request);
        await request.delete(`/api/projects/${project.projectId}`);
    }
});

test('«Показати фінальний промпт»: all layers in order, no book text, a token summary, Esc closes the prompt first', async ({ page, request }) => {
    test.setTimeout(90_000);
    const title = `Instructions prompt ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    try {
        await page.setViewportSize({ width: 1440, height: 900 });
        await openFirstChapter(page, title);
        await openSettings(page);
        const text = page.locator('#engine-instructions-text');
        await text.fill('Глобально: пиши стисло.');
        await page.locator('#engine-instructions-scope').getByText('Лише для цього проєкту').click();
        await text.fill('Проєкт: герої на «ти».');

        // the prompt shows the saved state: unsaved changes are refused
        await page.locator('#show-engine-prompt').click();
        await expect(page.locator('#engine-instructions-status')).toContainText('Спершу збережіть');
        await expect(page.locator('#engine-prompt-dialog')).toBeHidden();

        await page.locator('#save-engine-instructions').click();
        await expect(page.locator('#engine-instructions-status')).toContainText('Збережено');
        await page.locator('#show-engine-prompt').click();
        const dialog = page.locator('#engine-prompt-dialog');
        await expect(dialog).toBeVisible();
        const prompt = await page.locator('#engine-prompt-text').inputValue();
        expect(await page.locator('#engine-prompt-text').getAttribute('readonly')).not.toBeNull();
        const order = ['ФОРМАТ (суворо)', 'ПЕРСОНАЖІ', 'ГЛОСАРІЙ ПРОЄКТУ', 'ПРАВИЛА ПЕРЕКЛАДУ ПРОЄКТУ', 'ДОДАТКОВО ДЛЯ ЦЬОГО РУШІЯ',
            'Глобально: пиши стисло.', 'Проєкт: герої на «ти».', "ОБОВ'ЯЗКОВИЙ ФОРМАТ ВІДПОВІДІ"].map((part) => prompt.indexOf(part));
        expect(order.every((index) => index >= 0), String(order)).toBe(true);
        expect([...order].sort((a, b) => a - b)).toEqual(order);
        expect(prompt).not.toContain('This is a test EPUB file');
        await expect(page.locator('#engine-prompt-summary')).toContainText(/≈ \d+ токенів/);
        await expect(page.locator('#engine-prompt-summary')).toContainText(/інструкції #[0-9a-f]{8}/);
        await expect(page.locator('#engine-prompt-engine')).toContainText('Claude');

        // GPT without instructions: the shared prompt only, a dash instead of a hash
        await page.keyboard.press('Escape');
        await expect(dialog).toBeHidden();
        await expect(page.locator('#translation-settings-dialog')).toBeVisible();
        await page.locator('#engine-instructions-tabs').getByText('GPT').click();
        await page.locator('#show-engine-prompt').click();
        await expect(dialog).toBeVisible();
        expect(await page.locator('#engine-prompt-text').inputValue()).not.toContain('ДОДАТКОВО ДЛЯ ЦЬОГО РУШІЯ');
        await expect(page.locator('#engine-prompt-summary')).toContainText('інструкції —');
        await page.locator('#close-engine-prompt').click();
        await expect(dialog).toBeHidden();
    } finally {
        await clearGlobal(request);
        await request.delete(`/api/projects/${project.projectId}`);
    }
});

test('a translated version records the instructions hash and shows it in the version tooltip', async ({ page, request }) => {
    test.setTimeout(90_000);
    const title = `Instructions hash ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    await createConnection(request, 'claude');
    try {
        await request.put('/api/engine-instructions/claude', { data: { text: 'Глобально: пиши стисло.' } });
        await openFirstChapter(page, title);
        const toggle = page.locator('#translation-provider-toggle');
        await toggle.getByText('Claude').click();
        await expect(toggle.getByLabel('Claude')).toBeChecked();
        const button = page.locator('#translate-chapter-button');
        await button.click();
        await expect(button).toHaveText('Перекласти розділ');
        await expect(button).toBeEnabled();

        const row = page.locator('.translation-row').first();
        await expect(row.locator('.translation-paragraph')).toHaveText('Claude переклад');
        await expect(row.locator('.variant-meta')).toContainText(/інструкції #[0-9a-f]{8}/);
        const structure = await (await request.get(`/api/projects/${project.projectId}/book/structure`)).json();
        const paragraph = structure.chapters[0].elements.find((element: any) => element.type === 'paragraph');
        const variant = paragraph.translationVariants.find((item: any) => item.engine === 'claude');
        expect(variant.promptHash).toMatch(/^[0-9a-f]{8}$/);
    } finally {
        await clearGlobal(request);
        await request.delete(`/api/projects/${project.projectId}`);
    }
});
