import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// The compact layout: the chapter heading and the actions row, the service bar under each paragraph, the
// density setting, the «Ще ▾» / «⋯» menus and the search/replace panel, at 1280/1440/1920 and 1024/820/390.
// long-chapter.epub has 12 chapters; chapter 1 gets translations in its first six paragraphs.

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
    await page.getByRole('button', { name: 'Переклад', exact: true }).click();
    const showStructure = page.getByRole('button', { name: 'Переглянути структуру книги' });
    const firstChapter = page.locator('.chapter-button').first();
    await expect(showStructure.or(firstChapter).first()).toBeVisible();
    if (!(await firstChapter.isVisible())) await showStructure.click();
    await firstChapter.click();
    await expect(page.locator('.translation-row').first()).toBeVisible();
    await page.evaluate(() => document.querySelector('#chapter-text')!.scrollIntoView());
}

const sizes = [[1280, 800], [1440, 900], [1920, 1080], [1024, 768], [820, 1180], [390, 844]];

for (const [width, height] of sizes) {
    test(`layout at ${width}×${height}: actions, heading, service bar, alignment`, async ({ page, request }) => {
        test.setTimeout(120_000);
        await page.setViewportSize({ width, height });
        const title = `Compact ${width} ${Date.now()}`;
        const project = await createProject(request, title);
        try {
            await openProject(page, title);

            // the heading keeps a readable width and is not covered by the actions
            const heading = (await page.locator('.chapter-heading-content').boundingBox())!;
            expect(heading.width).toBeGreaterThanOrEqual(Math.min(250, width - 80));
            if (width <= 720) {
                // a phone: the actions row is not shown, its controls live in the «⋯» of the top bar (mobile-layout.spec.ts)
                await expect(page.locator('#chapter-actions-row')).toBeHidden();
                await expect(page.locator('#header-more-button')).toBeVisible();
            } else {
                const actions = (await page.locator('#chapter-actions-row').boundingBox())!;
                expect(actions.y).toBeGreaterThanOrEqual(heading.y + heading.height - 1); // under the heading, not over it

                // the action buttons have a size, never overlap and never leave the screen sideways
                const boxes = await page.evaluate(() => Array.from(document.querySelectorAll('#chapter-actions-row > *'))
                    .filter((el) => (el as HTMLElement).offsetParent !== null)
                    .map((el) => { const r = el.getBoundingClientRect(); return { id: el.id || el.className.toString().slice(0, 30), x: r.x, y: r.y, w: r.width, h: r.height }; }));
                expect(boxes.length).toBeGreaterThanOrEqual(5);
                for (const box of boxes) {
                    expect(box.w, box.id).toBeGreaterThan(0);
                    expect(box.h, box.id).toBeGreaterThan(0);
                }
                for (let i = 0; i < boxes.length; i++) {
                    for (let j = i + 1; j < boxes.length; j++) {
                        const a = boxes[i], b = boxes[j];
                        const overlap = a.x < b.x + b.w - 1 && b.x < a.x + a.w - 1 && a.y < b.y + b.h - 1 && b.y < a.y + a.h - 1;
                        expect(overlap, `${a.id} / ${b.id}`).toBe(false);
                    }
                }
            }
            expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);

            // the service bar: under the text, compact, the same height in every paragraph
            await page.locator('.translation-row').nth(1).scrollIntoViewIfNeeded();
            const rows = await page.evaluate(() => Array.from(document.querySelectorAll('.translation-row')).slice(0, 5).map((row) => {
                const text = (row.querySelector('.translation-paragraph') as HTMLElement).getBoundingClientRect();
                const original = (row.querySelector('.original-paragraph') as HTMLElement).getBoundingClientRect();
                const bar = (row.querySelector('.para-bar') as HTMLElement).getBoundingClientRect();
                const textStyle = getComputedStyle(row.querySelector('.translation-paragraph') as HTMLElement);
                return { textTop: text.top, textBottom: text.bottom, originalTop: original.top, barTop: bar.top, barHeight: bar.height, paddingTop: textStyle.paddingTop };
            }));
            for (const row of rows) {
                expect(row.barTop).toBeGreaterThanOrEqual(row.textBottom - 1); // under the translation text
                expect(row.barHeight).toBeLessThanOrEqual(112); // at most three compact lines
                if (width > 720) expect(Math.abs(row.originalTop - row.textTop)).toBeLessThanOrEqual(2); // both columns start at the same level
            }
            expect(new Set(rows.map((row) => Math.round(row.barHeight))).size).toBe(1); // the same height in every paragraph
            if (width >= 1280) expect(rows[0].barHeight).toBeLessThanOrEqual(44); // one line when there is room
            // the long «Редагування тексту для файлу…» sentence is not repeated in every paragraph
            expect(await page.locator('.variant-meta-long:visible').count()).toBeLessThanOrEqual(1);
        } finally {
            await request.delete(`/api/projects/${project.projectId}`);
        }
    });
}

