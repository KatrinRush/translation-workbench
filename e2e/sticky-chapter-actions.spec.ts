import { expect, test, type APIRequestContext, type Locator, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// test-data/long-chapter.epub: chapter 1 has 80 paragraphs (only no. 60 mentions the
// lighthouse, all mention gulls), then eleven one-paragraph chapters.

async function createLongProject(request: APIRequestContext, title: string) {
    const created = await request.post('/api/projects', { data: { title, status: 'translation' } });
    expect(created.ok()).toBeTruthy();
    const project = await created.json();
    const upload = await request.post('/upload', {
        headers: { 'X-Project-Id': project.projectId },
        multipart: {
            file: {
                name: 'long-chapter.epub',
                mimeType: 'application/epub+zip',
                buffer: fs.readFileSync(path.join(__dirname, '..', 'test-data', 'long-chapter.epub')),
            },
        },
    });
    expect(upload.ok()).toBeTruthy();
    return project;
}

async function openFirstChapter(page: Page, title: string) {
    await page.goto('/');
    await page.locator('.project-card').filter({ hasText: title }).getByRole('button', { name: 'Відкрити проєкт' }).click();
    await page.getByRole('button', { name: 'Переклад', exact: true }).click();
    // A project reopened in the same browser restores its book view; a fresh one asks first.
    const showStructure = page.getByRole('button', { name: 'Переглянути структуру книги' });
    const firstChapter = page.locator('.chapter-button').first();
    await expect(showStructure.or(firstChapter).first()).toBeVisible();
    if (!(await firstChapter.isVisible())) {
        await showStructure.click();
    }
    await firstChapter.click();
    await expect(page.locator('.translation-row')).toHaveCount(80);
}

// Bottom edge of everything pinned at the top of the viewport.
async function pinnedStackBottom(page: Page) {
    return page.evaluate(() => Math.max(
        ...['#quick-actions-bar', '.chapter-list.chapters-strip--stuck', '.chapter-actions--stuck']
            .map((selector) => document.querySelector(selector)?.getBoundingClientRect().bottom ?? 0),
    ));
}

// The current search match (a Range in the `search-current` highlight): it must sit below the pinned
// block and above the search sheet that docks at the bottom.
async function currentMatchBox(page: Page) {
    return page.evaluate(() => {
        const range = [...((CSS as any).highlights?.get('search-current') ?? [])][0] as Range | undefined;
        const rect = range?.getBoundingClientRect();
        return rect ? { y: rect.y, height: rect.height } : null;
    });
}

async function expectFullyUncovered(page: Page, target: Locator | null) {
    await expect.poll(async () => {
        const box = target ? await target.boundingBox() : await currentMatchBox(page);
        const top = await pinnedStackBottom(page);
        const sheet = await page.locator('#search-dialog .search-dialog-content').boundingBox();
        const viewport = page.viewportSize()!;
        const visibleBottom = sheet && !(await page.locator('#search-dialog').isHidden()) ? sheet.y : viewport.height;
        return Boolean(box) && box!.y >= top && box!.y + box!.height <= visibleBottom;
    }, { message: 'target must sit below the pinned block and above the search sheet' }).toBe(true);
}

for (const viewport of [{ width: 1024, height: 768 }, { width: 820, height: 1180 }, { width: 390, height: 844 }]) {
    test.describe(`Pinned chapter actions at ${viewport.width}×${viewport.height}`, () => {
        test.use({ viewport });

        test('translate button and engine switch stay visible after scrolling down, in one compact row', async ({ page, request }) => {
            const title = `Sticky actions ${viewport.width} ${Date.now()}`;
            const project = await createLongProject(request, title);
            try {
                await openFirstChapter(page, title);
                await page.locator('.translation-row').last().scrollIntoViewIfNeeded();
                await page.mouse.wheel(0, 400);

                const actions = page.locator('#chapter-actions-row');
                await expect(actions).toHaveClass(/chapter-actions--stuck/);
                await expect(page.locator('#chapter-list')).toHaveClass(/chapters-strip--stuck/);
                for (const control of [
                    page.locator('#translate-chapter-button'),
                    page.locator('#translation-provider-toggle'),
                ]) {
                    await expect(control).toBeInViewport();
                    const box = await control.boundingBox();
                    expect(box!.y).toBeLessThan(140);
                    expect(box!.height).toBeGreaterThanOrEqual(32); // compact density: 32px controls
                }
                // One line: no wrapping inside the pinned row, and the whole block stays compact.
                const rowBox = await actions.boundingBox();
                expect(rowBox!.height).toBeLessThan(50);
                // Pinned rows stay inside the screen horizontally (they scroll sideways instead).
                for (const pinned of [actions, page.locator('#chapter-list')]) {
                    const box = await pinned.boundingBox();
                    expect(box!.x).toBeGreaterThanOrEqual(0);
                    expect(box!.x + box!.width).toBeLessThanOrEqual(viewport.width);
                }
                expect(await pinnedStackBottom(page)).toBeLessThanOrEqual(140);
                for (const chip of await page.locator('.chapter-list.chapters-strip--stuck .chapter-button').all()) {
                    expect((await chip.boundingBox())!.height).toBeGreaterThanOrEqual(40);
                }
                // Heading, counters and checkboxes stay in the flow.
                await expect(page.locator('#chapter-title')).not.toBeInViewport();
                await expect(page.locator('#chapter-export-checkbox')).not.toBeInViewport();

                // Collapse: nothing but the top bar is pinned; the choice survives a reload.
                await page.locator('#toggle-sticky-panels').click();
                await expect(actions).not.toHaveClass(/chapter-actions--stuck/);
                await expect(page.locator('#translate-chapter-button')).not.toBeInViewport();
                expect(await page.evaluate(() => window.localStorage.getItem('workbench.stickyPanelsCollapsed'))).toBe('true');
                await openFirstChapter(page, title);
                await page.locator('.translation-row').last().scrollIntoViewIfNeeded();
                await expect(page.locator('#toggle-sticky-panels')).toHaveAttribute('aria-expanded', 'false');
                await expect(actions).not.toHaveClass(/chapter-actions--stuck/);
                await page.locator('#toggle-sticky-panels').click();
                await expect(actions).toHaveClass(/chapter-actions--stuck/);
                await expect(page.locator('#translate-chapter-button')).toBeInViewport();
            } finally {
                await page.evaluate(() => window.localStorage.removeItem('workbench.stickyPanelsCollapsed')).catch(() => {});
                await request.delete(`/api/projects/${project.projectId}`);
            }
        });

        test('search jumps and ‹ › keep the paragraph clear of the pinned block', async ({ page, request }) => {
            const title = `Sticky search ${viewport.width} ${Date.now()}`;
            const project = await createLongProject(request, title);
            try {
                await openFirstChapter(page, title);
                await page.locator('#open-search').click();
                await page.locator('#search-input').fill('lighthouse');
                await page.locator('.search-result-item').first().click();
                await expect(page.locator('#chapter-actions-row')).toHaveClass(/chapter-actions--stuck/);
                // the matched words (not the whole row, whose editor may reach under the sheet) are clear
                await expectFullyUncovered(page, null);

                await page.locator('#close-search-dialog').click();
                await page.locator('#open-search').click();
                await page.locator('#search-input').fill('gulls');
                await expect(page.locator('.search-result-item')).toHaveCount(50);  // the search caps results at 50
                await page.locator('.search-result-item').nth(39).click();
                await expect(page.locator('#search-status')).toContainText('40 з 50');
                await expectFullyUncovered(page, null);
                await page.locator('#search-next').click();
                await expect(page.locator('#search-status')).toContainText('41 з 50');
                await expectFullyUncovered(page, null);
                await page.locator('#search-return').click();
                await expect(page.locator('#search-return')).toBeHidden();
            } finally {
                await request.delete(`/api/projects/${project.projectId}`);
            }
        });
    });
}
