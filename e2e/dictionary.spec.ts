import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Dictionary in the original column: the «📖 Словник» mode, a tap on a word, a selected phrase, Alt+click,
// «Додати в глосарій», Esc and the remembered mode. sample-without-cover.epub: the first paragraph is
// "This is a test EPUB file for testing the book cover functionality."; e2e/server.py answers dictionary
// requests with fixed JSON. Needs WORKBENCH_CREDENTIALS_KEY.

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

async function createConnection(request: APIRequestContext) {
    const response = await request.post('/api/connections', {
        data: { providerId: 'claude', displayName: 'claude dictionary e2e', credentials: { apiKey: 'claude-e2e-key' } },
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

// The cache is keyed by the model, so every test uses a model name of its own: answers cached by an
// earlier run would otherwise hide the calls (and the "Ще значення" limit would be used up).
async function useUniqueModel(request: APIRequestContext, projectId: string, connectionId: string) {
    // the senses of a word and the sense picked per sentence are not tied to a model: the tests start from an empty dictionary
    expect((await request.post('/api/e2e/reset-dictionary')).status()).toBe(204);
    const current = await (await request.get(`/api/projects/${projectId}`)).json();
    const response = await request.put(`/api/projects/${projectId}`, {
        data: { ...current, aiConfiguration: { ...(current.aiConfiguration || {}), dictionary: { connectionId, model: `e2e-dictionary-${Date.now()}-${Math.random().toString(36).slice(2, 7)}` } } },
    });
    expect(response.ok(), await response.text()).toBeTruthy();
}

// The centre of a word (or phrase) of the first original paragraph, in page coordinates.
async function pointOf(page: Page, text: string, center = true) {
    return page.evaluate(({ needle, center }) => {
        for (const original of Array.from(document.querySelectorAll('.translation-row .original-paragraph'))) {
        const walker = document.createTreeWalker(original, NodeFilter.SHOW_TEXT);
        let node: Node | null;
        while ((node = walker.nextNode())) {
            const index = (node.nodeValue || '').indexOf(needle);
            if (index >= 0) {
                if (center) (original as HTMLElement).scrollIntoView({ block: 'center' });
                const range = document.createRange();
                range.setStart(node, index);
                range.setEnd(node, index + needle.length);
                const rect = range.getBoundingClientRect();
                return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
            }
        }
        }
        throw new Error(`no ${needle}`);
    }, { needle: text, center });
}

// Opening or closing the side panel changes the width of the columns, so the text re-wraps a moment later (and
// the paragraph heights follow). A point read before that settles points at where the word used to be: wait
// until the word stops moving (the same spot after two animation frames) and only then use its centre.
async function settledPointOf(page: Page, text: string) {
    let last = await pointOf(page, text);
    await expect.poll(async () => {
        await page.evaluate(() => new Promise<void>((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve()))));
        const now = await pointOf(page, text);
        const same = Math.abs(now.x - last.x) < 0.5 && Math.abs(now.y - last.y) < 0.5;
        last = now;
        return same;
    }, { message: `the word «${text}» must stop moving before it is clicked` }).toBe(true);
    return last;
}

async function selectText(page: Page, text: string) {
    await page.evaluate((needle) => {
        for (const original of Array.from(document.querySelectorAll('.translation-row .original-paragraph'))) {
        const walker = document.createTreeWalker(original, NodeFilter.SHOW_TEXT);
        let node: Node | null;
        while ((node = walker.nextNode())) {
            const index = (node.nodeValue || '').indexOf(needle);
            if (index >= 0) {
                const selection = window.getSelection()!;
                selection.setBaseAndExtent(node, index, node, index + needle.length);
                return;
            }
        }
        }
        throw new Error(`no ${needle}`);
    }, text);
}

const sheet = (page: Page) => page.locator('#dictionary-sheet');

test('mode off: nothing opens; mode on: a tap and a selected phrase open the window; Alt+click works without the mode', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Dictionary ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    const connection = await createConnection(request);
    await useUniqueModel(request, project.projectId, connection.connectionId);
    try {
        await page.setViewportSize({ width: 1280, height: 900 });
        await openFirstChapter(page, title);
        const toggle = page.getByRole('button', { name: 'Словник' });
        await expect(toggle).toHaveAttribute('aria-pressed', 'false');
        expect((await toggle.boundingBox())!.height).toBeGreaterThanOrEqual(40);

        // off: a click and a selection change nothing
        let point = await pointOf(page, 'functionality');
        await page.mouse.click(point.x, point.y);
        await selectText(page, 'test EPUB file');
        await page.waitForTimeout(900);
        await expect(sheet(page)).toBeHidden();
        await expect(page.locator('#dictionary-mode-bar')).toBeHidden();
        await page.evaluate(() => window.getSelection()!.removeAllRanges());

        // Alt+click on a computer opens it without the mode
        await page.keyboard.down('Alt');
        await page.mouse.click(point.x, point.y);
        await page.keyboard.up('Alt');
        await expect(sheet(page)).toBeVisible();
        await expect(page.locator('#dictionary-term')).toHaveText('functionality');
        await expect(page.locator('#dictionary-body')).toContainText('значення «functionality»');
        await page.keyboard.press('Escape');
        await expect(sheet(page)).toBeHidden();
        await expect(toggle).toHaveAttribute('aria-pressed', 'false');

        // on: the bar, a tap on a word
        await toggle.click();
        await expect(toggle).toHaveAttribute('aria-pressed', 'true');
        await expect(page.locator('#dictionary-mode-bar')).toContainText('Режим словника: торкніться слова в оригіналі');
        point = await pointOf(page, 'cover');
        await page.mouse.click(point.x, point.y);
        await expect(sheet(page)).toBeVisible();
        await expect(page.locator('#dictionary-term')).toHaveText('cover');
        await expect(page.locator('#dictionary-body .dictionary-section-title')).toContainText(['Значення в цьому реченні', 'Як перекладено тут', 'Інші значення', 'Приклади']);
        await expect(page.locator('#dictionary-body')).toContainText('cover-переклад-2');
        await expect(page.locator('#dictionary-body .dictionary-badge')).toHaveText('розмовне');
        const reverso = page.locator('#dictionary-reverso');
        await expect(reverso).toHaveAttribute('href', 'https://context.reverso.net/translation/english-ukrainian/cover');
        await expect(reverso).toHaveAttribute('target', '_blank');
        await expect(reverso).toHaveAttribute('rel', 'noopener noreferrer');
        await expect(page.locator('#dictionary-wiktionary')).toHaveAttribute('href', 'https://en.wiktionary.org/wiki/cover');
        for (const name of ['Додати в глосарій', 'Копіювати', 'Ще значення']) {
            expect((await page.locator('#dictionary-actions').getByRole('button', { name }).boundingBox())!.height).toBeGreaterThanOrEqual(44);
        }

        // a tap outside closes it; the mode stays
        await page.locator('.translation-headings h4').first().click();
        await expect(sheet(page)).toBeHidden();
        await expect(toggle).toHaveAttribute('aria-pressed', 'true');

        // a selected phrase opens it after the selection is finished
        await selectText(page, 'test EPUB file');
        await expect(sheet(page)).toBeVisible();
        await expect(page.locator('#dictionary-term')).toHaveText('test EPUB file');
        await expect(page.locator('#dictionary-subtitle')).toContainText('фраза');

        // «Додати в глосарій»: source = the phrase, target from a chip
        await page.locator('#dictionary-add-glossary').click();
        await expect(page.locator('#dictionary-glossary-source')).toHaveValue('test EPUB file');
        await page.locator('#dictionary-glossary-chips').getByRole('button', { name: 'test EPUB file-переклад-1' }).click();
        await expect(page.locator('#dictionary-glossary-target')).toHaveValue('test EPUB file-переклад-1');
        await page.locator('#dictionary-glossary-save').click();
        await expect(page.locator('#dictionary-status')).toContainText('Додано в глосарій проєкту');
        await expect(page.locator('#dictionary-body')).toContainText('У глосарії');
        const stored = await (await request.get(`/api/projects/${project.projectId}`)).json();
        expect(stored.projectGlossaryEntryIds).toHaveLength(1);
        const catalog = await (await request.get('/api/glossary')).json();
        const entry = catalog.find((item: any) => item.glossaryEntryId === stored.projectGlossaryEntryIds[0]);
        expect([entry.source, entry.target]).toEqual(['test EPUB file', 'test EPUB file-переклад-1']);
        await request.delete(`/api/glossary/${entry.glossaryEntryId}`);

        // Esc: first the window, then the mode; the state is remembered across a reload
        await page.keyboard.press('Escape');
        await expect(sheet(page)).toBeHidden();
        await expect(toggle).toHaveAttribute('aria-pressed', 'true');
        await page.keyboard.press('Escape');
        await expect(toggle).toHaveAttribute('aria-pressed', 'false');
        await expect(page.locator('#dictionary-mode-bar')).toBeHidden();
        await toggle.click();
        await page.reload();
        await openFirstChapter(page, title);
        await expect(page.getByRole('button', { name: 'Словник' })).toHaveAttribute('aria-pressed', 'true');
        await expect(page.locator('#dictionary-mode-bar')).toBeVisible();
        await page.getByRole('button', { name: 'Вийти' }).click();
        await page.reload();
        await openFirstChapter(page, title);
        await expect(page.getByRole('button', { name: 'Словник' })).toHaveAttribute('aria-pressed', 'false');

        // the calls are billed as their own kind
        const usage = await (await request.get(`/api/projects/${project.projectId}/usage`)).json();
        expect(usage.byKind.map((item: any) => item.kind)).toContain('dictionary');
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
        await request.delete(`/api/connections/${connection.connectionId}`);
    }
});

test('on a tablet the window is a bottom sheet; the translation column keeps working; "Ще значення" and the cache', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Dictionary tablet ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    const connection = await createConnection(request);
    await useUniqueModel(request, project.projectId, connection.connectionId);
    try {
        await page.setViewportSize({ width: 820, height: 1100 });
        await openFirstChapter(page, title);
        await page.getByRole('button', { name: 'Словник' }).click();
        const point = await pointOf(page, 'book');
        await page.mouse.click(point.x, point.y);
        await expect(sheet(page)).toBeVisible();
        const box = (await sheet(page).boundingBox())!;
        expect(Math.round(box.y + box.height)).toBe(1100); // pinned to the bottom edge
        expect(Math.round(box.width)).toBe(820);

        await page.locator('#dictionary-more').click();
        await expect(page.locator('#dictionary-status')).toHaveText('Шукаємо інші значення…');
        await expect(page.locator('#dictionary-status')).toHaveText('');
        await expect(page.locator('#dictionary-more')).toBeEnabled();
        const afterMore = await page.locator('#dictionary-body .dictionary-list li').count();
        expect(afterMore).toBeGreaterThanOrEqual(2);
        await page.keyboard.press('Escape');

        // the translation column is not affected: typing in it works and opens nothing
        const editor = page.locator('.translation-row').first().locator('.translation-paragraph');
        await editor.click();
        await editor.pressSequentially('Моя правка');
        await expect(editor).toHaveText('Моя правка');
        await expect(sheet(page)).toBeHidden();

        // the same word again is answered from the cache: one billed call fewer than the taps
        const again = await pointOf(page, 'book');
        await page.mouse.click(again.x, again.y);
        await expect(sheet(page)).toBeVisible();
        const usage = await (await request.get(`/api/projects/${project.projectId}/usage`)).json();
        const dictionary = usage.byKind.find((item: any) => item.kind === 'dictionary');
        expect(dictionary.calls).toBe(2); // the first lookup and «Ще значення»; the repeat was free
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
        await request.delete(`/api/connections/${connection.connectionId}`);
    }
});

