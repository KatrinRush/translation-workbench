import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Runs against the real backend; e2e/server.py answers Claude/OpenAI/Gemini locally
// (translations, connection checks, model lists), so no real API is called.
// Needs WORKBENCH_CREDENTIALS_KEY, like every e2e test that stores a connection.

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
        data: { providerId, displayName: `${providerId} variants e2e`, credentials: { apiKey: `${providerId}-e2e-key` } },
    });
    expect(response.ok(), await response.text()).toBeTruthy();
    const connection = await response.json();
    expect((await request.post(`/api/connections/${connection.connectionId}/test`)).ok()).toBeTruthy();
    return connection;
}

async function firstParagraph(request: APIRequestContext, projectId: string) {
    const structure = await (await request.get(`/api/projects/${projectId}/book/structure`)).json();
    return structure.chapters[0].elements.find((element: any) => element.type === 'paragraph');
}

async function openFirstChapter(page: Page, title: string) {
    await page.goto('/');
    await page.locator('.project-card').filter({ hasText: title }).getByRole('button', { name: 'Відкрити проєкт' }).click();
    await page.getByRole('button', { name: 'Переклад', exact: true }).click();
    await page.getByRole('button', { name: 'Переглянути структуру книги' }).click();
    await page.locator('.chapter-button').first().click();
}

async function translateChapter(page: Page) {
    const button = page.locator('#translate-chapter-button');
    await button.click();
    await expect(button).toHaveText('Перекласти розділ');
    await expect(button).toBeEnabled();
}

