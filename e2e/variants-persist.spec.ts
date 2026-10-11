import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Variant tabs must survive saving (project + chapter 💾) and a page reload.
// Runs against e2e/server.py (fake LLM transports). Needs WORKBENCH_CREDENTIALS_KEY.

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
        data: { providerId, displayName: `${providerId} persist e2e`, credentials: { apiKey: `${providerId}-e2e-key` } },
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
    await page.getByRole('button', { name: 'Переглянути структуру книги' }).click();
    await page.locator('.chapter-button').first().click();
}

async function translateChapter(page: Page) {
    const button = page.locator('#translate-chapter-button');
    await button.click();
    await expect(button).toHaveText('Перекласти розділ');
    await expect(button).toBeEnabled();
}

test.setTimeout(90_000);
test('variant tabs stay after saving the project and the chapter and reloading the page', async ({ page, request }) => {
    const title = `Variants persist ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    const connections = [await createConnection(request, 'claude'), await createConnection(request, 'openai'), await createConnection(request, 'gemini')];

    try {
        await openFirstChapter(page, title);
        const toggle = page.locator('#translation-provider-toggle');
        for (const [label] of [['Claude'], ['GPT'], ['Gemini']]) {
            await toggle.getByText(label).click();
            await expect(toggle.getByLabel(label)).toBeChecked();
            await translateChapter(page);
        }
        const row = page.locator('.translation-row').first();
        const tabs = ['✓ Claude', 'GPT', 'Gemini', 'Вручну'];
        await expect(row.locator('.variant-tab')).toHaveText(tabs);

        // Chapter save: a manual edit + 💾 (a real PUT of the dirty paragraph) ...
        const editor = row.locator('.translation-paragraph');
        await row.getByRole('tab', { name: 'Вручну' }).click();
        await editor.click();
        await editor.pressSequentially('Моя правка');
        await page.locator('#save-translation').click();
        await expect(page.locator('#save-translation')).toBeDisabled();
        const savedTabs = ['Claude', 'GPT', 'Gemini', '✓ Вручну'];
        await expect(row.locator('.variant-tab')).toHaveText(savedTabs);
        // ... and project save: the same PUT the project settings screens send.
        const current = await (await request.get(`/api/projects/${project.projectId}`)).json();
        expect((await request.put(`/api/projects/${project.projectId}`, { data: current })).ok()).toBeTruthy();
        expect((await request.put(`/api/projects/${project.projectId}`, { data: { title, bookNumber: 3 } })).ok()).toBeTruthy();

        await expect(row.locator('.variant-tab')).toHaveText(savedTabs);

        // Reload the page and open the chapter again: the tabs come from the server.
        await page.reload();
        await page.locator('.project-card').filter({ hasText: title }).getByRole('button', { name: 'Відкрити проєкт' }).click();
        await page.getByRole('button', { name: 'Переклад', exact: true }).click();
        await expect(page.locator('.translation-row').first()).toBeVisible();
        const reloadedRow = page.locator('.translation-row').first();
        await expect(reloadedRow.locator('.variant-tab')).toHaveText(savedTabs);
        await expect(reloadedRow.locator('.translation-paragraph')).toHaveText('Claude перекладМоя правка');

        const structure = await (await request.get(`/api/projects/${project.projectId}/book/structure`)).json();
        const paragraph = structure.chapters[0].elements.find((element: any) => element.type === 'paragraph');
        expect(paragraph.translationVariants.map((variant: any) => variant.engine).sort()).toEqual(['claude', 'gemini', 'manual', 'openai']);
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
        for (const connection of connections) {
            await request.delete(`/api/connections/${connection.connectionId}`);
        }
    }
});
