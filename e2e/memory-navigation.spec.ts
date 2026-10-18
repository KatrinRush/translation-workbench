import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Going from the translation memory to a paragraph and back; the collapsed dictionary strip. (Helpers as in translation-memory.spec.ts.)
// Translation memory in the dictionary sheet: a tap searches the reviewed / proofread paragraphs of all books first (no model);
// with a match only the memory and «Запитати ШІ» are shown, with none the dictionary is asked at once, a glossary entry answers
// by itself. long-chapter.epub has 91 paragraphs, most of them with «waves». Needs WORKBENCH_CREDENTIALS_KEY.

async function createBook(request: APIRequestContext, title: string) {
    const project = await (await request.post('/api/projects', { data: { title, status: 'translation' } })).json();
    const upload = await request.post('/upload', {
        headers: { 'X-Project-Id': project.projectId },
        multipart: { file: { name: 'long-chapter.epub', mimeType: 'application/epub+zip', buffer: fs.readFileSync(path.join(__dirname, '..', 'test-data', 'long-chapter.epub')) } },
    });
    expect(upload.ok()).toBeTruthy();
    const structure = await (await request.get(`/api/projects/${project.projectId}/book/structure`)).json();
    const paragraphs = structure.chapters[0].elements.filter((element: any) => element.paragraphId && /waves/.test(element.originalText));
    return { project, paragraphs, chapterId: structure.chapters[0].chapterId };
}

async function reviewParagraphs(request: APIRequestContext, paragraphs: any[], count: number, flag: 'reviewed' | 'proofread' = 'reviewed') {
    for (const paragraph of paragraphs.slice(0, count)) {
        const saved = await request.put(`/api/paragraphs/${paragraph.paragraphId}`, {
            data: { translationText: 'Хвилі й хвилі, хвиля за хвилею.', reviewed: flag === 'reviewed', proofread: flag === 'proofread' },
        });
        expect(saved.ok()).toBeTruthy();
    }
}

