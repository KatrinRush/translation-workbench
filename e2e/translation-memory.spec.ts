import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

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

async function tapWord(page: Page, word: string) {
    const point = await page.evaluate((needle) => {
        const original = document.querySelector('.translation-row .original-paragraph')!;
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
        throw new Error(`no ${needle}`);
    }, word);
    await page.mouse.click(point.x, point.y);
}

const dictionaryCalls = async (request: APIRequestContext, projectId: string) =>
    ((await (await request.get(`/api/projects/${projectId}/usage`)).json()).byKind.find((item: any) => item.kind === 'dictionary')?.calls ?? 0);

async function prepare(page: Page, request: APIRequestContext) {
    expect((await request.post('/api/e2e/reset-dictionary')).status()).toBe(204);
    await page.addInitScript(() => localStorage.setItem('dictionary-mode', '1'));
}

for (const [name, width, height] of [['desktop', 1280, 900], ['phone', 390, 844]] as const) {
    test(`with matches only the memory is shown, the model waits for «Запитати ШІ» (${name})`, async ({ page, request }) => {
        test.setTimeout(180_000);
        await page.setViewportSize({ width, height });
        const stamp = Date.now();
        const current = await createBook(request, `Memory current ${name} ${stamp}`);
        const earlier = await createBook(request, `Memory earlier ${name} ${stamp}`);
        const connection = await createConnection(request);
        try {
            await reviewParagraphs(request, earlier.paragraphs, 25);
            await prepare(page, request);
            await openFirstChapter(page, current.project.title);
            await tapWord(page, 'waves');
            const sheet = page.locator('#dictionary-sheet');
            await expect(sheet).toBeVisible();
            await expect(page.locator('.memory-block-title')).toHaveText('Як ти перекладала раніше');
            await expect(page.locator('.memory-pair')).toHaveCount(20);
            await expect(page.locator('.memory-count')).toHaveText('Показано 20 з 25');
            // only the memory and the button: the dictionary has not been asked
            await expect(page.locator('#dictionary-ask')).toBeVisible();
            // the footer of the sheet: the button stays in view under the scrolling list, nothing overlaps
            const askBox = (await page.locator('#dictionary-ask').boundingBox())!;
            const scrollBox = (await page.locator('#dictionary-scroll').boundingBox())!;
            const sheetBox = (await sheet.boundingBox())!;
            expect(askBox.y).toBeGreaterThanOrEqual(scrollBox.y + scrollBox.height - 0.5);
            expect(askBox.y + askBox.height).toBeLessThanOrEqual(sheetBox.y + sheetBox.height + 0.5);
            expect(askBox.height).toBeGreaterThanOrEqual(43.5);
            await page.locator('#dictionary-scroll').evaluate((node) => { node.scrollTop = node.scrollHeight; });
            await expect(page.locator('#dictionary-ask')).toBeInViewport();
            await page.locator('#dictionary-scroll').evaluate((node) => { node.scrollTop = 0; });
            await expect(page.locator('#dictionary-body .dictionary-section-title')).toHaveCount(0);
            await page.waitForTimeout(500);
            expect(await dictionaryCalls(request, current.project.projectId)).toBe(0);
            // the pair: book, chapter, the word marked in the original, the whole translation without a mark (the dictionary does not know it)
            const first = page.locator('.memory-pair').first();
            await expect(first.locator('.memory-where')).toContainText(`Memory earlier ${name} ${stamp}`);
            await expect(first.locator('.memory-where')).toContainText('розд. 1');
            await expect(first.locator('.memory-original .memory-mark').first()).toHaveText(/waves/i);
            await expect(first.locator('.memory-translation')).toHaveText('Хвилі й хвилі, хвиля за хвилею.');
            await expect(first.locator('.memory-translation .memory-mark')).toHaveCount(0);

            // «Показати ще»
            await page.getByRole('button', { name: 'Показати ще' }).click();
            await expect(page.locator('.memory-pair')).toHaveCount(25);
            await expect(page.locator('.memory-count')).toHaveText('Показано 25 з 25');
            await expect(page.getByRole('button', { name: 'Показати ще' })).toHaveCount(0);

            // the search field: Ukrainian, any form
            const search = page.locator('.memory-search-input');
            await search.fill('хвилею');
            await search.press('Enter');
            await expect(page.locator('.memory-pair').first().locator('.memory-translation .memory-mark').first()).toBeVisible();
            await expect(page.locator('.memory-count')).toHaveText(/Показано 20 з 25/);

            // «Додати в глосарій» opens the form with the words in it
            await page.locator('.memory-pair').first().getByRole('button', { name: 'Додати в глосарій' }).click();
            await expect(page.locator('#dictionary-glossary-form')).toBeVisible();
            await expect(page.locator('#dictionary-glossary-target')).toHaveValue('хвилею');

            // the geometry: nothing leaves the screen, the targets are at least 44 px
            const box = (await sheet.boundingBox())!;
            expect(box.x + box.width).toBeLessThanOrEqual(width + 0.5);
            expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
            for (const control of await page.locator('#dictionary-sheet .memory-search-input, #dictionary-sheet .memory-search-button, #dictionary-sheet .memory-go:visible, #dictionary-sheet .memory-add-glossary:visible').all()) {
                expect((await control.boundingBox())?.height ?? 0).toBeGreaterThanOrEqual(43.5);
            }
            if (name === 'phone') {
                // the paragraphs are cut to three lines and opened by a tap
                const pair = page.locator('.memory-pair').first();
                const text = pair.locator('.memory-original');
                expect(await text.evaluate((node) => node.scrollHeight > node.clientHeight)).toBe(true);
                await pair.getByRole('button', { name: 'Розгорнути' }).click();
                expect(await text.evaluate((node) => node.scrollHeight <= node.clientHeight + 1)).toBe(true);
                await expect(pair.getByRole('button', { name: 'Згорнути' })).toBeVisible();
            }
            await page.locator('#dictionary-glossary-cancel').click();

            // only now the model: the dictionary answers below the memory, which stays first
            await search.fill('');
            await page.locator('#dictionary-close').click();
            await tapWord(page, 'waves');
            await page.locator('#dictionary-ask').click();
            await expect(page.locator('#dictionary-body .dictionary-section-title').first()).toHaveText('Значення в цьому реченні');
            expect(await dictionaryCalls(request, current.project.projectId)).toBeGreaterThan(0);
            await expect(page.locator('#dictionary-body > section').first()).toHaveClass(/memory-block/);
            await expect(page.locator('#dictionary-ask')).toBeHidden();
            await expect(page.getByText('Перекладу цього абзацу ще немає.')).toBeVisible(); // the sheet is settled before the book is deleted
        } finally {
            await request.delete(`/api/projects/${current.project.projectId}`);
            await request.delete(`/api/projects/${earlier.project.projectId}`);
            await request.delete(`/api/connections/${connection.connectionId}`);
        }
    });

    test(`without matches the dictionary is asked at once (${name})`, async ({ page, request }) => {
        test.setTimeout(120_000);
        await page.setViewportSize({ width, height });
        const current = await createBook(request, `Memory empty ${name} ${Date.now()}`);
        const other = await createBook(request, `Memory unconfirmed ${name} ${Date.now()}`);
        const connection = await createConnection(request);
        try {
            // a translation nobody has confirmed is not in the memory
            for (const paragraph of other.paragraphs.slice(0, 3)) {
                await request.put(`/api/paragraphs/${paragraph.paragraphId}`, { data: { translationText: 'Сира хвиля.', reviewed: false } });
            }
            await prepare(page, request);
            await openFirstChapter(page, current.project.title);
            await tapWord(page, 'waves');
            await expect(page.locator('#dictionary-body .dictionary-section-title').first()).toHaveText('Значення в цьому реченні');
            await expect(page.locator('.memory-status')).toHaveText('У перевірених і вичитаних абзацах цього ще нема.');
            await expect(page.locator('.memory-pair')).toHaveCount(0);
            await expect(page.locator('#dictionary-ask')).toBeHidden();
            expect(await dictionaryCalls(request, current.project.projectId)).toBeGreaterThan(0);
            await expect(page.getByText('Перекладу цього абзацу ще немає.')).toBeVisible(); // the sheet is settled before the book is deleted
        } finally {
            await request.delete(`/api/projects/${current.project.projectId}`);
            await request.delete(`/api/projects/${other.project.projectId}`);
            await request.delete(`/api/connections/${connection.connectionId}`);
        }
    });

    test(`a glossary entry answers without the model, next to the memory (${name})`, async ({ page, request }) => {
        test.setTimeout(120_000);
        await page.setViewportSize({ width, height });
        const current = await createBook(request, `Memory glossary ${name} ${Date.now()}`);
        const earlier = await createBook(request, `Memory glossary source ${name} ${Date.now()}`);
        const connection = await createConnection(request);
        let entryId: string | null = null;
        try {
            await reviewParagraphs(request, earlier.paragraphs, 3, 'proofread');  // «Вичитано» counts like «Перевірено»
            const entry = await (await request.post('/api/glossary', { data: { source: 'waves', target: 'хвилі', note: null, active: true } })).json();
            entryId = entry.glossaryEntryId;
            expect((await request.put(`/api/projects/${current.project.projectId}`, { data: { ...current.project, projectGlossaryEntryIds: [entryId] } })).ok()).toBeTruthy();
            await prepare(page, request);
            await openFirstChapter(page, current.project.title);
            await tapWord(page, 'waves');
            await expect(page.locator('#dictionary-sheet')).toBeVisible();
            await expect(page.locator('#dictionary-body')).toContainText('waves → хвилі');
            await expect(page.locator('.memory-pair')).toHaveCount(3);
            await page.waitForTimeout(500);
            expect(await dictionaryCalls(request, current.project.projectId)).toBe(0);
            await expect(page.locator('#dictionary-body .dictionary-section-title')).toHaveText(['У глосарії']);
        } finally {
            await request.delete(`/api/projects/${current.project.projectId}`);
            await request.delete(`/api/projects/${earlier.project.projectId}`);
            await request.delete(`/api/connections/${connection.connectionId}`);
            if (entryId) await request.delete(`/api/glossary/${entryId}`);
        }
    });
}