test('«Модель словника» in ⚙ is saved with the project; a model without a price is flagged in the window', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Dictionary model ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    const connection = await createConnection(request);
    try {
        await page.setViewportSize({ width: 1280, height: 900 });
        await openFirstChapter(page, title);
        await page.locator('#translation-settings-button').click();
        const settings = page.locator('#translation-settings-dialog');
        await expect(settings.locator('#dictionary-model-settings h3')).toHaveText('Модель словника');
        await expect(settings.locator('#dictionary-model-status')).toContainText('Моделей у списку');
        await settings.locator('#dictionary-model-manual').fill('model-without-price');
        await settings.getByRole('button', { name: 'Зберегти', exact: true }).click();
        await expect(settings).toBeHidden();
        const stored = await (await request.get(`/api/projects/${project.projectId}`)).json();
        expect(stored.aiConfiguration.dictionary).toEqual({ connectionId: connection.connectionId, model: 'model-without-price' });

        await page.getByRole('button', { name: 'Словник' }).click();
        const point = await pointOf(page, 'cover');
        await page.mouse.click(point.x, point.y);
        await expect(sheet(page)).toBeVisible();
        await expect(page.locator('#dictionary-body .dictionary-warning')).toContainText('Для моделі model-without-price не задано ціну');
        await page.getByRole('button', { name: 'Вийти' }).click();
        await expect(sheet(page)).toBeHidden(); // leaving the mode closes the window
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
        await request.delete(`/api/connections/${connection.connectionId}`);
    }
});


