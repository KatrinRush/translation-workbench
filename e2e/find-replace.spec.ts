import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// «Знайти й замінити» in the search dialog (🔍): Cyrillic query only, translation text only, match modes,
// the confirmation with examples, one undo/redo step per action. long-chapter.epub has 12 chapters.

const P1 = '<b>Дрейвен</b> прийшов. Дрейвена бачили, Дрейвенський не чіпати.';
const P2 = 'Лише Дрейвеном і дрейвен.';
const Q1 = 'Дрейвену сказали.';

async function createProject(request: APIRequestContext, title: string) {
    const created = await request.post('/api/projects', { data: { title, status: 'translation' } });
    const project = await created.json();
    const upload = await request.post('/upload', {
        headers: { 'X-Project-Id': project.projectId },
        multipart: { file: { name: 'long-chapter.epub', mimeType: 'application/epub+zip', buffer: fs.readFileSync(path.join(__dirname, '..', 'test-data', 'long-chapter.epub')) } },
    });
    expect(upload.ok()).toBeTruthy();
    const structure = await (await request.get(`/api/projects/${project.projectId}/book/structure`)).json();
    const put = async (id: string, text: string, reviewed: boolean) =>
        expect((await request.put(`/api/paragraphs/${id}`, { data: { translationText: text, reviewed } })).ok()).toBeTruthy();
    const [first, second] = structure.chapters;
    const ids = (chapter: any) => chapter.elements.filter((e: any) => e.type === 'paragraph' && e.paragraphId).map((e: any) => e.paragraphId);
    await put(ids(first)[0], P1, false);
    await put(ids(first)[1], P2, true);
    await put(ids(second)[0], Q1, false);
    return { project, first: ids(first), second: ids(second) };
}