test('«Позначити відповідник»: a word she picks becomes a known rendering and is marked in every pair', async ({ page, request }) => {
    test.setTimeout(180_000);
    await page.setViewportSize({ width: 390, height: 844 });
    const stamp = Date.now();
    const current = await createBook(request, `Memory pick here ${stamp}`);
    const earlier = await createBook(request, `Memory pick there ${stamp}`);
    const connection = await createConnection(request);
    try {
        await reviewParagraphs(request, earlier.paragraphs, 25);
        await prepare(page, request);
        await openFirstChapter(page, current.project.title);
        await tapWord(page, 'waves');
        await expect(page.locator('.memory-pair')).toHaveCount(20);
        await expect(page.locator('.memory-summary')).toHaveCount(0);
        const first = page.locator('.memory-pair').first();
        await expect(first.locator('.memory-translation .memory-mark')).toHaveCount(0);
        await first.getByRole('button', { name: 'Позначити відповідник' }).click();
        await expect(first.locator('.memory-translation .memory-pick-word').first()).toBeVisible();
        const confirm = first.getByRole('button', { name: /^Підтвердити/ });
        await expect(confirm).toBeDisabled();
        const last = first.locator('.memory-pick-word').last();
        await last.click();
        await expect(confirm).toBeEnabled();
        await expect(confirm).toHaveText('Підтвердити «хвилею»');
        expect((await confirm.boundingBox())!.height).toBeGreaterThanOrEqual(43.5);
        await last.click();  // the same word again clears the choice
        await expect(confirm).toBeDisabled();
        await last.click();
        await confirm.click();
        // every pair now has the word marked (its case forms too), and the summary counts them under one lemma
        await expect(page.locator('.memory-summary')).toContainText('хвиля — 25');
        await expect(page.locator('.memory-pair').first().locator('.memory-translation .memory-mark')).toHaveCount(4); // хвилі, хвилі, хвиля, хвилею
        await expect(page.locator('.memory-pair .memory-confirm')).toHaveCount(0);
        await page.locator('#dictionary-scroll').evaluate((node) => { node.scrollTop = node.scrollHeight; });
        await expect(page.locator('#dictionary-ask')).toBeInViewport();
    } finally {
        await request.delete(`/api/projects/${current.project.projectId}`);
        await request.delete(`/api/projects/${earlier.project.projectId}`);
        await request.delete(`/api/connections/${connection.connectionId}`);
    }
});