// --- the highlight of the word, the context line and the layout ---------------------------------

async function createLongProject(request: APIRequestContext, title: string) {
    const created = await request.post('/api/projects', { data: { title, status: 'translation' } });
    const project = await created.json();
    const epubPath = path.join(__dirname, '..', 'test-data', 'long-chapter.epub');
    const upload = await request.post('/upload', {
        headers: { 'X-Project-Id': project.projectId },
        multipart: { file: { name: 'long-chapter.epub', mimeType: 'application/epub+zip', buffer: fs.readFileSync(epubPath) } },
    });
    expect(upload.ok()).toBeTruthy();
    return project;
}

// The highlighted range (Custom Highlight API), as plain numbers.
const highlightRange = (page: Page) => page.evaluate(() => {
    const highlight = (CSS as any).highlights?.get('dictionary-term');
    if (!highlight) return null;
    const range = highlight.values().next().value as Range;
    const box = range.getBoundingClientRect();
    return { text: range.toString(), count: highlight.size, left: box.left, top: box.top, right: box.right, bottom: box.bottom };
});

test('the word stays highlighted while the window is open, the context line shows the sentence, nothing is covered', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Dictionary highlight ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    const connection = await createConnection(request);
    await useUniqueModel(request, project.projectId, connection.connectionId);
    try {
        for (const width of [1280, 1920]) {
            await page.setViewportSize({ width, height: 900 });
            await openFirstChapter(page, title);
            const toggle = page.getByRole('button', { name: 'Словник' });
            if ((await toggle.getAttribute('aria-pressed')) !== 'true') await toggle.click();
            const point = await settledPointOf(page, 'cover');
            await page.mouse.click(point.x, point.y);
            await expect(sheet(page)).toBeVisible();
            await expect(page.locator('#dictionary-body')).toContainText('значення «cover»');

            // the context line: the sentence with the word in bold
            const context = page.locator('#dictionary-context');
            await expect(context).toHaveText('У реченні: This is a test EPUB file for testing the book cover functionality.');
            await expect(context.locator('strong')).toHaveText('cover');

            // highlight: one range with the word, still there after a click in the window
            let marked = await highlightRange(page);
            expect(marked).toMatchObject({ text: 'cover', count: 1 });
            await page.locator('#dictionary-term').click();
            await page.evaluate(() => window.getSelection()!.removeAllRanges());
            marked = await highlightRange(page);
            expect(marked!.text).toBe('cover');

            // the panel is on the right, nothing is under it: the word and both columns end left of it
            const panel = (await sheet(page).boundingBox())!;
            expect(Math.round(panel.x + panel.width)).toBe(width);
            expect(marked!.right).toBeLessThanOrEqual(panel.x);
            const rows = (await page.locator('#translation-rows').boundingBox())!;
            expect(rows.x + rows.width).toBeLessThanOrEqual(panel.x + 1);
            const overlaps = !(marked!.right <= panel.x || marked!.left >= panel.x + panel.width || marked!.bottom <= panel.y || marked!.top >= panel.y + panel.height);
            expect(overlaps).toBe(false);
            expect(await page.evaluate(() => document.body.classList.contains('dictionary-panel-open'))).toBe(true);

            // the highlight does not hide the text: the paragraph text is unchanged and the mark is translucent
            expect(await page.evaluate(() => document.querySelector('.original-paragraph')!.innerHTML.includes('<mark'))).toBe(false);

            // closing removes the highlight and gives the space back
            await page.keyboard.press('Escape');
            await expect(sheet(page)).toBeHidden();
            expect(await highlightRange(page)).toBeNull();
            expect(await page.evaluate(() => document.body.classList.contains('dictionary-panel-open'))).toBe(false);
            await page.keyboard.press('Escape'); // the mode
            await expect(toggle).toHaveAttribute('aria-pressed', 'false');
        }

        // a new lookup moves the highlight
        await toggleOn(page);
        let point = await settledPointOf(page, 'cover');
        await page.mouse.click(point.x, point.y);
        await expect(page.locator('#dictionary-term')).toHaveText('cover');
        await expect(page.locator('#dictionary-body')).toContainText('значення «cover»');
        await expect(sheet(page)).toBeVisible();
        await expect.poll(() => page.evaluate(() => document.body.classList.contains('dictionary-panel-open'))).toBe(true);
        point = await settledPointOf(page, 'EPUB');
        await page.mouse.click(point.x, point.y);
        await expect(page.locator('#dictionary-term')).toHaveText('EPUB');
        expect((await highlightRange(page))!.text).toBe('EPUB');
        expect((await highlightRange(page))!.count).toBe(1);
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
        await request.delete(`/api/connections/${connection.connectionId}`);
    }
});

