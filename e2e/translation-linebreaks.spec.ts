import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// A dialogue is one English paragraph but several Ukrainian ones: Enter in the translation only starts a new line,
// the line break is saved, survives a reload and stays in place; nothing is saved or moved by Enter itself.

async function createProject(request: APIRequestContext, title: string) {
    const project = await (await request.post('/api/projects', { data: { title, status: 'translation' } })).json();
    const upload = await request.post('/upload', {
        headers: { 'X-Project-Id': project.projectId },
        multipart: { file: { name: 'long-chapter.epub', mimeType: 'application/epub+zip', buffer: fs.readFileSync(path.join(__dirname, '..', 'test-data', 'long-chapter.epub')) } },
    });
    expect(upload.ok()).toBeTruthy();
    return project;
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

async function firstTexts(request: APIRequestContext, projectId: string) {
    const structure = await (await request.get(`/api/projects/${projectId}/book/structure`)).json();
    return structure.chapters[0].elements.filter((e: any) => e.paragraphId).slice(0, 2).map((e: any) => e.translationText as string | null);
}

for (const [name, width, height] of [['desktop', 1280, 900], ['phone', 390, 844]] as const) {
    test(`Enter in the translation inserts a line break (${name}); it is saved and survives a reload`, async ({ page, request }) => {
        test.setTimeout(120_000);
        await page.setViewportSize({ width, height });
        const title = `Linebreaks ${name} ${Date.now()}`;
        const project = await createProject(request, title);
        try {
            await openFirstChapter(page, title);
            const rows = page.locator('.translation-row');
            const editor = rows.nth(0).locator('.translation-paragraph');
            await editor.click();
            await editor.pressSequentially('— Привіт, — сказав він.');
            await page.keyboard.press('Enter');
            await editor.pressSequentially('— Привіт, — відповіла вона.');
            await page.keyboard.press('Enter');
            await page.keyboard.press('Enter');
            await editor.pressSequentially('— Втретє.');

            // Enter saved nothing and moved nowhere: still the first row's field, still focused, the chapter is unsaved
            await expect(editor).toBeFocused();
            await expect(page.locator('#save-translation')).toBeEnabled();
            expect(await firstTexts(request, project.projectId)).toEqual([null, null]);
            // the lines are on separate lines in the field
            const lines = await editor.evaluate((el) => (el as HTMLElement).innerText.split('\n').filter((line) => line.length));
            expect(lines).toEqual(['— Привіт, — сказав він.', '— Привіт, — відповіла вона.', '— Втретє.']);

            await page.locator('#save-translation').click();
            await expect.poll(async () => (await firstTexts(request, project.projectId))[0])
                .toBe('— Привіт, — сказав він.\n— Привіт, — відповіла вона.\n— Втретє.');

            await page.reload();
            await openFirstChapter(page, title);
            const reloaded = page.locator('.translation-row').nth(0).locator('.translation-paragraph');
            await expect(reloaded).toContainText('— Втретє.');
            const reloadedLines = await reloaded.evaluate((el) => (el as HTMLElement).innerText.split('\n').filter((line) => line.length));
            expect(reloadedLines).toEqual(['— Привіт, — сказав він.', '— Привіт, — відповіла вона.', '— Втретє.']);
            // the second paragraph is untouched
            expect((await firstTexts(request, project.projectId))[1]).toBeNull();
            // one original paragraph, still one row
            await expect(page.locator('.translation-row .original-paragraph').first()).not.toHaveText('');
        } finally {
            await request.delete(`/api/projects/${project.projectId}`);
        }
    });
}