test('density: compact by default for a mouse, a choice is remembered', async ({ page, request }) => {
    test.setTimeout(90_000);
    await page.setViewportSize({ width: 1440, height: 900 });
    const title = `Compact density ${Date.now()}`;
    const project = await createProject(request, title);
    try {
        await openProject(page, title);
        await expect(page.locator('html')).toHaveAttribute('data-density', 'compact');
        const compactHeight = (await page.locator('.translate-paragraph-button').first().boundingBox())!.height;
        expect(compactHeight).toBeLessThanOrEqual(34);

        await page.locator('#translation-settings-button').click();
        const select = page.locator('#density-select');
        await expect(select).toHaveValue('compact');
        await select.selectOption('normal');
        await expect(page.locator('html')).toHaveAttribute('data-density', 'normal');
        await page.keyboard.press('Escape');
        expect((await page.locator('.translate-paragraph-button').first().boundingBox())!.height).toBeGreaterThanOrEqual(38);

        await page.reload();
        await expect(page.locator('html')).toHaveAttribute('data-density', 'normal');
        expect(await page.evaluate(() => localStorage.getItem('workbench.density'))).toBe('normal');
        await page.evaluate(() => localStorage.removeItem('workbench.density'));
        await page.reload();
        await expect(page.locator('html')).toHaveAttribute('data-density', 'compact');
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});

test.describe('touch device: targets stay at least 44px in both densities', () => {
    test.use({ hasTouch: true, isMobile: true, viewport: { width: 820, height: 1180 } });

    for (const density of ['compact', 'normal']) {
        test(`${density}`, async ({ page, request }) => {
            test.setTimeout(90_000);
            const title = `Compact touch ${density} ${Date.now()}`;
            const project = await createProject(request, title);
            try {
                await page.addInitScript((value) => { try { localStorage.setItem('workbench.density', value); } catch { /* blocked */ } }, density);
                await openProject(page, title);
                expect(await page.evaluate(() => matchMedia('(pointer: coarse)').matches)).toBe(true);
                await expect(page.locator('html')).toHaveAttribute('data-density', density);
                const small = await page.evaluate(() => {
                    const selectors = ['.variant-tab', '.variant-to-file', '.translate-paragraph-button', '.para-menu-button', '#chapter-more-button',
                        '#dictionary-toggle-button', '#translate-chapter-button', '#translation-settings-button'];
                    return selectors.flatMap((selector) => Array.from(document.querySelectorAll(selector))
                        .filter((el) => (el as HTMLElement).offsetParent !== null)
                        .map((el) => ({ selector, h: Math.round(el.getBoundingClientRect().height) }))).filter((item) => item.h < 44);
                });
                expect(small).toEqual([]);
            } finally {
                await request.delete(`/api/projects/${project.projectId}`);
            }
        });
    }
});

test('menus: «Ще ▾» and «⋯» open, move with the arrows, close with Esc and a click outside', async ({ page, request }) => {
    test.setTimeout(90_000);
    await page.setViewportSize({ width: 1280, height: 800 });
    const title = `Compact menus ${Date.now()}`;
    const project = await createProject(request, title);
    try {
        await openProject(page, title);
        const more = page.locator('#chapter-more-button');
        await expect(more).toHaveAttribute('aria-haspopup', 'true');
        await expect(more).toHaveAttribute('aria-expanded', 'false');
        await more.click();
        await expect(more).toHaveAttribute('aria-expanded', 'true');
        const items = page.getByRole('menuitem');
        await expect(items).toHaveText([
            'Обрати для файлу весь розділ з…', 'Перекласти кілька розділів…',
            'Позначити весь розділ: Перевірено', 'Зняти «Перевірено» з розділу', 'Позначити весь розділ: Вичитано', 'Зняти «Вичитано» з розділу',
        ]);
        await page.keyboard.press('Escape');
        await expect(page.locator('#chapter-more-panel')).toBeHidden();
        await expect(more).toBeFocused();

        // keyboard: ArrowDown opens and focuses the first item, ArrowDown again the second, Enter presses it
        // (the whole-chapter choice is disabled here: no paragraph has an engine variant yet)
        await expect(page.locator('#bulk-select-button')).toBeDisabled();
        await more.press('ArrowDown');
        await expect(items.nth(1)).toBeFocused();
        await page.keyboard.press('ArrowUp');
        await expect(items.nth(5)).toBeFocused(); // the first enabled item: the focus wraps to the last one
        await page.keyboard.press('ArrowDown');
        await expect(items.nth(1)).toBeFocused(); // and back to the first enabled item
        let alert = '';
        page.once('dialog', (dialog) => { alert = dialog.message(); void dialog.dismiss(); });
        await page.keyboard.press('Enter');
        await expect.poll(() => alert).toContain('лише для Claude, GPT і Gemini'); // DeepL: the queue explains itself
        await expect(page.locator('#chapter-more-panel')).toBeHidden();

        // pinned: the menu still opens next to its button and is not clipped by the pinned row
        await page.locator('.translation-row').last().scrollIntoViewIfNeeded();
        await page.mouse.wheel(0, 400);
        await expect(page.locator('#chapter-actions-row')).toHaveClass(/chapter-actions--stuck/);
        await more.click();
        const panel = (await page.locator('#chapter-more-panel').boundingBox())!;
        const button = (await more.boundingBox())!;
        expect(panel.y).toBeGreaterThanOrEqual(button.y + button.height - 1);
        expect(panel.height).toBeGreaterThan(40);
        await page.mouse.click(5, 400); // a click outside
        await expect(page.locator('#chapter-more-panel')).toBeHidden();

        // the paragraph's «⋯»
        await page.locator('.translation-row').first().scrollIntoViewIfNeeded();
        const row = page.locator('.translation-row').nth(1);
        const dots = row.locator('.para-menu-button');
        await dots.click();
        await expect(dots).toHaveAttribute('aria-expanded', 'true');
        const panelRow = row.locator('.para-menu > div');
        await expect(panelRow.getByLabel('Службовий текст')).toBeVisible();
        await expect(panelRow.getByLabel('У черзі на QA')).toBeVisible();
        await expect(panelRow.getByLabel('Оповідач з цього абзаца:')).toBeVisible();
        await panelRow.getByLabel('У черзі на QA').check();
        await page.keyboard.press('Escape');
        await expect(panelRow).toBeHidden();
        // «Перевірено» and the paragraph's translate button stay in the bar
        await expect(row.getByRole('checkbox', { name: 'Перевірено' })).toBeVisible();
        await expect(row.locator('.translate-paragraph-button')).toBeVisible();
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});

for (const [width, height] of [[1440, 900], [820, 1180], [390, 844]]) {
    test(`search / replace panel at ${width}×${height}: compact, the results and the buttons are always visible`, async ({ page, request }) => {
        test.setTimeout(90_000);
        await page.setViewportSize({ width, height });
        const title = `Compact search ${width} ${Date.now()}`;
        const project = await createProject(request, title);
        try {
            await openProject(page, title);
            await page.locator('#open-search').click();
            await page.locator('#replace-mode-toggle').click();
            await page.locator('#search-input').fill('Дрейвен');
            await expect(page.locator('#search-status')).toContainText('6 збігів');
            const panel = (await page.locator('#search-dialog .search-dialog-content').boundingBox())!;
            // the buttons are pinned at the bottom of the panel and inside the screen
            for (const id of ['#search-prev', '#search-next', '#replace-one', '#replace-all']) {
                const box = (await page.locator(id).boundingBox())!;
                expect(box.y + box.height, id).toBeLessThanOrEqual(height);
                expect(box.y, id).toBeGreaterThanOrEqual(panel.y);
                expect(box.height, id).toBeGreaterThanOrEqual(32);
            }
            // the list of matches keeps a usable height and its own scroll
            const results = (await page.locator('#search-results').boundingBox())!;
            expect(results.height).toBeGreaterThanOrEqual(120);
            expect(await page.locator('#search-results').evaluate((el) => getComputedStyle(el).overflowY)).toBe('auto');
            // segmented switches in one row each
            for (const selector of ['#search-scope-toggle', '.replace-modes']) {
                const toggle = (await page.locator(selector).boundingBox())!;
                expect(toggle.height, selector).toBeLessThanOrEqual(48);
            }
            // the panel is compact: the two switches, the checkboxes and the fields fit in the upper part
            const checks = (await page.locator('.replace-checks').boundingBox())!;
            expect(checks.y + checks.height).toBeLessThan(panel.y + panel.height - 200 + (width < 1100 ? 120 : 0));
            await expect(page.locator('.replace-modes input[value="start"]')).toBeChecked();
            await page.locator('.replace-modes .segment').nth(1).click();
            await expect(page.locator('.replace-modes input[value="word"]')).toBeChecked();
        } finally {
            await request.delete(`/api/projects/${project.projectId}`);
        }
    });
}