async function toggleOn(page: Page) {
    const toggle = page.getByRole('button', { name: 'Словник' });
    if ((await toggle.getAttribute('aria-pressed')) !== 'true') await toggle.click();
}

test('without the Custom Highlight API the word is marked by rectangles that follow the scroll', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Dictionary fallback ${Date.now()}`;
    const project = await createLongProject(request, title);
    const connection = await createConnection(request);
    await useUniqueModel(request, project.projectId, connection.connectionId);
    try {
        await page.addInitScript(() => {
            try { Object.defineProperty(CSS, 'highlights', { value: undefined, configurable: true }); } catch { /* keep the API */ }
        });
        await page.setViewportSize({ width: 1280, height: 900 });
        await openFirstChapter(page, title);
        expect(await page.evaluate(() => (CSS as any).highlights)).toBeUndefined();
        await toggleOn(page);
        const point = await pointOf(page, 'shore');
        await page.mouse.click(point.x, point.y);
        await expect(sheet(page)).toBeVisible();
        const rect = page.locator('.dictionary-highlight-rect');
        await expect(rect).toHaveCount(1);
        const wordBox = async () => page.evaluate(() => {
            const layer = document.querySelector('.dictionary-highlight-rect') as HTMLElement;
            const box = layer.getBoundingClientRect();
            return { left: box.left, top: box.top, width: box.width, height: box.height, outline: getComputedStyle(layer).outlineStyle };
        });
        const before = await wordBox();
        expect(before.outline).toBe('solid');
        // the rectangle sits on the word ...
        const wordNow = await page.evaluate(() => {
            const original = document.querySelector('.translation-row .original-paragraph')!;
            const node = original.firstChild as Text;
            const index = node.nodeValue!.indexOf('shore');
            const range = document.createRange();
            range.setStart(node, index);
            range.setEnd(node, index + 5);
            const box = range.getBoundingClientRect();
            return { left: box.left, top: box.top };
        });
        expect(Math.abs(before.left - (wordNow.left - 2))).toBeLessThan(3);
        expect(Math.abs(before.top - (wordNow.top - 1))).toBeLessThan(3);
        // ... and follows it when the page is scrolled
        await page.evaluate(() => window.scrollBy(0, 60));
        await expect.poll(async () => Math.round((await wordBox()).top)).toBe(Math.round(before.top - 60));
        await page.keyboard.press('Escape');
        await expect(rect).toHaveCount(0);
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
        await request.delete(`/api/connections/${connection.connectionId}`);
    }
});

test('«Показати в тексті» brings the paragraph between the pinned block and the bottom bar; on a tablet the word stays above the sheet', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Dictionary show ${Date.now()}`;
    const project = await createLongProject(request, title);
    const connection = await createConnection(request);
    await useUniqueModel(request, project.projectId, connection.connectionId);
    try {
        await page.setViewportSize({ width: 1280, height: 800 });
        await openFirstChapter(page, title);
        await toggleOn(page);
        const point = await pointOf(page, 'shore');
        await page.mouse.click(point.x, point.y);
        await expect(sheet(page)).toBeVisible();
        const marked = await highlightRange(page);
        // scroll far away: the sheet stays, the word is out of sight
        await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
        await expect.poll(async () => (await highlightRange(page))!.top).not.toBeCloseTo(marked!.top, 0);
        const panelBefore = await sheet(page).boundingBox();
        await page.locator('#dictionary-show').click();
        await expect.poll(async () => {
            const box = (await highlightRange(page))!;
            const top = await page.evaluate(() => parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--sticky-stack-height')) || 48);
            const chat = await page.evaluate(() => { const c = document.querySelector('#project-chat-panel') as HTMLElement | null; return c && c.offsetParent !== null ? window.innerHeight - c.getBoundingClientRect().top : 0; });
            return box.top >= top && box.bottom <= 800 - chat;
        }).toBe(true);
        // on a computer the panel stays where it was
        const panelAfter = await sheet(page).boundingBox();
        expect([panelAfter!.x, panelAfter!.width]).toEqual([panelBefore!.x, panelBefore!.width]);
        await page.keyboard.press('Escape');

        // tablet: bottom sheet of at most 42vh, the word is scrolled above it
        await page.setViewportSize({ width: 820, height: 1100 });
        await page.evaluate(() => window.scrollTo(0, 0));
        await page.evaluate(() => window.scrollBy(0, 0));
        const lower = await pointOf(page, 'shore', false);
        await page.evaluate((y) => window.scrollBy(0, y - 950), lower.y); // the word is near the bottom edge
        const near = await pointOf(page, 'shore', false);
        await page.mouse.click(near.x, near.y);
        await expect(sheet(page)).toBeVisible();
        await expect(page.locator('#dictionary-body')).toContainText('значення «shore»');
        await expect.poll(async () => {
            const box = (await highlightRange(page))!;
            const top = (await sheet(page).boundingBox())!.y;
            return box.bottom <= top + 1;
        }).toBe(true);
        expect((await sheet(page).boundingBox())!.height).toBeLessThanOrEqual(1100 * 0.42 + 1);
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
        await request.delete(`/api/connections/${connection.connectionId}`);
    }
});