async function textOf(request: APIRequestContext, projectId: string, paragraphId: string) {
    const structure = await (await request.get(`/api/projects/${projectId}/book/structure`)).json();
    for (const chapter of structure.chapters) {
        for (const element of chapter.elements) {
            if (element.paragraphId === paragraphId) return [element.translationText, element.reviewed];
        }
    }
    throw new Error('no paragraph');
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

// «N збігів» before a match is chosen, «збіг k з N» after
const total = (n: number) => new RegExp(`(^| )${n} (збіг|збіги|збігів) ·|з ${n} ·`);

const highlighted = (page: Page) => page.evaluate(() => {
    const highlight = (CSS as any).highlights?.get('search-current');
    return highlight ? Array.from(highlight.values()).map((range: any) => range.toString()) : null;
});

test('replace one match at a time and everywhere: modes, case forms, confirmation, undo and redo', async ({ page, request }) => {
    test.setTimeout(150_000);
    const title = `Replace ${Date.now()}`;
    const { project, first, second } = await createProject(request, title);
    try {
        await page.setViewportSize({ width: 1440, height: 900 });
        await openFirstChapter(page, title);
        await page.locator('#open-search').click();
        const dialog = page.locator('#search-dialog');
        await expect(dialog).toBeVisible();
        await dialog.getByRole('button', { name: 'Знайти й замінити' }).click();
        const status = page.locator('#search-status');
        const search = page.locator('#search-input');

        // a Latin query: the replace field is off, with an explanation
        await search.fill('Dreyven');
        await expect(page.locator('#replace-note')).toContainText('введіть запит кирилицею');
        await expect(page.locator('#replace-input')).toBeDisabled();
        await expect(page.locator('#replace-one')).toBeDisabled();

        // «Початок слова» is the default: case forms, not «Дрейвенський»; the chapter scope first
        await search.fill('Дрейвен');
        await expect(status).toHaveText(total(4));
        await expect(page.locator('#replace-input')).toBeEnabled();
        await expect(page.locator('input[name="replace-mode"][value="start"]')).toBeChecked();
        const items = page.locator('#search-results .search-result-item');
        await expect(items).toHaveCount(4);
        await expect(items.nth(1)).toContainText('Дрейвена');
        await page.locator('input[name="replace-mode"][value="word"]').check();
        await expect(status).toHaveText(total(2)); // Дрейвен, дрейвен
        await page.locator('input[name="replace-mode"][value="any"]').check();
        await expect(status).toHaveText(total(5)); // + Дрейвенський
        await page.locator('#replace-match-case').check();
        await expect(status).toHaveText(total(4)); // lower-case «дрейвен» no longer matches «Дрейвен…»
        await page.locator('#replace-match-case').uncheck();
        await page.locator('input[name="replace-mode"][value="start"]').check();
        await expect(status).toHaveText(total(4));

        // the dialog stays open (docked) and the match is highlighted in the text
        await page.locator('#replace-input').fill('Дравен');
        await items.first().click();
        await expect(dialog).toBeVisible();
        await expect(status).toContainText('збіг 1 з 4');
        await expect.poll(() => highlighted(page)).toEqual(['Дрейвен']);
        const panel = (await dialog.locator('.search-dialog-content').boundingBox())!;
        const rows = (await page.locator('#translation-rows').boundingBox())!;
        expect(rows.x + rows.width).toBeLessThanOrEqual(panel.x + 1); // nothing is under the panel

        // «Замінити»: one match, then the next one is current
        await page.locator('#replace-one').click();
        await expect(status).toContainText('збіг 1 з 3');
        expect(await textOf(request, project.projectId, first[0])).toEqual(['<b>Дравен</b> прийшов. Дрейвена бачили, Дрейвенський не чіпати.', false]);
        await expect.poll(() => highlighted(page)).toEqual(['Дрейвена']);
        // undo is one step
        await page.locator('#undo-translation').click();
        await expect.poll(async () => (await textOf(request, project.projectId, first[0]))[0]).toBe(P1);
        await expect(page.locator('.translation-row').first().locator('.translation-paragraph')).toContainText('Дрейвен прийшов');
        await page.locator('#redo-translation').click();
        await expect.poll(async () => (await textOf(request, project.projectId, first[0]))[0]).toContain('<b>Дравен</b>');
        await page.locator('#undo-translation').click();
        await expect.poll(async () => (await textOf(request, project.projectId, first[0]))[0]).toBe(P1);

        // «Замінити все» in the project: a confirmation with the counts and examples first
        await dialog.locator('[data-scope="project"]').click();
        await expect(status).toHaveText(total(5));
        await expect(status).toContainText('розділів: 2');
        await page.locator('#replace-all').click();
        const confirm = page.locator('#replace-confirm');
        await expect(confirm).toBeVisible();
        await expect(page.locator('#replace-confirm-title')).toHaveText('Замінити 5 збігів у 2 розділах?');
        await expect(page.locator('#replace-confirm-details')).toContainText('перевірених: 1');
        await expect(page.locator('#replace-confirm-examples li')).toHaveCount(5);
        await expect(page.locator('#replace-confirm-examples li').first()).toContainText('було:');
        await expect(page.locator('#replace-confirm-examples li').first()).toContainText('стане:');
        await page.locator('#replace-confirm-no').click();
        await expect(confirm).toBeHidden();
        expect((await textOf(request, project.projectId, first[0]))[0]).toBe(P1);

        await page.locator('#replace-all').click();
        await page.locator('#replace-confirm-yes').click();
        await expect.poll(async () => (await textOf(request, project.projectId, first[0]))[0]).toBe('<b>Дравен</b> прийшов. Дравена бачили, Дрейвенський не чіпати.');
        expect(await textOf(request, project.projectId, first[1])).toEqual(['Лише Дравеном і дравен.', true]); // still proofread, case of the first letter kept
        expect((await textOf(request, project.projectId, second[0]))[0]).toBe('Дравену сказали.');
        await expect(page.locator('#chapter-bulk-status')).toContainText('Замінено 5 збігів у 2 розділах');

        // one undo for the whole action, across both chapters; then redo
        await page.locator('#undo-translation').click();
        await expect.poll(async () => (await textOf(request, project.projectId, second[0]))[0]).toBe(Q1);
        expect((await textOf(request, project.projectId, first[0]))[0]).toBe(P1);
        expect(await textOf(request, project.projectId, first[1])).toEqual([P2, true]);
        await page.locator('#redo-translation').click();
        await expect.poll(async () => (await textOf(request, project.projectId, second[0]))[0]).toBe('Дравену сказали.');
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});

test('unsaved edits are offered to be saved first; a narrow screen docks the panel at the bottom', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Replace unsaved ${Date.now()}`;
    const { project, first } = await createProject(request, title);
    try {
        await page.setViewportSize({ width: 820, height: 1100 });
        await openFirstChapter(page, title);
        const editor = page.locator('.translation-row').nth(2).locator('.translation-paragraph');
        await editor.click();
        await editor.pressSequentially('Нова правка');
        await page.locator('#open-search').click();
        await page.locator('#replace-mode-toggle').click();
        await page.locator('#search-input').fill('Дрейвен');
        await page.locator('#replace-input').fill('Дравен');
        await expect(page.locator('#search-status')).toHaveText(total(4));
        const box = (await page.locator('#search-dialog .search-dialog-content').boundingBox())!;
        expect(Math.round(box.y + box.height)).toBe(1100);
        expect(box.height).toBeLessThanOrEqual(1100 * 0.48 + 1);

        const asked: string[] = [];
        page.once('dialog', (confirm) => { asked.push(confirm.message()); void confirm.dismiss(); });
        await page.locator('#replace-all').click();
        await expect.poll(() => asked.length).toBe(1);
        expect(asked[0]).toContain('незбережені зміни');
        await expect(page.locator('#replace-confirm')).toBeHidden(); // declined: nothing happens
        expect((await textOf(request, project.projectId, first[0]))[0]).toBe(P1);

        page.once('dialog', (confirm) => { void confirm.accept(); });
        await page.locator('#replace-all').click();
        await expect(page.locator('#replace-confirm')).toBeVisible();
        await page.locator('#replace-confirm-yes').click();
        await expect.poll(async () => (await textOf(request, project.projectId, first[0]))[0]).toContain('Дравен');
        expect((await textOf(request, project.projectId, first[2]))[0]).toBe('Нова правка'); // the edit was saved, not lost
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});
