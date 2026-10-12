import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Every engine run adds a version of that engine's variant (nothing is overwritten); the tab
// shows one version with a ‹ 3/5 › switcher, «У файл» acts on the version on screen.
// e2e/server.py answers "Claude переклад" always, "Claude v2 переклад" when the project's
// translation rules contain [[v2]], and so on. Needs WORKBENCH_CREDENTIALS_KEY.

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
        data: { providerId, displayName: `${providerId} versions e2e`, credentials: { apiKey: `${providerId}-e2e-key` } },
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

test('repeated translations by one engine become versions with a ‹ n/m › switcher', async ({ page, request }) => {
    test.setTimeout(90_000);
    const title = `Variant versions ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    const connection = await createConnection(request, 'claude');
    const paragraph = async () => (await (await request.get(`/api/projects/${project.projectId}/book/structure`)).json())
        .chapters[0].elements.find((element: any) => element.type === 'paragraph');

    try {
        await openFirstChapter(page, title);
        await page.locator('#translation-provider-toggle').getByText('Claude', { exact: true }).click();
        await expect(page.locator('#translation-provider-toggle').getByLabel('Claude')).toBeChecked();
        const row = page.locator('.translation-row').first();
        const tab = row.locator('.variant-tab[aria-selected="true"]');
        const counter = row.locator('.variant-version-counter');

        await translateChapter(page);
        await expect(row.locator('.variant-versions')).toHaveCount(0); // a single version: no switcher
        await expect(tab).toHaveText('✓ Claude');

        // Same answer again: no duplicate version.
        await translateChapter(page);
        expect((await paragraph()).translationVariants.filter((variant: any) => variant.engine === 'claude')).toHaveLength(1);

        // Two different answers: three versions, the tab follows the newest, the file keeps version 1.
        for (const marker of ['[[v2]]', '[[v3]]']) {
            expect((await request.put(`/api/projects/${project.projectId}/translation-rules`, { data: { translationRules: marker } })).ok()).toBeTruthy();
            await translateChapter(page);
        }
        await expect(counter).toHaveText('3/3');
        await expect(row.locator('.variant-preview')).toHaveText('Claude v3 переклад');
        await expect(tab).toHaveText('✓ Claude'); // ✓: one version of Claude is in the file
        await expect(row.locator('.variant-to-file')).toHaveText('≠ У файл'); // ... but not this one
        expect((await paragraph()).translationText).toBe('Claude переклад');

        // Step back: 2/3, then 1/3 which is the version in the file (✓).
        await row.getByRole('button', { name: 'Попередня версія' }).click();
        await expect(counter).toHaveText('2/3');
        await expect(row.locator('.variant-preview')).toHaveText('Claude v2 переклад');
        await row.getByRole('button', { name: 'Попередня версія' }).click();
        await expect(counter).toHaveText('1/3 ✓');
        await expect(row.locator('.variant-preview')).toHaveText('Claude переклад');
        await expect(row.locator('.variant-to-file')).toHaveText('✓ у файлі');
        await expect(row.getByRole('button', { name: 'Попередня версія' })).toBeDisabled();

        // «У файл» acts on the version on screen (2/3), nothing is overwritten.
        await row.getByRole('button', { name: 'Наступна версія' }).click();
        await expect(counter).toHaveText('2/3');
        await row.locator('.variant-to-file').click();
        await expect(counter).toHaveText('2/3 ✓');
        await expect.poll(async () => (await paragraph()).translationText).toBe('Claude v2 переклад');
        expect((await paragraph()).translationVariants.filter((variant: any) => variant.engine === 'claude').map((variant: any) => variant.text))
            .toEqual(['Claude переклад', 'Claude v2 переклад', 'Claude v3 переклад']);

        // Undo of «У файл» restores the previous choice.
        await page.locator('#undo-translation').click();
        await expect.poll(async () => (await paragraph()).translationText).toBe('Claude переклад');

        // A reload keeps every version; the Claude tab opens on the version in the file.
        await page.reload();
        await page.locator('.project-card').filter({ hasText: title }).getByRole('button', { name: 'Відкрити проєкт' }).click();
        await page.getByRole('button', { name: 'Переклад', exact: true }).click();
        const reloaded = page.locator('.translation-row').first();
        await reloaded.getByRole('tab', { name: '✓ Claude' }).click();
        await expect(reloaded.locator('.variant-version-counter')).toHaveText('1/3 ✓');
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
        await request.delete(`/api/connections/${connection.connectionId}`);
    }
});
