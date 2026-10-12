import { expect, test, type APIRequestContext, type Locator, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// With a docked side panel (search, replace, dictionary) open, collapsed or closed, the pinned rows (chapters,
// actions) have exactly the edges of the work area, and the panel starts right below the top bar (measured, so
// it follows the density) and ends at the bottom of the window. long-chapter.epub has an 80-paragraph chapter.

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

async function createConnection(request: APIRequestContext) {
    const response = await request.post('/api/connections', {
        data: { providerId: 'claude', displayName: 'claude geometry e2e', credentials: { apiKey: 'claude-e2e-key' } },
    });
    expect(response.ok(), await response.text()).toBeTruthy();
    const connection = await response.json();
    expect((await request.post(`/api/connections/${connection.connectionId}/test`)).ok()).toBeTruthy();
    return connection;
}

async function useUniqueModel(request: APIRequestContext, projectId: string, connectionId: string) {
    const current = await (await request.get(`/api/projects/${projectId}`)).json();
    const response = await request.put(`/api/projects/${projectId}`, {
        data: { ...current, aiConfiguration: { ...(current.aiConfiguration || {}), dictionary: { connectionId, model: `e2e-geometry-${Date.now()}-${Math.random().toString(36).slice(2, 7)}` } } },
    });
    expect(response.ok(), await response.text()).toBeTruthy();
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

// Scroll into the chapter until both rows are pinned.
async function pinRows(page: Page) {
    await page.locator('.translation-row').nth(30).scrollIntoViewIfNeeded();
    await page.mouse.wheel(0, 300);
    await expect(page.locator('#chapter-list')).toHaveClass(/chapters-strip--stuck/);
    await expect(page.locator('#chapter-actions-row')).toHaveClass(/chapter-actions--stuck/);
}

const rect = (locator: Locator) => locator.evaluate((el) => {
    const r = el.getBoundingClientRect();
    return { left: r.left, right: r.right, top: r.top, bottom: r.bottom };
});

async function expectRowsMatchWorkArea(page: Page, label: string) {
    await expect.poll(async () => {
        const area = await rect(page.locator('#chapter-browser'));
        const out: number[] = [];
        for (const selector of ['#chapter-list', '#chapter-actions-row']) {
            const r = await rect(page.locator(selector));
            out.push(Math.abs(r.left - area.left), Math.abs(r.right - area.right));
        }
        return Math.max(...out) <= 1;
    }, { message: `${label}: the pinned rows must have the edges of the work area (±1px)` }).toBe(true);
}

async function expectPanelGeometry(page: Page, panel: Locator, titleLocator: Locator, label: string) {
    const viewport = page.viewportSize()!;
    await expect.poll(async () => {
        const bar = await rect(page.locator('#quick-actions-bar'));
        const box = await rect(panel);
        return Math.abs(box.top - bar.bottom) <= 1 && Math.abs(box.bottom - viewport.height) <= 1;
    }, { message: `${label}: the panel starts at the bottom of the top bar and ends at the window bottom` }).toBe(true);

    // the title is visible and nothing covers it
    const title = await rect(titleLocator);
    const bar = await rect(page.locator('#quick-actions-bar'));
    expect(title.top, label).toBeGreaterThanOrEqual(bar.bottom - 1);
    const hit = await page.evaluate(({ x, y }) => {
        const element = document.elementFromPoint(x, y);
        return element ? element.closest('#search-dialog, #dictionary-sheet, #search-collapsed-tab') !== null : false;
    }, { x: (title.left + title.right) / 2, y: (title.top + title.bottom) / 2 });
    expect(hit, `${label}: the centre of the panel title belongs to the panel`).toBe(true);

    // the pinned rows end where the panel begins
    const panelBox = await rect(panel);
    for (const selector of ['#chapter-list', '#chapter-actions-row']) {
        expect((await rect(page.locator(selector))).right, `${label} ${selector}`).toBeLessThanOrEqual(panelBox.left + 1);
    }
}

for (const viewport of [{ width: 1280, height: 800 }, { width: 1440, height: 900 }, { width: 1920, height: 1080 }]) {
    test.describe(`Pinned rows and docked panels at ${viewport.width}×${viewport.height}`, () => {
        test.use({ viewport });

        test('closed, open, collapsed, dictionary: the rows follow the work area, the panel sits below the top bar', async ({ page, request }) => {
            test.setTimeout(150_000);
            const title = `Pinned geometry ${viewport.width} ${Date.now()}`;
            const project = await createLongProject(request, title);
            const connection = await createConnection(request);
            await useUniqueModel(request, project.projectId, connection.connectionId);
            try {
                await openFirstChapter(page, title);
                await pinRows(page);
                await expectRowsMatchWorkArea(page, 'panel closed');

                // search panel open
                await page.locator('#open-search').click();
                await expect(page.locator('#search-dialog')).toBeVisible();
                await expectRowsMatchWorkArea(page, 'search open');
                await expectPanelGeometry(page, page.locator('#search-dialog .search-dialog-content'), page.locator('#search-dialog-title'), 'search open');

                // replace mode: same geometry
                await page.getByRole('button', { name: 'Знайти й замінити' }).click();
                await expectRowsMatchWorkArea(page, 'replace open');
                await expectPanelGeometry(page, page.locator('#search-dialog .search-dialog-content'), page.locator('#search-dialog-title'), 'replace open');

                // collapsed into the strip
                await page.locator('#collapse-search-panel').click();
                await expect(page.locator('#search-collapsed-tab')).toBeVisible();
                await expectRowsMatchWorkArea(page, 'search collapsed');
                const tab = page.locator('#search-collapsed-tab');
                await expect.poll(async () => Math.abs((await rect(tab)).top - (await rect(page.locator('#quick-actions-bar'))).bottom)).toBeLessThanOrEqual(1);
                expect((await rect(tab)).left).toBeGreaterThanOrEqual((await rect(page.locator('#chapter-list'))).right - 1);

                // closed again
                await tab.click();
                await page.locator('#close-search-dialog').click();
                await expect(page.locator('#search-dialog')).toBeHidden();
                await expectRowsMatchWorkArea(page, 'search closed');

                // dictionary: Alt+click on a word of an original paragraph
                const point = await page.evaluate(() => {
                    for (const original of Array.from(document.querySelectorAll('.translation-row .original-paragraph'))) {
                        const rectangle = (original as HTMLElement).getBoundingClientRect();
                        if (rectangle.top < 220 || rectangle.bottom > window.innerHeight - 60) continue;
                        const walker = document.createTreeWalker(original, NodeFilter.SHOW_TEXT);
                        const node = walker.nextNode() as Text | null;
                        const index = node ? (node.nodeValue || '').indexOf('chapter') : -1;
                        if (node && index >= 0) {
                            const range = document.createRange();
                            range.setStart(node, index);
                            range.setEnd(node, index + 7);
                            const r = range.getBoundingClientRect();
                            return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
                        }
                    }
                    return null;
                });
                expect(point, 'a visible original paragraph with a word').not.toBeNull();
                await page.keyboard.down('Alt');
                await page.mouse.click(point!.x, point!.y);
                await page.keyboard.up('Alt');
                await expect(page.locator('#dictionary-sheet')).toBeVisible();
                await expectRowsMatchWorkArea(page, 'dictionary open');
                await expectPanelGeometry(page, page.locator('#dictionary-sheet'), page.locator('#dictionary-term'), 'dictionary open');
                await page.keyboard.press('Escape');
                await expect(page.locator('#dictionary-sheet')).toBeHidden();
                await expectRowsMatchWorkArea(page, 'dictionary closed');
            } finally {
                await request.delete(`/api/projects/${project.projectId}`);
            }
        });
    });
}

test('the panel top follows the top bar in both densities', async ({ page, request }) => {
    test.setTimeout(120_000);
    await page.setViewportSize({ width: 1440, height: 900 });
    const title = `Pinned density ${Date.now()}`;
    const project = await createLongProject(request, title);
    try {
        await openFirstChapter(page, title);
        for (const density of ['normal', 'compact']) {
            await page.locator('#translation-settings-button').click();
            await page.locator('#density-select').selectOption(density);
            await expect(page.locator('html')).toHaveAttribute('data-density', density);
            await page.keyboard.press('Escape');
            await pinRows(page);
            await page.locator('#open-search').click();
            const panel = page.locator('#search-dialog .search-dialog-content');
            await expectPanelGeometry(page, panel, page.locator('#search-dialog-title'), `density ${density}`);
            await expectRowsMatchWorkArea(page, `density ${density}`);
            const topbar = await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--topbar-h'));
            const bar = await rect(page.locator('#quick-actions-bar'));
            expect(Math.abs(parseFloat(topbar) - bar.bottom), `--topbar-h at ${density}`).toBeLessThanOrEqual(1);
            await page.locator('#close-search-dialog').click();
        }
        await page.evaluate(() => localStorage.removeItem('workbench.density'));
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});