test('«Перейти до абзацу» opens the other book and «Назад» comes back', async ({ page, request }) => {
    test.setTimeout(120_000);
    await page.setViewportSize({ width: 390, height: 844 });
    const stamp = Date.now();
    const current = await createBook(request, `Memory here ${stamp}`);
    const earlier = await createBook(request, `Memory there ${stamp}`);
    const connection = await createConnection(request);
    try {
        await reviewParagraphs(request, earlier.paragraphs, 2);
        await prepare(page, request);
        await openFirstChapter(page, current.project.title);
        await tapWord(page, 'waves');
        await page.locator('.memory-pair').first().getByRole('button', { name: 'Перейти до абзацу' }).click();
        await expect(page.locator('#dictionary-sheet')).toBeHidden();
        await expect(page.locator('#project-page-title, .project-title').first()).toContainText(`Memory there ${stamp}`);
        const row = page.locator(`.translation-row[data-paragraph-id="${earlier.paragraphs[0].paragraphId}"]`);
        await expect(row).toBeVisible();
        const back = page.locator('#memory-return');
        await expect(back).toBeVisible();
        await expect(back).toContainText(`Memory here ${stamp}`);
        // with the sheet closed the way back is at the bottom of the screen, and while the sheet is open it is a row of its footer
        await expect(page.locator('#dictionary-footer #memory-return')).toHaveCount(0);
        await tapWord(page, 'waves');
        await expect(page.locator('#dictionary-sheet')).toBeVisible();
        await expect(page.locator('#dictionary-footer #memory-return')).toHaveCount(1);
        await expect(page.locator('#dictionary-ask')).toBeVisible();
        const sheetBox = (await page.locator('#dictionary-sheet').boundingBox())!;
        const backBox = (await back.boundingBox())!;
        const actionsBox = (await page.locator('#dictionary-actions').boundingBox())!;
        const askBox = (await page.locator('#dictionary-ask').boundingBox())!;
        expect(backBox.y + backBox.height).toBeLessThanOrEqual(actionsBox.y + 0.5);   // its own row above the actions
        expect(askBox.y + askBox.height).toBeLessThanOrEqual(backBox.y + 0.5);
        expect(backBox.x).toBeGreaterThanOrEqual(sheetBox.x - 0.5);
        expect(backBox.x + backBox.width).toBeLessThanOrEqual(sheetBox.x + sheetBox.width + 0.5);
        expect(backBox.height).toBeGreaterThanOrEqual(43.5);
        await page.locator('#dictionary-close').click();
        await expect(page.locator('#dictionary-footer #memory-return')).toHaveCount(0);
        await expect(back).toBeVisible();
        await back.click();
        await expect(back).toBeHidden();
        await expect(page.locator('#project-page-title, .project-title').first()).toContainText(`Memory here ${stamp}`);
    } finally {
        await request.delete(`/api/projects/${current.project.projectId}`);
        await request.delete(`/api/projects/${earlier.project.projectId}`);
        await request.delete(`/api/connections/${connection.connectionId}`);
    }
});