test.describe('Translation variants', () => {
    test('engines write separate variants, «У файл» picks one, undo restores it, manual edits become «Вручну»', async ({ page, request }) => {
        const title = `Variants ${Date.now()}`;
        const project = await createProjectWithBook(request, title);
        const connections = [await createConnection(request, 'claude'), await createConnection(request, 'openai')];

        try {
            await openFirstChapter(page, title);
            const toggle = page.locator('#translation-provider-toggle');
            await expect(toggle.getByLabel('GPT')).toBeVisible();
            await expect(toggle.getByLabel('Gemini')).toBeVisible();

            await toggle.getByText('Claude').click();
            await expect(toggle.getByLabel('Claude')).toBeChecked();
            await expect(page.locator('#translation-engine-model')).toContainText('(за замовчуванням)');
            await translateChapter(page);

            const row = page.locator('.translation-row').first();
            const editor = row.locator('.translation-paragraph');
            await expect(editor).toHaveText('Claude переклад');
            await expect(row.locator('.variant-tab')).toHaveText(['✓ Claude', 'Вручну']);

            // A second engine adds its own variant and leaves the chosen text alone.
            await toggle.getByText('GPT').click();
            await expect(toggle.getByLabel('GPT')).toBeChecked();
            await expect(row.locator('.translate-paragraph-button')).toHaveText('Перекласти GPT');
            await translateChapter(page);
            await expect(editor).toHaveText('Claude переклад');
            await expect(row.locator('.variant-tab')).toHaveText(['✓ Claude', 'GPT', 'Вручну']);

            await row.getByRole('tab', { name: 'GPT' }).click();
            await expect(row.locator('.variant-preview')).toHaveText('GPT переклад');
            await expect(row.locator('.variant-meta')).toContainText('gpt-4.1-nano');
            await row.getByRole('button', { name: 'У файл' }).click();
            await expect(row.getByRole('tab', { name: '✓ GPT' })).toBeVisible();
            await expect.poll(async () => (await firstParagraph(request, project.projectId)).translationText).toBe('GPT переклад');

            // Undo of «У файл» puts the previous choice back on the server, without a manual variant.
            await page.locator('#undo-translation').click();
            await expect(row.getByRole('tab', { name: '✓ Claude' })).toBeVisible();
            await expect(editor).toHaveText('Claude переклад');
            await expect.poll(async () => {
                const paragraph = await firstParagraph(request, project.projectId);
                return [paragraph.translationText, paragraph.translationVariants.some((variant: any) => variant.engine === 'manual')];
            }).toEqual(['Claude переклад', false]);

            // Opening «Вручну» creates nothing; a real edit + save does.
            await row.getByRole('tab', { name: 'Вручну' }).click();
            await expect(editor).toBeVisible();
            await editor.click();
            await editor.press('End');
            await editor.pressSequentially(' — виправлено');
            await page.locator('#save-translation').click();
            await expect.poll(async () => {
                const paragraph = await firstParagraph(request, project.projectId);
                const manual = paragraph.translationVariants.find((variant: any) => variant.engine === 'manual');
                return [paragraph.translationText, manual?.variantId === paragraph.selectedVariantId];
            }).toEqual(['Claude переклад — виправлено', true]);
            await expect(row.getByRole('tab', { name: '✓ Вручну' })).toBeVisible();

            // Choosing another variant for a proofread paragraph asks once and clears «Перевірено».
            await row.getByRole('checkbox', { name: 'Перевірено' }).check();
            await page.locator('#save-translation').click();
            await expect.poll(async () => (await firstParagraph(request, project.projectId)).reviewed).toBe(true);
            await row.getByRole('tab', { name: 'GPT' }).click();
            page.once('dialog', (dialog) => {
                expect(dialog.message()).toContain('перевірений');
                void dialog.accept();
            });
            await row.getByRole('button', { name: 'У файл' }).click();
            await expect(row.getByRole('tab', { name: '✓ GPT' })).toBeVisible();
            await expect(row.getByRole('checkbox', { name: 'Перевірено' })).not.toBeChecked();

            // GPT is in the file, an older manual edit exists: «Вручну» shows that edit
            // but opening the tab neither saves anything nor marks the chapter dirty.
            await row.getByRole('tab', { name: 'Вручну' }).click();
            await expect(editor).toHaveText('Claude переклад — виправлено');
            await expect(page.locator('#save-translation')).toBeDisabled();
            await row.getByRole('tab', { name: '✓ GPT' }).click();
            await expect.poll(async () => (await firstParagraph(request, project.projectId)).translationText).toBe('GPT переклад');
        } finally {
            await request.delete(`/api/projects/${project.projectId}`);
            for (const connection of connections) {
                await request.delete(`/api/connections/${connection.connectionId}`);
            }
        }
    });

    test('translation settings list models through the stored connection and save the choice', async ({ page, request }) => {
        const title = `Variants settings ${Date.now()}`;
        const project = await createProjectWithBook(request, title);
        const connection = await createConnection(request, 'claude');
        await page.setViewportSize({ width: 820, height: 1180 }); // tablet portrait

        try {
            await openFirstChapter(page, title);
            await page.locator('#translation-settings-button').click();
            const dialog = page.locator('#translation-settings-dialog');
            await expect(dialog).toBeVisible();
            await expect(dialog.locator('[data-engine="deepl"]')).toContainText('quality_optimized (фіксована)');

            const claude = dialog.locator('[data-engine="claude"]');
            await expect(claude.locator('.translation-engine-status')).toContainText('Підключено');
            await expect(claude.locator('.translation-model-list-status')).toContainText('Моделей у списку: 2');
            await claude.locator('.translation-model-search').fill('beta');
            await expect(claude.locator('.translation-model-select option')).toHaveCount(2);
            await claude.locator('.translation-model-select').selectOption('claude-e2e-beta');

            const gemini = dialog.locator('[data-engine="gemini"]');
            await expect(gemini.locator('.translation-engine-status')).toContainText('Немає підключення');
            await expect(gemini.getByRole('button', { name: 'Відкрити Connections' })).toBeVisible();
            await gemini.locator('.translation-model-manual').fill('gemini-handpicked');

            for (const control of await dialog.locator('select, input, button.text-btn').all()) {
                const box = await control.boundingBox();
                expect(box?.height ?? 0).toBeGreaterThanOrEqual(44);
            }

            await dialog.getByRole('button', { name: 'Зберегти' }).click();
            await expect(dialog).toBeHidden();
            await expect.poll(async () => {
                const saved = await (await request.get(`/api/projects/${project.projectId}`)).json();
                return saved.aiConfiguration.translationModels;
            }).toEqual({ claude: 'claude-e2e-beta', openai: null, gemini: 'gemini-handpicked' });

            await page.locator('#translation-provider-toggle').getByText('Claude').click();
            await expect(page.locator('#translation-engine-model')).toHaveText('Модель: claude-e2e-beta');
        } finally {
            await request.delete(`/api/projects/${project.projectId}`);
            await request.delete(`/api/connections/${connection.connectionId}`);
        }
    });

    test('a glossary term the engine did not use shows a warning next to the paragraph', async ({ page, request }) => {
        const title = `Variants glossary ${Date.now()}`;
        const project = await createProjectWithBook(request, title);
        // The first paragraph reads "This is a test EPUB file…"; the e2e engine never writes «тест».
        const entry = await (await request.post('/api/glossary', { data: { source: 'test EPUB', target: 'тестовий EPUB' } })).json();
        await request.put(`/api/projects/${project.projectId}`, { data: { projectGlossaryEntryIds: [entry.glossaryEntryId] } });
        const connection = await createConnection(request, 'claude');

        try {
            await openFirstChapter(page, title);
            await page.locator('#translation-provider-toggle').getByText('Claude').click();
            await expect(page.locator('#translation-provider-toggle').getByLabel('Claude')).toBeChecked();
            await translateChapter(page);

            const row = page.locator('.translation-row').first();
            await expect(row.locator('.variant-warning')).toContainText('test EPUB → тестовий EPUB');
            await expect(page.locator('.translation-row').nth(1).locator('.variant-warning')).toHaveCount(0);
            const paragraph = await firstParagraph(request, project.projectId);
            expect(paragraph.translationVariants[0].warnings).toEqual([
                { type: 'glossary_missing', source: 'test EPUB', target: 'тестовий EPUB' },
            ]);
        } finally {
            await request.delete(`/api/projects/${project.projectId}`);
            await request.delete(`/api/connections/${connection.connectionId}`);
            await request.delete(`/api/glossary/${entry.glossaryEntryId}`);
        }
    });
});