async function createConnection(request: APIRequestContext) {
    const response = await request.post('/api/connections', { data: { providerId: 'claude', displayName: 'claude memory e2e', credentials: { apiKey: 'claude-e2e-key' } } });
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


async function tapWordInRow(page: Page, rowIndex: number, word: string) {
    const point = await page.evaluate(({ index, needle }) => {
        const row = document.querySelectorAll('.translation-row')[index] as HTMLElement;
        const original = row.querySelector('.original-paragraph')!;
        row.scrollIntoView({ block: 'center' });
        const walker = document.createTreeWalker(original, NodeFilter.SHOW_TEXT);
        let node: Node | null;
        while ((node = walker.nextNode())) {
            const at = (node.nodeValue || '').indexOf(needle);
            if (at >= 0) {
                const range = document.createRange();
                range.setStart(node, at);
                range.setEnd(node, at + needle.length);
                const rect = range.getBoundingClientRect();
                return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
            }
        }
        throw new Error(`no ${needle}`);
    }, { index: rowIndex, needle: word });
    await page.waitForTimeout(300);  // the scroll settles
    const settled = await page.evaluate(({ index, needle }) => {
        const original = document.querySelectorAll('.translation-row')[index].querySelector('.original-paragraph')!;
        const walker = document.createTreeWalker(original, NodeFilter.SHOW_TEXT);
        let node: Node | null;
        while ((node = walker.nextNode())) {
            const at = (node.nodeValue || '').indexOf(needle);
            if (at >= 0) {
                const range = document.createRange();
                range.setStart(node, at);
                range.setEnd(node, at + needle.length);
                const rect = range.getBoundingClientRect();
                return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
            }
        }
        return point;
    }, { index: rowIndex, needle: word });
    await page.mouse.click(settled.x, settled.y);
}

const rowBox = (page: Page, paragraphId: string) =>
    page.evaluate((id) => {
        const rect = document.querySelector(`.translation-row[data-paragraph-id="${id}"]`)!.getBoundingClientRect();
        return { top: rect.top, bottom: rect.bottom };
    }, paragraphId);

const highlightedText = (page: Page) =>
    page.evaluate(() => {
        const highlight = (CSS as any).highlights?.get('dictionary-term');
        if (!highlight) return null;
        const range = [...highlight][0] as Range | undefined;
        return range ? range.toString() : null;
    });

async function prepare(page: Page, request: APIRequestContext) {
    expect((await request.post('/api/e2e/reset-dictionary')).status()).toBe(204);
    await page.addInitScript(() => localStorage.setItem('dictionary-mode', '1'));
}

for (const [name, width, height] of [['phone', 390, 844], ['tablet', 820, 1100], ['desktop', 1280, 900]] as const) {
    test(`the way to a paragraph of the memory and back, and the collapsed dictionary (${name})`, async ({ page, request }) => {
        test.setTimeout(240_000);
        await page.setViewportSize({ width, height });
        const stamp = Date.now();
        const current = await createBook(request, `Nav here ${name} ${stamp}`);
        const earlier = await createBook(request, `Nav there ${name} ${stamp}`);
        const connection = await createConnection(request);
        try {
            await reviewParagraphs(request, earlier.paragraphs, 25);
            await prepare(page, request);
            await openFirstChapter(page, current.project.title);
            const originId = current.paragraphs[40].paragraphId;
            const originIndex = await page.evaluate((id) => [...document.querySelectorAll('.translation-row')].findIndex((row) => (row as HTMLElement).dataset.paragraphId === id), originId);
            await tapWordInRow(page, originIndex, 'waves');
            await expect(page.locator('.memory-pair')).toHaveCount(20);
            const before = await rowBox(page, originId);

            // the sheet collapses with its button, the strip shows the word, a tap brings the sheet back as it was
            await page.locator('#dictionary-scroll').evaluate((node) => { node.scrollTop = 400; });
            const scrolled = await page.locator('#dictionary-scroll').evaluate((node) => node.scrollTop);
            expect(scrolled).toBeGreaterThan(0);
            await page.locator('#dictionary-collapse').click();
            await expect(page.locator('#dictionary-sheet')).toBeHidden();
            const strip = page.locator('#dictionary-strip');
            await expect(strip).toBeVisible();
            await expect(strip).toContainText('waves');
            await expect(strip.locator('.dictionary-strip-chevron')).toBeVisible();
            await strip.locator('#dictionary-strip-open').click();
            await expect(page.locator('#dictionary-sheet')).toBeVisible();
            await expect(strip).toBeHidden();
            expect(Math.abs((await page.locator('#dictionary-scroll').evaluate((node) => node.scrollTop)) - scrolled)).toBeLessThanOrEqual(1);
            await expect(page.locator('.memory-pair')).toHaveCount(20);

            // «Перейти до абзацу» of a pair far down the chapter: exactly that paragraph, the word marked, the strip instead of the sheet
            const pair = page.locator('.memory-pair').nth(19);
            await pair.scrollIntoViewIfNeeded();
            const targetId = earlier.paragraphs[19].paragraphId;
            await pair.getByRole('button', { name: 'Перейти до абзацу' }).click();
            await expect(page.locator('#dictionary-sheet')).toBeHidden();
            await expect(strip).toBeVisible();
            await expect(page.locator(`.translation-row[data-paragraph-id="${targetId}"]`)).toBeVisible();
            await expect.poll(() => highlightedText(page), { timeout: 8000 }).toBe('waves');
            const placed = async () => {
                const box = await rowBox(page, targetId);
                const stripTop = (await strip.boundingBox())!.y;
                return { ...box, stripTop };
            };
            await expect.poll(async () => { const p = await placed(); return p.top >= 40 && p.bottom <= p.stripTop; }, { timeout: 8000 }).toBe(true);
            const first = await placed();
            await page.waitForTimeout(1200);  // nothing slides afterwards
            const second = await placed();
            expect(Math.abs(second.top - first.top)).toBeLessThanOrEqual(1.5);
            // the strip covers nothing: the end of the page stays above it, and the strip is not wider than the screen
            await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight));
            await page.waitForTimeout(200);
            const lastRow = await page.evaluate(() => { const rows = document.querySelectorAll('.translation-row'); return rows[rows.length - 1].getBoundingClientRect().bottom; });
            expect(lastRow).toBeLessThanOrEqual((await strip.boundingBox())!.y + 1);
            const stripBox = (await strip.boundingBox())!;
            expect(stripBox.x).toBeGreaterThanOrEqual(-0.5);
            expect(stripBox.x + stripBox.width).toBeLessThanOrEqual(width + 0.5);
            expect((await strip.locator('#dictionary-strip-open').boundingBox())!.height).toBeGreaterThanOrEqual(43.5);
            await expect(page.locator('#memory-return')).toBeVisible();
            expect((await page.locator('#memory-return').boundingBox())!.y).toBeLessThan(stripBox.y + stripBox.height);

            // another sheet (the chat) hides the strip, closing it brings the strip back
            await page.locator('#project-chat-toggle').click();
            await expect(strip).toBeHidden();
            await page.locator('#project-chat-toggle').click();
            await expect(strip).toBeVisible();

            // «Назад»: the paragraph the word was tapped in, at the same place of the screen
            await page.locator('#memory-return').click();
            await expect(page.locator('#memory-return')).toBeHidden();
            await expect(page.locator('#project-page-title')).toContainText(`Nav here ${name} ${stamp}`);
            await expect.poll(async () => Math.abs((await rowBox(page, originId)).top - before.top), { timeout: 8000 }).toBeLessThanOrEqual(2);
            await page.waitForTimeout(1200);
            expect(Math.abs((await rowBox(page, originId)).top - before.top)).toBeLessThanOrEqual(2);

            // the strip is still there; expanding shows the same word and list, ✕ closes everything
            await expect(strip).toBeVisible();
            await strip.locator('#dictionary-strip-open').click();
            await expect(page.locator('#dictionary-term')).toHaveText('waves');
            await expect(page.locator('.memory-pair')).toHaveCount(20);
            await page.locator('#dictionary-close').click();
            await expect(page.locator('#dictionary-sheet')).toBeHidden();
            await expect(strip).toBeHidden();
        } finally {
            await request.delete(`/api/projects/${current.project.projectId}`);
            await request.delete(`/api/projects/${earlier.project.projectId}`);
            await request.delete(`/api/connections/${connection.connectionId}`);
        }
    });
}
