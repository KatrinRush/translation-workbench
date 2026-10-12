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
    const current = await (await request.get(`/api/projects/${projectId}`)).json();
    const response = await request.put(`/api/projects/${projectId}`, {
        data: { ...current, aiConfiguration: { ...(current.aiConfiguration || {}), dictionary: { connectionId, model: `e2e-dictionary-${Date.now()}-${Math.random().toString(36).slice(2, 7)}` } } },
    });
    expect(response.ok(), await response.text()).toBeTruthy();
}

// The centre of a word (or phrase) of the first original paragraph, in page coordinates.
async function pointOf(page: Page, text: string) {
    return page.evaluate((needle) => {
        for (const original of Array.from(document.querySelectorAll('.translation-row .original-paragraph'))) {
        const walker = document.createTreeWalker(original, NodeFilter.SHOW_TEXT);
        let node: Node | null;
        while ((node = walker.nextNode())) {
            const index = (node.nodeValue || '').indexOf(needle);
            if (index >= 0) {
                (original as HTMLElement).scrollIntoView({ block: 'center' });
                const range = document.createRange();
                range.setStart(node, index);
                range.setEnd(node, index + needle.length);
                const rect = range.getBoundingClientRect();
                return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
            }
        }
        }
        throw new Error(`no ${needle}`);
    }, text);
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
        const toggle = page.getByRole('button', { name: '📖 Словник' });
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
        await expect(page.getByRole('button', { name: '📖 Словник' })).toHaveAttribute('aria-pressed', 'true');
        await expect(page.locator('#dictionary-mode-bar')).toBeVisible();
        await page.getByRole('button', { name: 'Вийти' }).click();
        await page.reload();
        await openFirstChapter(page, title);
        await expect(page.getByRole('button', { name: '📖 Словник' })).toHaveAttribute('aria-pressed', 'false');

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
        await page.getByRole('button', { name: '📖 Словник' }).click();
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
        await page.mouse.click(point.x, point.y);
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

        await page.getByRole('button', { name: '📖 Словник' }).click();
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
