import { expect, test, type APIRequestContext, type Locator, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// «Усі рушії»: per paragraph the original and the editor on top, panel A (default Claude) under the original and
// panel B (default Gemini) under the editor; stacked on a narrow or touch screen. e2e/server.py answers the engines
// locally: "Claude переклад", "GPT переклад", "Gemini переклад" ("Claude v2 переклад" when the project's rules
// contain [[v2]]). Needs WORKBENCH_CREDENTIALS_KEY.

async function createProjectWithBook(request: APIRequestContext, title: string) {
    const created = await request.post('/api/projects', { data: { title, status: 'translation' } });
    expect(created.ok()).toBeTruthy();
    const project = await created.json();
    const upload = await request.post('/upload', {
        headers: { 'X-Project-Id': project.projectId },
        multipart: { file: { name: 'sample-without-cover.epub', mimeType: 'application/epub+zip', buffer: fs.readFileSync(path.join(__dirname, '..', 'test-data', 'sample-without-cover.epub')) } },
    });
    expect(upload.ok()).toBeTruthy();
    return project;
}

// Connections are shared by the whole app: every one created here is deleted after the test.
const createdConnections: string[] = [];

test.afterEach(async ({ request }) => {
    while (createdConnections.length) await request.delete(`/api/connections/${createdConnections.pop()}`);
});

async function createConnection(request: APIRequestContext, providerId: string) {
    const response = await request.post('/api/connections', {
        data: { providerId, displayName: `${providerId} compare e2e`, credentials: { apiKey: `${providerId}-e2e-key` } },
    });
    expect(response.ok(), await response.text()).toBeTruthy();
    const connection = await response.json();
    createdConnections.push(connection.connectionId);
    expect((await request.post(`/api/connections/${connection.connectionId}/test`)).ok()).toBeTruthy();
    return connection;
}

async function paragraphs(request: APIRequestContext, projectId: string) {
    const structure = await (await request.get(`/api/projects/${projectId}/book/structure`)).json();
    return structure.chapters[0].elements.filter((element: any) => element.type === 'paragraph');
}

// Paragraph 1: Claude (3 versions, version 1 in the file), GPT and Gemini. Paragraph 2: Claude only.
async function prepare(request: APIRequestContext, title: string) {
    const project = await createProjectWithBook(request, title);
    const claude = await createConnection(request, 'claude');
    const openai = await createConnection(request, 'openai');
    const gemini = await createConnection(request, 'gemini');
    const [first, second] = await paragraphs(request, project.projectId);
    const translate = async (paragraphId: string, connection: any) => {
        const response = await request.post(`/api/paragraphs/${paragraphId}/translate`, { data: { connectionId: connection.connectionId } });
        expect(response.ok(), await response.text()).toBeTruthy();
    };
    await translate(first.paragraphId, claude);
    await translate(first.paragraphId, openai);
    await translate(first.paragraphId, gemini);
    for (const marker of ['[[v2]]', '[[v3]]']) {
        expect((await request.put(`/api/projects/${project.projectId}/translation-rules`, { data: { translationRules: marker } })).ok()).toBeTruthy();
        await translate(first.paragraphId, claude);
    }
    expect((await request.put(`/api/projects/${project.projectId}/translation-rules`, { data: { translationRules: '' } })).ok()).toBeTruthy();
    await translate(second.paragraphId, claude);
    return { project, first, second, connections: { claude, openai, gemini } };
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
    await expect(page.locator('.translation-row')).toHaveCount(2);
}

const toggle = (page: Page) => page.locator('#compare-engines-toggle');
const panel = (row: Locator, slot: 'a' | 'b') => row.locator(`.compare-panel[data-slot="${slot}"]`);

async function enable(page: Page) {
    if ((await toggle(page).getAttribute('aria-pressed')) !== 'true') {
        if (!(await toggle(page).isVisible())) await page.locator('#header-more-button').click(); // a phone: the switch is in the «⋯» of the top bar
        await toggle(page).click();
    }
    await expect(toggle(page)).toHaveAttribute('aria-pressed', 'true');
}

const rect = (locator: Locator) => locator.evaluate((element) => {
    const box = element.getBoundingClientRect();
    return { left: box.left, right: box.right, top: box.top, bottom: box.bottom, width: box.width, height: box.height };
});

// Selects `needle` inside the first text node of `selector` (a panel's text or the editor).
async function selectIn(locator: Locator, needle: string) {
    await locator.evaluate((element, text) => {
        const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
        let node: Node | null;
        while ((node = walker.nextNode())) {
            const index = (node.nodeValue || '').indexOf(text);
            if (index >= 0) {
                document.getSelection()!.setBaseAndExtent(node, index, node, index + text.length);
                return;
            }
        }
        throw new Error(`no ${text}`);
    }, needle);
}

test('the mode switches on and off, is remembered, replaces the tabs and the view selector', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Compare mode ${Date.now()}`;
    const { project } = await prepare(request, title);
    try {
        await page.setViewportSize({ width: 1440, height: 900 });
        await openFirstChapter(page, title);
        const row = page.locator('.translation-row').first();
        await expect(toggle(page)).toHaveText('Усі рушії');
        await expect(toggle(page)).toHaveAttribute('aria-pressed', 'false');
        await expect(page.locator('.compare-panel')).toHaveCount(0);
        await expect(row.locator('.variant-tab').first()).toBeVisible();
        await expect(page.locator('#compare-diff-toggle')).toBeHidden();

        await toggle(page).click();
        await expect(toggle(page)).toHaveAttribute('aria-pressed', 'true');
        await expect(page.locator('.compare-panel')).toHaveCount(4);
        await expect(row.locator('.variant-tab').first()).toBeHidden();      // the tabs are replaced by the panels
        await expect(page.locator('#chapter-view-select')).toBeDisabled();    // «Показувати весь розділ у варіанті» is not needed
        await expect(page.locator('#compare-diff-toggle')).toBeVisible();
        await expect(row.locator('.translation-paragraph')).toHaveText('Claude переклад');
        await expect(panel(row, 'a').locator('.compare-engine-select')).toHaveValue('claude');
        await expect(panel(row, 'b').locator('.compare-engine-select')).toHaveValue('gemini');
        expect(await page.evaluate(() => localStorage.getItem('workbench.compareEngines.mode'))).toBe('1');

        await page.reload();
        await openFirstChapter(page, title);
        await expect(toggle(page)).toHaveAttribute('aria-pressed', 'true');
        await expect(page.locator('.compare-panel')).toHaveCount(4);

        await toggle(page).click();
        await expect(page.locator('.compare-panel')).toHaveCount(0);
        await expect(row.locator('.variant-tab').first()).toBeVisible();
        await expect(page.locator('#chapter-view-select')).toBeEnabled();
        expect(await page.evaluate(() => localStorage.getItem('workbench.compareEngines.mode'))).toBe('0');
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});

for (const viewport of [{ width: 1280, height: 800 }, { width: 1440, height: 900 }, { width: 1920, height: 1080 }]) {
    test(`2×2 grid at ${viewport.width}×${viewport.height}: A under the original, B under the editor, equal heights`, async ({ page, request }) => {
        test.setTimeout(120_000);
        const title = `Compare grid ${viewport.width} ${Date.now()}`;
        const { project } = await prepare(request, title);
        try {
            await page.setViewportSize(viewport);
            await openFirstChapter(page, title);
            await enable(page);
            const row = page.locator('.translation-row').first();
            await expect(panel(row, 'a').locator('.compare-panel-text')).toBeVisible();
            await expect(panel(row, 'b').locator('.compare-panel-text')).toBeVisible();
            const original = await rect(row.locator('.original-paragraph'));
            const control = await rect(row.locator('.translation-control'));
            const a = await rect(panel(row, 'a'));
            const b = await rect(panel(row, 'b'));
            expect(Math.abs(original.top - control.top)).toBeLessThanOrEqual(2);           // original | editor on top
            expect(original.left).toBeLessThan(control.left);
            expect(Math.abs(a.left - original.left)).toBeLessThanOrEqual(2);               // A under the original
            expect(Math.abs(b.left - control.left)).toBeLessThanOrEqual(2);                // B under the editor
            expect(a.top).toBeGreaterThanOrEqual(Math.max(original.bottom, control.bottom) - 1);
            expect(Math.abs(a.top - b.top)).toBeLessThanOrEqual(1);
            expect(Math.abs(a.height - b.height)).toBeLessThanOrEqual(1);                  // the panels of one row are equally tall
            expect(a.right).toBeLessThanOrEqual(b.left + 1);                               // nothing overlaps
            expect(b.right).toBeLessThanOrEqual(viewport.width);
            // the service bar stays under the editor
            expect((await rect(row.locator('.para-bar'))).top).toBeGreaterThanOrEqual((await rect(row.locator('.translation-paragraph'))).bottom - 1);
        } finally {
            await request.delete(`/api/projects/${project.projectId}`);
        }
    });
}

for (const viewport of [{ width: 1024, height: 768 }, { width: 820, height: 1180 }, { width: 390, height: 844 }]) {
    test.describe(`Stack at ${viewport.width}×${viewport.height} (touch)`, () => {
        test.use({ viewport, hasTouch: true, isMobile: true });

        test('original, editor with its service bar, panel A, panel B; buttons ≥ 44 px', async ({ page, request }) => {
            test.setTimeout(120_000);
            const title = `Compare stack ${viewport.width} ${Date.now()}`;
            const { project } = await prepare(request, title);
            try {
                await openFirstChapter(page, title);
                await enable(page);
                const row = page.locator('.translation-row').first();
                await expect(panel(row, 'a').locator('.compare-panel-text')).toBeVisible();
                const original = await rect(row.locator('.original-paragraph'));
                const control = await rect(row.locator('.translation-control'));
                const bar = await rect(row.locator('.para-bar'));
                const a = await rect(panel(row, 'a'));
                const b = await rect(panel(row, 'b'));
                expect(original.bottom).toBeLessThanOrEqual(control.top + 1);
                expect(bar.bottom).toBeLessThanOrEqual(a.top + 1);          // the service bar is right under the editor, before A
                expect(control.bottom).toBeLessThanOrEqual(a.top + 1);
                expect(a.bottom).toBeLessThanOrEqual(b.top + 1);
                expect(Math.abs(a.left - b.left)).toBeLessThanOrEqual(1);
                expect(Math.abs(a.left - original.left)).toBeLessThanOrEqual(2);
                const rowBox = await rect(row);
                expect(b.right).toBeLessThanOrEqual(rowBox.right + 1);       // the panels stay inside the row
                expect(a.left).toBeGreaterThanOrEqual(rowBox.left - 1);
                for (const target of [
                    panel(row, 'a').locator('.compare-engine-select'), panel(row, 'a').locator('.compare-to-file'),
                    panel(row, 'a').locator('.compare-copy'), panel(row, 'a').locator('.compare-expand'),
                    panel(row, 'a').locator('.compare-step').first(), panel(row, 'b').locator('.compare-copy'),
                ]) {
                    const box = (await target.boundingBox())!;
                    expect(box.height).toBeGreaterThanOrEqual(43.5);
                }
            } finally {
                await request.delete(`/api/projects/${project.projectId}`);
            }
        });
    });
}

test('panel engine and version: choice is remembered, ‹ n/m › steps, «У файл» and the in-file mark', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Compare panels ${Date.now()}`;
    const { project, first } = await prepare(request, title);
    try {
        await page.setViewportSize({ width: 1440, height: 900 });
        await openFirstChapter(page, title);
        await enable(page);
        const row = page.locator('.translation-row').first();
        const a = panel(row, 'a');
        const b = panel(row, 'b');

        // A = Claude with three versions; version 1 is in the file
        await expect(a.locator('.compare-panel-text')).toHaveText('Claude переклад');
        await expect(a.locator('.compare-version-counter')).toHaveText('1/3');
        await expect(a.locator('.compare-in-file')).toHaveText('✓ у файлі');
        await expect(a.locator('.compare-meta')).toContainText(/Claude · .+ · інструкції —/);
        await a.locator('.compare-step').last().click();
        await expect(a.locator('.compare-version-counter')).toHaveText('2/3');
        await expect(a.locator('.compare-panel-text')).toHaveText('Claude v2 переклад');
        await expect(a.locator('.compare-in-file')).toHaveText('≠ не у файлі');
        await a.locator('.compare-step').last().click();
        await expect(a.locator('.compare-panel-text')).toHaveText('Claude v3 переклад');

        // B = Gemini: one version, not in the file; the engine of a panel can be changed and is remembered
        await expect(b.locator('.compare-panel-text')).toHaveText('Gemini переклад');
        await expect(b.locator('.compare-version-counter')).toHaveCount(0);
        await b.locator('.compare-engine-select').selectOption('openai');
        await expect(b.locator('.compare-panel-text')).toHaveText('GPT переклад');
        await expect(b.locator('.compare-meta')).toContainText('GPT');
        expect(await page.evaluate(() => JSON.parse(localStorage.getItem('workbench.compareEngines.engines')!))).toEqual({ a: 'claude', b: 'openai' });
        await page.reload();
        await openFirstChapter(page, title);
        await enable(page);
        await expect(panel(page.locator('.translation-row').first(), 'b').locator('.compare-engine-select')).toHaveValue('openai');
        await expect(panel(page.locator('.translation-row').first(), 'b').locator('.compare-panel-text')).toHaveText('GPT переклад');

        // «У файл» on panel B: the file takes the text, the editor shows it, the mark turns ✓; undo restores
        const row1 = page.locator('.translation-row').first();
        const b1 = panel(row1, 'b');
        await b1.locator('.compare-to-file').click();
        await expect(b1.locator('.compare-in-file')).toHaveText('✓ у файлі');
        await expect(row1.locator('.translation-paragraph')).toHaveText('GPT переклад');
        await expect.poll(async () => (await paragraphs(request, project.projectId))[0].translationText).toBe('GPT переклад');
        await page.locator('#undo-translation').click();
        await expect(row1.locator('.translation-paragraph')).toHaveText('Claude переклад');
        expect(first.paragraphId).toBeTruthy();
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});

test('«→ Вручну»: a selected fragment goes to the cursor, replaces the editor selection, or is appended; undo works', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Compare insert ${Date.now()}`;
    const { project } = await prepare(request, title);
    try {
        await page.setViewportSize({ width: 1440, height: 900 });
        await openFirstChapter(page, title);
        await enable(page);
        const row = page.locator('.translation-row').first();
        const editor = row.locator('.translation-paragraph');
        const bText = panel(row, 'b').locator('.compare-panel-text');
        const button = page.locator('.compare-selection-button');
        await expect(bText).toHaveText('Gemini переклад');
        await expect(button).toBeHidden();

        // no cursor was ever placed in the editor: appended at the end after a space
        await selectIn(bText, 'Gemini');
        await expect(button).toBeVisible();
        await expect(button).toHaveText('→ Вручну');
        expect((await button.boundingBox())!.height).toBeGreaterThanOrEqual(39);
        await button.click();
        await expect(editor).toHaveText('Claude переклад Gemini');
        await expect(button).toBeHidden();

        // a cursor in the editor: inserted at the cursor (the caret was after «Claude»)
        await selectIn(editor, 'Claude');
        await editor.evaluate((element) => {
            const selection = document.getSelection()!;
            selection.collapseToEnd();
            element.dispatchEvent(new Event('focus'));
        });
        await selectIn(bText, 'переклад');
        await button.click();
        await expect(editor).toHaveText('Claudeпереклад переклад Gemini');

        // a selection in the editor is replaced
        await selectIn(editor, 'Gemini');
        await selectIn(bText, 'Gemini');
        await button.click();
        await expect(editor).toHaveText('Claudeпереклад переклад Gemini');
        await selectIn(editor, 'переклад Gemini');
        await selectIn(bText, 'переклад');
        await button.click();
        await expect(editor).toHaveText('Claudeпереклад переклад');

        // it is an ordinary edit: the paragraph is unsaved, undo steps back, saving makes a «Вручну» version
        await expect(page.locator('#save-translation')).toBeEnabled();
        await page.locator('#undo-translation').click();
        await expect(editor).not.toHaveText('Claudeпереклад переклад');
        await page.locator('#redo-translation').click();
        await expect(editor).toHaveText('Claudeпереклад переклад');
        await page.locator('#save-translation').click();
        await expect.poll(async () => {
            const variants = (await paragraphs(request, project.projectId))[0].translationVariants;
            return variants.find((variant: any) => variant.engine === 'manual')?.text;
        }).toBe('Claudeпереклад переклад');
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});

test('«Копіювати все у Вручну» replaces the editor text as an edit and undo brings it back', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Compare copy ${Date.now()}`;
    const { project } = await prepare(request, title);
    try {
        await page.setViewportSize({ width: 1440, height: 900 });
        await openFirstChapter(page, title);
        await enable(page);
        const row = page.locator('.translation-row').first();
        const editor = row.locator('.translation-paragraph');
        await expect(editor).toHaveText('Claude переклад');
        await panel(row, 'b').locator('.compare-copy').click();
        await expect(editor).toHaveText('Gemini переклад');
        await expect(page.locator('#save-translation')).toBeEnabled();
        await page.locator('#undo-translation').click();
        await expect(editor).toHaveText('Claude переклад');
        await page.locator('#redo-translation').click();
        await page.locator('#save-translation').click();
        await expect.poll(async () => {
            const paragraph = (await paragraphs(request, project.projectId))[0];
            return [paragraph.translationText, paragraph.translationVariants.some((variant: any) => variant.engine === 'manual' && variant.text === 'Gemini переклад')];
        }).toEqual(['Gemini переклад', true]);
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});

test('no translation: «немає перекладу» and «Перекласти {рушій}» in the panel', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Compare empty ${Date.now()}`;
    const { project } = await prepare(request, title);
    try {
        await page.setViewportSize({ width: 1440, height: 900 });
        await openFirstChapter(page, title);
        await enable(page);
        const second = page.locator('.translation-row').nth(1);
        const b = panel(second, 'b');                                   // Gemini has nothing for paragraph 2
        await expect(b.locator('.compare-empty')).toContainText('немає перекладу');
        const translate = b.getByRole('button', { name: 'Перекласти Gemini' });
        await expect(translate).toBeVisible();
        await translate.click();
        await expect(b.locator('.compare-panel-text')).toHaveText('Gemini переклад');
        await expect(b.locator('.compare-empty')).toHaveCount(0);
        // the editor keeps the text for the file (Claude's, chosen first)
        await expect(second.locator('.translation-paragraph')).toHaveText('Claude переклад');
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});

test('long paragraphs scroll inside a panel (≤ 40vh) and «⤢» expands it', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Compare long ${Date.now()}`;
    const { project, first } = await prepare(request, title);
    try {
        const long = Array.from({ length: 120 }, (_, index) => `рядок ${index + 1} з довгого абзацу`).join(' ');
        expect((await request.put(`/api/paragraphs/${first.paragraphId}`, { data: { translationText: long, reviewed: false } })).ok()).toBeTruthy();
        await page.setViewportSize({ width: 1440, height: 900 });
        await openFirstChapter(page, title);
        await enable(page);
        const row = page.locator('.translation-row').first();
        const a = panel(row, 'a');
        await a.locator('.compare-engine-select').selectOption('manual');
        const text = a.locator('.compare-panel-text');
        await expect(text).toContainText('рядок 1 з довгого абзацу');
        const limited = await text.evaluate((element) => ({ height: element.getBoundingClientRect().height, scroll: element.scrollHeight, window: window.innerHeight }));
        expect(limited.height).toBeLessThanOrEqual(limited.window * 0.4 + 2);
        expect(limited.scroll).toBeGreaterThan(limited.height);
        await a.locator('.compare-expand').click();
        const expanded = await a.locator('.compare-panel-text').evaluate((element) => element.getBoundingClientRect().height);
        expect(expanded).toBeGreaterThan(limited.height);
        await expect(a.locator('.compare-expand')).toHaveAttribute('aria-pressed', 'true');
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});

test('«Підсвітити відмінності» marks the words that differ; search matches are highlighted in the panels too', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Compare diff ${Date.now()}`;
    const { project } = await prepare(request, title);
    try {
        await page.setViewportSize({ width: 1440, height: 900 });
        await openFirstChapter(page, title);
        await enable(page);
        const row = page.locator('.translation-row').first();
        await expect(panel(row, 'b').locator('.compare-panel-text')).toHaveText('Gemini переклад');
        const diff = () => page.evaluate(() => {
            const highlight = (CSS as any).highlights?.get('compare-diff');
            return highlight ? Array.from(highlight.values()).map((range: any) => range.toString()).sort() : null;
        });
        expect(await diff()).toBeNull();                                      // off by default
        await page.locator('#compare-diff-toggle').click();
        await expect(page.locator('#compare-diff-toggle')).toHaveAttribute('aria-pressed', 'true');
        // editor «Claude переклад», A «Claude переклад», B «Gemini переклад»: only the first word of B and the editor/A pair with it differ
        await expect.poll(diff).toContain('Gemini');
        const marked = (await diff())!;
        expect(marked.filter((word) => word === 'Gemini')).toHaveLength(1);
        expect(marked).toContain('Claude');
        expect(marked).not.toContain('переклад');
        await page.locator('#compare-diff-toggle').click();
        expect(await diff()).toBeNull();

        // search: the matches are marked in the editor and in the panels
        await page.locator('#open-search').click();
        await page.locator('#search-input').fill('переклад');
        await expect.poll(() => page.evaluate(() => {
            const highlight = (CSS as any).highlights?.get('search-all');
            if (!highlight) return 0;
            return Array.from(highlight.values()).filter((range: any) => (range.startContainer.parentElement as Element)?.closest('.compare-panel-text')).length;
        })).toBeGreaterThanOrEqual(2);
        const inEditor = await page.evaluate(() => {
            const highlight = (CSS as any).highlights?.get('search-all');
            return Array.from(highlight.values()).filter((range: any) => (range.startContainer.parentElement as Element)?.closest('.translation-paragraph')).length;
        });
        expect(inEditor).toBeGreaterThanOrEqual(1);
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});