// --- the neutral blocks, the translation-aware blocks and the sheet on a phone ----------------------------

async function openDictionaryWord(page: Page, word: string) {
    const point = await settledPointOf(page, word);
    await page.mouse.click(point.x, point.y);
    await expect(sheet(page)).toBeVisible();
    await expect(page.locator('#dictionary-term')).toHaveText(word);
    await expect(page.locator('#dictionary-body .dictionary-section-title').first()).toBeVisible();
}

async function setFirstTranslation(request: APIRequestContext, projectId: string, text: string) {
    const structure = await (await request.get(`/api/projects/${projectId}/book/structure`)).json();
    const paragraph = structure.chapters[0].elements.find((element: any) => element.paragraphId);
    const saved = await request.put(`/api/paragraphs/${paragraph.paragraphId}`, { data: { translationText: text, reviewed: false } });
    expect(saved.ok()).toBeTruthy();
}

test('the blocks: meaning, variants (no repeats), how it was translated; a reason and remarks only when there are some', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Dictionary blocks ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    const connection = await createConnection(request);
    await useUniqueModel(request, project.projectId, connection.connectionId);
    try {
        await setFirstTranslation(request, project.projectId, 'Це тестовий файл EPUB cover-у-перекладі.');
        await page.setViewportSize({ width: 1280, height: 900 });
        await page.addInitScript(() => localStorage.setItem('dictionary-mode', '1'));
        await openFirstChapter(page, title);
        await openDictionaryWord(page, 'cover');
        const titles = page.locator('#dictionary-body .dictionary-section-title');
        await expect(titles).toHaveText(['Значення в цьому реченні', 'Варіанти перекладу', 'Як перекладено тут', 'Інші значення', 'В інших розділах', 'Приклади']);
        await expect(page.locator('#dictionary-body .dictionary-here')).toHaveText('cover-у-перекладі');
        // no reason and no remarks: the blocks are not there
        await expect(page.getByText('Чому так')).toHaveCount(0);
        await expect(page.getByText('Зауваження', { exact: true })).toHaveCount(0);
        // a word is not shown twice in the whole sheet
        const items = await page.locator('#dictionary-body .dictionary-variants li, #dictionary-body .dictionary-other-senses li').allInnerTexts();
        const words = items.flatMap((text) => text.split(/\n|—|,/).map((part) => part.replace(/розмовне|з цієї книжки/g, '').trim())).filter(Boolean);
        expect(new Set(words.map((word) => word.toLowerCase())).size).toBe(words.length);
        await expect(page.locator('#dictionary-body .dictionary-variants .dictionary-badge')).toHaveText(['розмовне']);

        // the translation says why: the reason and the remark appear
        await page.keyboard.press('Escape');
        await setFirstTranslation(request, project.projectId, 'Це тестовий файл [[reason]] cover-у-перекладі.');
        await openFirstChapter(page, title);
        await openDictionaryWord(page, 'cover');
        await expect(page.locator('#dictionary-body')).toContainText('Каже вуличний хлопчисько: просте слово.');
        await expect(titles).toHaveText(['Значення в цьому реченні', 'Варіанти перекладу', 'Як перекладено тут', 'Чому так', 'Зауваження', 'Інші значення', 'В інших розділах', 'Приклади']);
        await expect(page.locator('#dictionary-body')).toContainText('Глосарій радить інше слово.');
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
        await request.delete(`/api/connections/${connection.connectionId}`);
    }
});

