import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// The phone / small-tablet layout (≤ 720 px is one column and a simplified interface; 820 px keeps the wide
// layout): the project information, the «Переклад» tab and an opened chapter never scroll sideways; on a phone the
// .docx downloads and the chapter actions are in the «⋯» of the top bar, the paragraph bar keeps «Перевірено»,
// «Вичитано» and «⋯», the glossary warning stays visible and the pinned strip does not cover the first paragraph.

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
        // connections are mocked: the result must not depend on what the e2e server's vault holds
        await page.route('**/api/connections', (route) => route.fulfill({ json: [] }));
        const title = `Mobile ${width} ${Date.now()}`;
        const project = await createProject(request, title);
        try {
            await openProject(page, title);

            // --- project information: the .docx downloads -----------------------------------------
            const exportButtons = page.locator('.project-export-actions button:not([hidden])');
            await expectNoSidewaysScroll(page, 'project information', ['.project-sticky-header', '.project-mode-navigation', '.project-export-actions button']);
            if (width <= 720) {
                // a phone: not in the page, in the «⋯» of the top bar; both still download
                await expect(exportButtons).toHaveCount(0);
                const more = page.locator('#header-more-button');
                await expect(more).toBeVisible();
                await more.click();
                await expect(page.locator('#export-bilingual-docx')).toBeVisible();
                await expect(page.locator('#export-translation-docx')).toBeVisible();
                await expect(page.locator('#translate-chapter-button')).toBeHidden(); // chapter actions only with an open chapter
                const downloadPromise = page.waitForEvent('download');
                await page.locator('#export-translation-docx').click();
                expect((await downloadPromise).suggestedFilename()).toMatch(/\.docx$/);
                await expect(page.locator('#header-more-panel')).toBeHidden();
            } else {
                await expect(exportButtons).toHaveCount(2);
                await expect(page.locator('#header-more-button')).toBeHidden();
                const titleBox = (await page.locator('#project-page-title').boundingBox())!;
                for (const button of await exportButtons.all()) {
                    const box = (await button.boundingBox())!;
                    const overlaps = box.x < titleBox.x + titleBox.width && box.x + box.width > titleBox.x
                        && box.y < titleBox.y + titleBox.height && box.y + box.height > titleBox.y;
                    expect(overlaps, 'export button over the title').toBe(false);
                    expect(box.x + box.width).toBeLessThanOrEqual(width);
                }
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

            if (width <= 720) {
                // --- the simplified phone interface -------------------------------------------------
                const row = page.locator('.translation-row').first();
                // paragraph bar: «Перевірено», «Вичитано», «⋯»; the variants, «У файл» and «Перекласти» are in the «⋯» panel
                await expect(row.locator('.paragraph-review:not(.menu-panel .paragraph-review)')).toHaveCount(2);
                await expect(row.locator('.para-menu-button')).toBeVisible();
                await expect(row.locator('.translate-paragraph-button')).toBeHidden();
                expect(await row.locator('.para-menu .translate-paragraph-button').count(), 'translate button lives in the menu').toBe(1);
                expect(await row.locator('.para-menu .variant-bar').count(), 'variant bar lives in the menu').toBe(1);
                // scroll first: a scroll after the tap closes a dropdown (the click itself must not scroll the page)
                await row.locator('.para-menu-button').evaluate((el) => el.scrollIntoView({ block: 'center' }));
                await page.waitForTimeout(300);
                await row.locator('.para-menu-button').click();
                await expect(row.locator('.translate-paragraph-button')).toBeVisible();
                await page.keyboard.press('Escape');
                await expect(row.locator('.translate-paragraph-button')).toBeHidden();
                // the glossary warning has its own slot in the bar, outside the menu: it is on the screen
                await row.evaluate((el) => {
                    const warning = document.createElement('p');
                    warning.className = 'variant-warning';
                    warning.textContent = '⚠ Gemini не використав термін глосарію: test → тест';
                    el.querySelector('.variant-warning-slot')!.append(warning);
                });
                await expect(row.locator('.variant-warning')).toBeVisible();
                expect(await row.locator('.para-menu .variant-warning').count()).toBe(0);
                await row.locator('.variant-warning').evaluate((el) => el.remove());
                // «Наступний невичитаний»: a compact icon button at the right edge of the chapter strip, which stays pinned
                const next = page.locator('#next-unproofread-button');
                await expect(page.locator('#chapter-list > #next-unproofread-button')).toBeVisible();
                const nextBox = (await next.boundingBox())!;
                expect(nextBox.width, 'compact').toBeLessThanOrEqual(48);
                expect(nextBox.x + nextBox.width, 'at the right edge of the strip').toBeGreaterThanOrEqual(width - 30);
                await expect(next).toHaveAccessibleName(/невичитан/i);
                await page.mouse.wheel(0, 900); // the strip is pinned under the top bar now, the button with it
                await expect(page.locator('#chapter-list')).toHaveClass(/chapters-strip--stuck/);
                await expect(next).toBeInViewport();
                expect((await next.boundingBox())!.y, 'in the pinned strip').toBeLessThan(110);
                const chip = (await page.locator('#chapter-list .chapter-button').first().boundingBox())!;
                expect(chip.width, 'the chapter chips keep their room').toBeGreaterThanOrEqual(100);
                await next.click(); // walks to the first paragraph without «Вичитано»
                await expect(page.locator('.translation-row.paragraph-row-current')).toHaveCount(1);
                await expect.poll(async () => { // the jump may still be scrolling; a scroll closes an open dropdown
                    const before = await page.evaluate(() => window.scrollY);
                    await page.waitForTimeout(200);
                    return before === await page.evaluate(() => window.scrollY);
                }).toBe(true);
                await expectNoSidewaysScroll(page, 'after «next unproofread»', ['#chapter-list', '#next-unproofread-button']);

                // the top bar «⋯»: the chapter actions, the engine switch and the «Ще ▾» items
                await expect(page.locator('#chapter-actions-row')).toBeHidden();
                await page.locator('#header-more-button').click();
                for (const id of ['translate-chapter-button', 'translation-provider-toggle', 'dictionary-toggle-button', 'compare-engines-toggle',
                    'mark-chapter-reviewed', 'mark-chapter-proofread', 'translation-settings-button', 'add-footnote', 'export-bilingual-docx']) {
                    await expect(page.locator(`#${id}`), id).toBeVisible();
                }
                // the moved switch still works: without a Claude connection the handler refuses and explains (as on a wide screen)
                await page.locator('#translation-provider-toggle label').filter({ hasText: 'Claude' }).click();
                await expect(page.locator('#translation-provider-hint')).toContainText('Немає підключення Claude');
                await expect(page.locator('#translation-provider-toggle input[value="deepl"]')).toBeChecked();
                await page.keyboard.press('Escape');
                await expect(page.locator('#translate-chapter-button')).toBeHidden();
                // undo / redo, save, search stay in the bar
                for (const id of ['undo-translation', 'redo-translation', 'save-translation', 'open-search']) {
                    await expect(page.locator(`#${id}`), id).toBeVisible();
                }
                const titleWidth = (await page.locator('#quick-actions-project-title').boundingBox())!.width;
                expect(titleWidth, 'the title keeps some room in the top bar').toBeGreaterThanOrEqual(50);

                // the same nodes go back on a wide screen and again to the menus: no copies, nothing lost
                await page.setViewportSize({ width: 1280, height: 900 });
                await expect(page.locator('#chapter-actions-row')).toBeVisible();
                await expect(page.locator('#chapter-actions-row #translate-chapter-button')).toBeVisible();
                await expect(page.locator('#chapter-actions-row #translation-provider-toggle')).toBeVisible();
                await expect(page.locator('#header-more-button')).toBeHidden();
                await expect(row.locator('.para-bar > .translate-paragraph-button')).toBeVisible();
                await expect(page.locator('#chapter-actions-checkboxes > #next-unproofread-button')).toBeVisible(); // back in the page
                await page.setViewportSize({ width, height });
                await expect(page.locator('#chapter-list > #next-unproofread-button')).toBeAttached(); // and at the strip edge again
                await expect(page.locator('#chapter-actions-row')).toBeHidden();
                await expect(page.locator('#header-more-button')).toBeVisible();
                for (const id of ['translate-chapter-button', 'translation-provider-toggle', 'export-bilingual-docx', 'next-unproofread-button']) {
                    expect(await page.locator(`#${id}`).count(), id).toBe(1);
                }
                expect(await row.locator('.translate-paragraph-button').count()).toBe(1);
            } else {
                await expect(page.locator('#chapter-actions-row')).toBeVisible();
                await expect(page.locator('#header-more-button')).toBeHidden();
                await expect(page.locator('.translation-row').first().locator('.para-bar > .translate-paragraph-button')).toBeVisible();
                await expect(page.locator('#chapter-actions-checkboxes > #next-unproofread-button')).toBeVisible(); // not moved on a wide screen
            }

            // the pinned strip does not cover the first paragraph: a jump to it lands below
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

test('mobile layout: a glossary warning of the real render stays visible under the bar, the variants are in «⋯»', async ({ page, request }) => {
    test.setTimeout(120_000);
    await page.setViewportSize({ width: 390, height: 844 });
    const title = `Mobile warning ${Date.now()}`;
    const project = await createProject(request, title);
    // The variant (with a warning) comes with the book structure, as it does from the server after a translation run.
    await page.route('**/book/structure', async (route) => {
        const response = await route.fetch();
        const body = await response.json();
        const first = body.chapters[0].elements.find((element: any) => element.paragraphId);
        first.translationVariants = [{
            variantId: 'variant-e2e-warning', engine: 'claude', model: 'e2e', text: first.translationText || 'Переклад',
            warnings: [{ type: 'glossary_missing', source: 'test EPUB', target: 'тестовий EPUB' }],
            promptHash: null, createdAt: '2026-10-14T20:00:00', updatedAt: '2026-10-14T20:00:00',
        }];
        first.selectedVariantId = 'variant-e2e-warning';
        await route.fulfill({ response, json: body });
    });
    try {
        await openProject(page, title);
        await openTranslationTab(page);
        await openFirstChapter(page);
        const row = page.locator('.translation-row').first();
        await row.scrollIntoViewIfNeeded();
        const warning = row.locator('.variant-warning');
        await expect(warning).toContainText('test EPUB → тестовий EPUB');
        await expect(warning).toBeVisible();
        expect(await row.locator('.para-menu .variant-warning').count(), 'the warning is not hidden in the menu').toBe(0);
        // the variant tabs and «У файл» are in the «⋯» panel, not in the bar
        await expect(row.locator('.variant-tab').first()).toBeHidden();
        await expect(row.locator('.variant-to-file')).toBeHidden();
        await row.locator('.para-menu-button').evaluate((el) => el.scrollIntoView({ block: 'center' }));
        await page.waitForTimeout(300);
        await row.locator('.para-menu-button').click();
        await expect(row.locator('.variant-tab').first()).toBeVisible();
        await expect(row.locator('.variant-to-file')).toBeVisible();
        await expectNoSidewaysScroll(page, 'warning row, menu open', ['.translation-row', '.para-bar', '.variant-warning']);
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});
