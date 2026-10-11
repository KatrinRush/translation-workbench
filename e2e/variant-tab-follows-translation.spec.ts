import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// After an engine run the tab of every translated paragraph switches to that engine's newest
// variant. Only the tab on screen changes: the chosen variant and translation_text stay.
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
        data: { providerId, displayName: `${providerId} tab e2e`, credentials: { apiKey: `${providerId}-e2e-key` } },
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

const activeTab = (row: ReturnType<Page['locator']>) => row.locator('.variant-tab[aria-selected="true"]');

test('the tab of each translated paragraph follows the engine that has just translated', async ({ page, request }) => {
    test.setTimeout(90_000);
    const title = `Variant tab follows ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    const connections = [await createConnection(request, 'claude'), await createConnection(request, 'openai'), await createConnection(request, 'gemini')];
    const structure = async () => (await (await request.get(`/api/projects/${project.projectId}/book/structure`)).json())
        .chapters[0].elements.filter((element: any) => element.type === 'paragraph');

    try {
        await openFirstChapter(page, title);
        const rows = page.locator('.translation-row');
        const firstRow = rows.nth(0);
        const secondRow = rows.nth(1);

        // Chapter translation: every translated paragraph shows the new variant.
        await selectEngine(page, 'Claude');
        await translateChapter(page);
        await expect(activeTab(firstRow)).toHaveText('✓ Claude');
        await expect(activeTab(secondRow)).toHaveText('✓ Claude');

        // A second engine: the tab moves to GPT although Claude stays the variant in the file.
        await selectEngine(page, 'GPT');
        await translateChapter(page);
        await expect(activeTab(firstRow)).toHaveText('GPT');
        await expect(activeTab(secondRow)).toHaveText('GPT');
        await expect(firstRow.locator('.variant-preview')).toHaveText('GPT переклад');
        await expect(firstRow.locator('.variant-tab[data-in-file="true"]')).toHaveText('✓ Claude');
        const afterGpt = await structure();
        expect(afterGpt.map((paragraph: any) => paragraph.translationText)).toEqual(['Claude переклад', 'Claude переклад']);
        expect(afterGpt.map((paragraph: any) => paragraph.translationVariants.find((variant: any) => variant.variantId === paragraph.selectedVariantId).engine)).toEqual(['claude', 'claude']);

        // The user picks another tab by hand; a later chapter batch/re-render must not undo that choice
        // for a paragraph the run did not touch, and a paragraph button moves only its own paragraph.
        await firstRow.getByRole('tab', { name: '✓ Claude' }).click();
        await expect(activeTab(firstRow)).toHaveText('✓ Claude');
        await selectEngine(page, 'Gemini');
        await activeTab(secondRow).click(); // the paragraph's own actions show for the current paragraph
        await expect(secondRow.locator('.translate-paragraph-button')).toHaveText('Перекласти Gemini');
        await secondRow.locator('.translate-paragraph-button').click();
        await expect(activeTab(secondRow)).toHaveText('Gemini');
        await expect(activeTab(firstRow)).toHaveText('✓ Claude');
        await expect(secondRow.locator('.variant-preview')).toHaveText('Gemini переклад');
        const afterGemini = await structure();
        expect(afterGemini.map((paragraph: any) => paragraph.translationText)).toEqual(['Claude переклад', 'Claude переклад']);

        // Interface state only: a reloaded page opens the default tabs again.
        await page.reload();
        await page.locator('.project-card').filter({ hasText: title }).getByRole('button', { name: 'Відкрити проєкт' }).click();
        await page.getByRole('button', { name: 'Переклад', exact: true }).click();
        await expect(page.locator('.translation-row').nth(1).locator('.variant-tab')).toHaveCount(4);
        await expect(activeTab(page.locator('.translation-row').nth(1))).toHaveText('Вручну');
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
        for (const connection of connections) {
            await request.delete(`/api/connections/${connection.connectionId}`);
        }
    }
});