test('«Показати в інших розділах» scans without a model and uses what is stored; «Оновити значення» rebuilds the senses', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Dictionary chapters ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    const connection = await createConnection(request);
    await useUniqueModel(request, project.projectId, connection.connectionId);
    try {
        await setFirstTranslation(request, project.projectId, 'Це тестовий файл EPUB cover-у-перекладі.');
        await page.setViewportSize({ width: 1280, height: 900 });
        await page.addInitScript(() => localStorage.setItem('dictionary-mode', '1'));
        await openFirstChapter(page, title);
        await openDictionaryWord(page, 'cover');
        const callsBefore = async () => ((await (await request.get(`/api/projects/${project.projectId}/usage`)).json()).byKind.find((item: any) => item.kind === 'dictionary')?.calls ?? 0);
        await expect.poll(callsBefore).toBe(2); // the inventory and the translation check
        await page.getByRole('button', { name: 'Показати в інших розділах' }).click();
        // the rendering found for this paragraph is already stored: the scan uses it, and no model
        await expect(page.locator('.dictionary-occurrences')).toContainText('cover-у-перекладі — розд. 1');
        await expect(page.getByRole('button', { name: /Визначити решту моделлю/ })).toHaveCount(0); // nothing is left to ask about
        expect(await callsBefore()).toBe(2);

        page.once('dialog', (dialog) => { void dialog.accept(); });
        await page.getByRole('button', { name: 'Оновити значення' }).click();
        await expect(page.locator('#dictionary-status')).toHaveText('');
        await expect(page.locator('#dictionary-body .dictionary-section-title').first()).toHaveText('Значення в цьому реченні');
        await expect.poll(callsBefore).toBe(3); // the inventory made again; the translation check was kept (same translation, same sense)
        await expect(page.getByRole('button', { name: 'Показати в інших розділах' })).toBeVisible();
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
        await request.delete(`/api/connections/${connection.connectionId}`);
    }
});

