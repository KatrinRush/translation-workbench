import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// The phone / small-tablet layout (≤ 720 px is one column; 820 px keeps the wider layout): the project
// information, the «Переклад» tab and an opened chapter must never scroll sideways, the export buttons sit
// under the project title, and the pinned «Перекласти розділ» block does not cover the first paragraph.

const sizes: Array<[number, number]> = [[390, 844], [820, 1180]];

async function createProject(request: APIRequestContext, title: string) {
    const project = await (await request.post('/api/projects', { data: { title, status: 'translation' } })).json();
    const upload = await request.post('/upload', {
        headers: { 'X-Project-Id': project.projectId },
        multipart: { file: { name: 'long-chapter.epub', mimeType: 'application/epub+zip', buffer: fs.readFileSync(path.join(__dirname, '..', 'test-data', 'long-chapter.epub')) } },
    });
    expect(upload.ok()).toBeTruthy();
    const structure = await (await request.get(`/api/projects/${project.projectId}/book/structure`)).json();
    const ids = structure.chapters[0].elements.filter((e: any) => e.paragraphId).map((e: any) => e.paragraphId);
    for (const id of ids.slice(0, 6)) {
        expect((await request.put(`/api/paragraphs/${id}`, { data: { translationText: 'Дрейвен прийшов до моря, де гуси сперечалися над ранковим уловом.', reviewed: false } })).ok()).toBeTruthy();
    }
    return project;
}

async function openProject(page: Page, title: string) {
    await page.goto('/');
    await page.locator('.project-card').filter({ hasText: title }).getByRole('button', { name: 'Відкрити проєкт' }).click();
    await expect(page.locator('#project-page-title')).toContainText(title);
}

async function openTranslationTab(page: Page) {
    await page.getByRole('button', { name: 'Переклад', exact: true }).click();
    await expect(page.locator('#project-submode-navigation')).toBeVisible();
}

async function openFirstChapter(page: Page) {
    const showStructure = page.getByRole('button', { name: 'Переглянути структуру книги' });
    const firstChapter = page.locator('.chapter-button').first();
    await expect(showStructure.or(firstChapter).first()).toBeVisible();
    if (!(await firstChapter.isVisible())) await showStructure.click();
    await firstChapter.click();
    await expect(page.locator('.translation-row').first()).toBeVisible();
}

// The page is never wider than the screen. documentElement.scrollWidth is the contract; the blocks listed
// are checked too, because html/body clip the overflow and a wide child would still shift the layout.
async function expectNoSidewaysScroll(page: Page, where: string, selectors: string[] = []) {
    const { scrollWidth, innerWidth, bodyScrollWidth } = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        innerWidth: window.innerWidth,
        bodyScrollWidth: document.body.scrollWidth,
    }));
    expect(scrollWidth, `${where}: documentElement.scrollWidth`).toBeLessThanOrEqual(innerWidth);
    expect(bodyScrollWidth, `${where}: body.scrollWidth`).toBeLessThanOrEqual(innerWidth);
    for (const selector of selectors) {
        const rights = await page.evaluate((sel) => Array.from(document.querySelectorAll(sel))
            .filter((el) => (el as HTMLElement).offsetParent !== null || getComputedStyle(el).position === 'fixed')
            .map((el) => el.getBoundingClientRect().right), selector);
        for (const right of rights) expect(right, `${where}: ${selector}`).toBeLessThanOrEqual(innerWidth + 1);
    }
}

