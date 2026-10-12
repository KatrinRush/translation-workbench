import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Search (🔍) lives in the docked side panel (desktop) or the bottom sheet (tablet/phone); there is no
// separate bottom bar. long-chapter.epub: chapter 1 has 80 paragraphs that all mention "gulls"
// (the search caps results at 50), only no. 60 mentions the lighthouse; eleven more one-paragraph chapters.

async function createLongProject(request: APIRequestContext, title: string) {
    const created = await request.post('/api/projects', { data: { title, status: 'translation' } });
    expect(created.ok()).toBeTruthy();
    const project = await created.json();
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
    await expect(page.locator('.translation-row')).toHaveCount(80);
}

const currentMatches = (page: Page) => page.evaluate(() => {
    const highlight = (CSS as any).highlights?.get('search-current');
    return highlight ? Array.from(highlight.values()).map((range: any) => range.toString()) : [];
});

for (const viewport of [{ width: 1280, height: 800 }, { width: 1440, height: 900 }, { width: 1920, height: 1080 }]) {
    test.describe(`Search panel at ${viewport.width}×${viewport.height}`, () => {
        test.use({ viewport });

        test('docked panel: no bottom bar, ‹ › Enter, click, return, Esc, collapse, one docked panel', async ({ page, request }) => {
            test.setTimeout(120_000);
            const title = `Search panel ${viewport.width} ${Date.now()}`;
            const project = await createLongProject(request, title);
            try {
                await openFirstChapter(page, title);
                await page.locator('#open-search').click();
                const dialog = page.locator('#search-dialog');
                await expect(dialog).toBeVisible();
                await expect(page.locator('#search-nav-bar')).toHaveCount(0);

                const input = page.locator('#search-input');
                await input.fill('gulls');
                const items = page.locator('#search-results .search-result-item');
                await expect(items).toHaveCount(50);
                await expect(page.locator('#search-status')).toContainText('50');
                await expect(page.locator('#search-return')).toBeHidden();

                // a click on a match: the panel stays, the status counts paragraphs, the match is highlighted
                await items.nth(6).click();
                await expect(dialog).toBeVisible();
                await expect(page.locator('#search-status')).toContainText('збіг 7 з 50');
                await expect(items.nth(6)).toHaveAttribute('aria-current', 'true');
                await expect.poll(() => currentMatches(page)).toHaveLength(1);
                await expect(page.locator('#search-return')).toBeVisible();

                // ‹ › and Enter / Shift+Enter in the input
                await page.locator('#search-next').click();
                await expect(page.locator('#search-status')).toContainText('збіг 8 з 50');
                await page.locator('#search-prev').click();
                await expect(page.locator('#search-status')).toContainText('збіг 7 з 50');
                await input.press('Enter');
                await expect(page.locator('#search-status')).toContainText('збіг 8 з 50');
                await input.press('Shift+Enter');
                await expect(page.locator('#search-status')).toContainText('збіг 7 з 50');

                // nothing is under the panel and the list does not hide the footer buttons
                const panel = (await dialog.locator('.search-dialog-content').boundingBox())!;
                const rows = (await page.locator('#translation-rows').boundingBox())!;
                expect(rows.x + rows.width).toBeLessThanOrEqual(panel.x + 1);
                const next = (await page.locator('#search-next').boundingBox())!;
                expect(next.y + next.height).toBeLessThanOrEqual(viewport.height);

                // "← Повернутися" goes back to where the search started
                await page.locator('#search-return').click();
                await expect(page.locator('#search-return')).toBeHidden();
                await expect(dialog).toBeVisible();

                // collapse into the vertical strip, persisted, and expand again with the query kept
                await page.locator('#collapse-search-panel').click();
                const tab = page.locator('#search-collapsed-tab');
                await expect(tab).toBeVisible();
                await expect(tab).toContainText('Пошук');
                expect(await page.evaluate(() => window.localStorage.getItem('workbench.searchPanelCollapsed'))).toBe('1');
                await expect(dialog.locator('.search-dialog-content')).toBeHidden();
                const strip = (await tab.boundingBox())!;
                expect(strip.width).toBeLessThan(80);
                await tab.click();
                await expect(dialog.locator('.search-dialog-content')).toBeVisible();
                await expect(input).toHaveValue('gulls');
                await expect(items).toHaveCount(50);
                expect(await page.evaluate(() => window.localStorage.getItem('workbench.searchPanelCollapsed'))).toBe('0');

                // Esc closes the panel; reopening keeps the query and selects the text
                await input.press('Escape');
                await expect(dialog).toBeHidden();
                await page.locator('#open-search').click();
                await expect(input).toHaveValue('gulls');
                expect(await input.evaluate((el: HTMLInputElement) => el.selectionEnd! - el.selectionStart!)).toBe(5);
                await expect(items).toHaveCount(50);

                // one docked panel at a time: the dictionary hides the search, 🔍 brings it back
                await page.locator('#close-search-dialog').click();
                await expect(dialog).toBeHidden();
                await expect.poll(() => page.evaluate(() => document.body.classList.contains('search-panel-open'))).toBe(false);
            } finally {
                await page.evaluate(() => window.localStorage.removeItem('workbench.searchPanelCollapsed')).catch(() => {});
                await request.delete(`/api/projects/${project.projectId}`);
            }
        });
    });
}

for (const viewport of [{ width: 1024, height: 768 }, { width: 820, height: 1180 }, { width: 390, height: 844 }]) {
    test.describe(`Search sheet at ${viewport.width}×${viewport.height}`, () => {
        test.use({ viewport, hasTouch: true });

        test('bottom sheet: visible, big buttons, nothing covered, no separate bar', async ({ page, request }) => {
            test.setTimeout(120_000);
            const title = `Search sheet ${viewport.width} ${Date.now()}`;
            const project = await createLongProject(request, title);
            try {
                await openFirstChapter(page, title);
                await page.locator('#open-search').click();
                const dialog = page.locator('#search-dialog');
                await expect(dialog).toBeVisible();
                await expect(page.locator('#search-nav-bar')).toHaveCount(0);
                await page.locator('#search-input').fill('gulls');
                const items = page.locator('#search-results .search-result-item');
                await expect(items).toHaveCount(50);
                await items.nth(6).click();
                await expect(page.locator('#search-status')).toContainText('збіг 7 з 50');

                for (const id of ['#search-prev', '#search-next', '#search-return', '#close-search-dialog']) {
                    const box = (await page.locator(id).boundingBox())!;
                    expect(box.height, id).toBeGreaterThanOrEqual(43.5);
                    expect(box.width, id).toBeGreaterThanOrEqual(43.5);
                    expect(box.y + box.height, id).toBeLessThanOrEqual(viewport.height + 1);
                }
                const sheet = (await dialog.locator('.search-dialog-content').boundingBox())!;
                expect(sheet.height).toBeLessThanOrEqual(viewport.height * 0.48 + 2);

                // the current match stays above the sheet
                await expect.poll(async () => page.evaluate((sheetTop) => {
                    const range = [...((CSS as any).highlights?.get('search-current') ?? [])][0] as Range | undefined;
                    const rect = range?.getBoundingClientRect();
                    return Boolean(rect) && rect!.bottom <= sheetTop + 1 && rect!.top >= 0;
                }, sheet.y)).toBe(true);

                await page.locator('#close-search-dialog').click();
                await expect(dialog).toBeHidden();
            } finally {
                await request.delete(`/api/projects/${project.projectId}`);
            }
        });
    });
}