test('on a phone (390 px) the heading keeps its top padding and is never run into by the paragraph, however the sheet is reopened', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Dictionary phone ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    const connection = await createConnection(request);
    await useUniqueModel(request, project.projectId, connection.connectionId);
    try {
        await setFirstTranslation(request, project.projectId, 'Це тестовий файл EPUB cover-у-перекладі.');
        await page.setViewportSize({ width: 390, height: 844 });
        await page.addInitScript(() => localStorage.setItem('dictionary-mode', '1'));
        await openFirstChapter(page, title);

        const geometry = () => page.evaluate(() => {
            const sheetBox = document.querySelector('#dictionary-sheet')!;
            const sheetRect = sheetBox.getBoundingClientRect();
            const scrollBox = document.querySelector('#dictionary-scroll')!;
            const headingRect = document.querySelector('#dictionary-term')!.getBoundingClientRect();
            const closeRect = document.querySelector('#dictionary-close')!.getBoundingClientRect();
            return { scrollTop: scrollBox.scrollTop, scrollHeight: scrollBox.scrollHeight, clientHeight: scrollBox.clientHeight,
                     headingGap: Math.round(headingRect.top - sheetRect.top), closeGap: Math.round(closeRect.top - sheetRect.top), sheetTop: sheetRect.top };
        });
        const expectHeadingInPlace = async (label: string) => {
            const g = await geometry();
            expect(g.scrollTop, `${label}: a new word starts at the top`).toBe(0);
            expect(g.headingGap, `${label}: the heading has room above it`).toBeGreaterThanOrEqual(8);
            expect(g.closeGap).toBeGreaterThanOrEqual(0);
        };

        await openDictionaryWord(page, 'cover');
        await expectHeadingInPlace('first');
        // the answer is longer than the sheet: scroll it down, and the heading stays at the top edge
        const scrolled = await page.evaluate(() => { const box = document.querySelector('#dictionary-scroll')!; box.scrollTop = box.scrollHeight; return box.scrollTop; });
        expect(scrolled).toBeGreaterThan(0);
        const stuck = await geometry();
        expect(stuck.headingGap).toBeGreaterThanOrEqual(0);
        expect(stuck.headingGap).toBeLessThan(40); // the heading did not scroll away with the answer
        // another word while the sheet is open
        await openDictionaryWord(page, 'book');
        await expectHeadingInPlace('another word');
        // close and open the same word again
        await page.evaluate(() => { const box = document.querySelector('#dictionary-scroll')!; box.scrollTop = box.scrollHeight; });
        await page.locator('#dictionary-close').click();
        await expect(sheet(page)).toBeHidden();
        await openDictionaryWord(page, 'book');
        await expectHeadingInPlace('reopened');
        // «Ще значення» keeps the reader where they are, but the heading still has its place
        await page.locator('#dictionary-more').click();
        await expect(page.locator('#dictionary-status')).toHaveText('');
        const afterMore = await geometry();
        expect(afterMore.headingGap).toBeGreaterThanOrEqual(0);
        // the sheet and its controls stay inside the screen
        const box = (await sheet(page).boundingBox())!;
        expect(box.x + box.width).toBeLessThanOrEqual(390);
        expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
        await request.delete(`/api/connections/${connection.connectionId}`);
    }
});