for (const [width, height] of sizes) {
    test(`mobile layout at ${width}×${height}: project info, «Переклад» tab, opened chapter`, async ({ page, request }) => {
        test.setTimeout(120_000);
        await page.setViewportSize({ width, height });
        const title = `Mobile ${width} ${Date.now()}`;
        const project = await createProject(request, title);
        try {
            await openProject(page, title);

            // --- project information: the export buttons stay out of the title ---------------------
            const exportButtons = page.locator('.project-export-actions button:not([hidden])');
            await expect(exportButtons).toHaveCount(2);
            await expectNoSidewaysScroll(page, 'project information', ['.project-sticky-header', '.project-mode-navigation', '.project-export-actions button']);
            const titleBox = (await page.locator('#project-page-title').boundingBox())!;
            for (const button of await exportButtons.all()) {
                const box = (await button.boundingBox())!;
                const overlaps = box.x < titleBox.x + titleBox.width && box.x + box.width > titleBox.x
                    && box.y < titleBox.y + titleBox.height && box.y + box.height > titleBox.y;
                expect(overlaps, 'export button over the title').toBe(false);
                expect(box.x).toBeGreaterThanOrEqual(0);
                expect(box.x + box.width).toBeLessThanOrEqual(width);
                if (width <= 720) expect(box.y, 'under the title, in the flow').toBeGreaterThanOrEqual(titleBox.y + titleBox.height - 1);
            }

            // --- «Переклад» tab -------------------------------------------------------------------
            await openTranslationTab(page);
            await expectNoSidewaysScroll(page, 'translation tab', [
                '.project-sticky-header', '.project-export-actions button', '.project-mode-navigation',
                '#project-submode-navigation', '.project-mode-content', '.file-details',
            ]);
            // the tab rows may scroll inside themselves, they do not widen the page
            for (const selector of ['.project-mode-navigation', '#project-submode-navigation']) {
                const box = (await page.locator(selector).boundingBox())!;
                expect(box.x + box.width, selector).toBeLessThanOrEqual(width + 1);
            }
            if (width <= 720) {
                // cards: one column
                const xs = await page.evaluate(() => Array.from(document.querySelectorAll('.file-details > div'))
                    .filter((el) => (el as HTMLElement).offsetParent !== null)
                    .map((el) => Math.round(el.getBoundingClientRect().x)));
                expect(xs.length).toBeGreaterThan(2);
                expect(new Set(xs).size, 'file cards in one column').toBe(1);
            }

            // --- opened chapter -------------------------------------------------------------------
            await openFirstChapter(page);
            await page.evaluate(() => document.querySelector('#chapter-text')!.scrollIntoView());
            await expectNoSidewaysScroll(page, 'opened chapter', [
                '#workspace-content', '.chapter-text', '.translation-row', '.original-paragraph', '.translation-paragraph', '.para-bar', '.para-bar > *',
            ]);

            // the paragraph service bar and its children stay on the screen
            const bar = (await page.locator('.translation-row').first().locator('.para-bar').boundingBox())!;
            expect(bar.x).toBeGreaterThanOrEqual(0);
            expect(bar.x + bar.width).toBeLessThanOrEqual(width + 1);

            if (width <= 720) {
                // no side strips: the text uses the screen width
                const text = (await page.locator('.original-paragraph').first().boundingBox())!;
                expect(text.width, 'paragraph text width').toBeGreaterThanOrEqual(width - 90);

                // original above translation, no stretched gap between them (no inline height, no 92px floors)
                const gap = await page.evaluate(() => {
                    const row = document.querySelector('.translation-row')!;
                    const original = row.querySelector('.original-paragraph') as HTMLElement;
                    const control = row.querySelector('.translation-control') as HTMLElement;
                    const o = original.getBoundingClientRect();
                    const c = control.getBoundingClientRect();
                    return { inlineHeight: original.style.height, gap: c.top - o.bottom, sameColumn: Math.abs(o.x - c.x) < 4, minHeight: parseFloat(getComputedStyle(original).minHeight) };
                });
                expect(gap.sameColumn, 'stacked, not side by side').toBe(true);
                expect(gap.inlineHeight, 'no equalized height in one column').toBe('');
                expect(gap.gap, 'gap between original and translation').toBeLessThanOrEqual(24);
                expect(gap.minHeight).toBeLessThanOrEqual(48);

                // and the textarea still shows its whole text (it does not grow by itself)
                const fits = await page.locator('.translation-row').first().locator('.translation-paragraph').evaluate((el) => el.scrollHeight <= el.clientHeight + 1);
                expect(fits, 'translation textarea fits its text').toBe(true);
            }

            // the pinned «Перекласти розділ» block does not cover the first paragraph: a jump to it lands below
            await page.locator('.translation-row').first().evaluate((el) => el.scrollIntoView({ block: 'start' }));
            await page.waitForTimeout(400);
            const geometry = await page.evaluate(() => {
                const stackBottom = Math.max(...['#quick-actions-bar', '.chapter-list.chapters-strip--stuck', '.chapter-actions--stuck']
                    .map((selector) => document.querySelector(selector)?.getBoundingClientRect().bottom ?? 0));
                const row = document.querySelector('.translation-row')!;
                const firstButton = row.querySelector('.para-bar button')!;
                return { stackBottom, rowTop: row.getBoundingClientRect().top, buttonTop: firstButton.getBoundingClientRect().top };
            });
            expect(geometry.rowTop, 'first paragraph below the pinned block').toBeGreaterThanOrEqual(geometry.stackBottom - 1);
            expect(geometry.buttonTop, 'its buttons below the pinned block').toBeGreaterThanOrEqual(geometry.stackBottom - 1);
            await expectNoSidewaysScroll(page, 'opened chapter, scrolled');
        } finally {
            await request.delete(`/api/projects/${project.projectId}`);
        }
    });
}
