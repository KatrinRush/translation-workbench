import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// «Наступний невичитаний» and «Показати лише невичитані». long-chapter.epub: chapter 1 has 80 paragraphs, then eleven
// one-paragraph chapters.

test.use({ actionTimeout: 15_000 });   // a stuck click fails with its own message instead of the whole test timing out

async function createProject(request: APIRequestContext, title: string) {
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

async function chapters(request: APIRequestContext, projectId: string) {
    return (await (await request.get(`/api/projects/${projectId}/book/structure`)).json()).chapters;
}

const idsOf = (chapter: any) => chapter.elements.filter((element: any) => element.type === 'paragraph').map((element: any) => element.paragraphId);
const put = async (request: APIRequestContext, paragraphId: string, data: Record<string, unknown>) =>
    expect((await request.put(`/api/paragraphs/${paragraphId}`, { data })).ok()).toBeTruthy();

// Chapter 1: paragraph 1 is proofread, the last one is service text. Chapter 2 is fully proofread. Chapter 4 is «Не експортувати».
async function prepare(request: APIRequestContext, title: string) {
    const project = await createProject(request, title);
    const list = await chapters(request, project.projectId);
    const ids = list.map(idsOf);
    await put(request, ids[0][0], { translationText: 'Переклад 1', reviewed: false, proofread: true });
    await put(request, ids[0][79], { translationText: null, reviewed: false, isService: true });
    await put(request, ids[1][0], { translationText: 'Розділ 2', reviewed: false, proofread: true });
    expect((await request.patch(`/api/projects/${project.projectId}/chapters/${list[3].chapterId}/export-flag`, { data: { excludeFromExport: true } })).ok()).toBeTruthy();
    return { project, list, ids };
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

// «Наступний невичитаний» scrolls smoothly, and an open menu closes when the page scrolls: wait until it has stopped.
async function scrolled(page: Page) {
    await expect.poll(async () => {
        const before = await page.evaluate(() => window.scrollY);
        await page.waitForTimeout(150);
        return before === await page.evaluate(() => window.scrollY);
    }).toBe(true);
}

const next = (page: Page) => page.locator('#next-unproofread-button');
const focusedParagraphId = (page: Page) => page.evaluate(() => (document.activeElement?.closest('.translation-row') as HTMLElement | null)?.dataset.paragraphId ?? null);

test('the button walks to the next paragraph without «Вичитано», through the chapters, skipping service text and excluded chapters', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Next unproofread ${Date.now()}`;
    const { project, ids } = await prepare(request, title);
    try {
        await page.setViewportSize({ width: 1440, height: 900 });
        await openFirstChapter(page, title);
        await expect(next(page)).toHaveText('Наступний невичитаний');

        // from the start of the chapter: paragraph 1 is proofread, so the first stop is paragraph 2
        await next(page).click();
        await expect.poll(() => focusedParagraphId(page)).toBe(ids[0][1]);
        await expect(page.locator('.translation-row').nth(1)).toHaveClass(/paragraph-row-current/);
        await next(page).click();
        await expect.poll(() => focusedParagraphId(page)).toBe(ids[0][2]);

        // proofread paragraphs after the cursor are skipped
        await page.locator('.translation-row').nth(3).locator('.paragraph-proofread input').check();
        await next(page).click();
        await expect.poll(() => focusedParagraphId(page)).toBe(ids[0][4]);

        // the rest of chapter 1 proofread (the menu skips the service paragraph): the next stop is in chapter 3
        await scrolled(page);
        page.once('dialog', (dialog) => { void dialog.accept(); });
        await page.locator('#chapter-more-button').click();
        await page.locator('#mark-chapter-proofread').click();
        await page.locator('#save-translation').click();
        await expect.poll(() => page.evaluate('isTranslationDirty(selectedChapterIndex)')).toBe(false);   // saved: no «unsaved changes» question
        await next(page).click();
        await expect(page.locator('.chapter-button.active')).toContainText('03');       // chapter 2 is proofread already
        await expect.poll(() => focusedParagraphId(page)).toBe(ids[2][0]);

        // chapter 4 is «Не експортувати»: the next stop after chapter 3 is chapter 5
        await next(page).click();
        await expect(page.locator('.chapter-button.active')).toContainText('05');
        await expect.poll(() => focusedParagraphId(page)).toBe(ids[4][0]);
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});

test('with everything proofread to the end the button says so', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Next unproofread end ${Date.now()}`;
    const { project, list, ids } = await prepare(request, title);
    try {
        for (let chapter = 0; chapter < list.length; chapter += 1) {
            for (const [index, paragraphId] of ids[chapter].entries()) {
                if (chapter === 0 && index === 79) continue;                              // the service paragraph
                await put(request, paragraphId, { translationText: `Т ${chapter}-${index}`, reviewed: false, proofread: true });
            }
        }
        await page.setViewportSize({ width: 1440, height: 900 });
        await openFirstChapter(page, title);
        await next(page).click();
        await expect(page.locator('#chapter-bulk-status')).toContainText('невичитаних абзаців немає');
        await expect(page.locator('.chapter-button.active')).toContainText('01');           // it did not move
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});

test('«Показати лише невичитані» hides the proofread paragraphs of the open chapter; a jump to a hidden one shows it', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Unproofread filter ${Date.now()}`;
    const { project } = await prepare(request, title);
    try {
        await page.setViewportSize({ width: 1440, height: 900 });
        await openFirstChapter(page, title);
        const filter = page.getByLabel('Показати лише невичитані');
        const rows = page.locator('.translation-row');
        await expect(filter).not.toBeChecked();
        await expect(rows.first()).toBeVisible();

        await filter.check();
        await expect(page.locator('#unproofread-filter-count')).toHaveText('(показано 79 з 80)');
        await expect(rows.first()).toBeHidden();                                           // paragraph 1 is proofread
        await expect(rows.nth(1)).toBeVisible();
        await expect(page.locator('.translation-row:visible')).toHaveCount(79);

        // search jumps to the hidden paragraph: it is shown (with real heights, not collapsed)
        await page.locator('#open-search').click();
        await page.locator('#search-input').fill('Переклад 1');
        await page.locator('.search-result-item').first().click();
        await expect(rows.first()).toBeVisible();
        expect((await rows.first().locator('.original-paragraph').boundingBox())!.height).toBeGreaterThan(30);
        await page.locator('#close-search-dialog').click();

        // switching off shows everything again; the filter follows the chapter
        await filter.uncheck();
        await expect(page.locator('#unproofread-filter-count')).toHaveText('');
        await expect(page.locator('.translation-row:visible')).toHaveCount(80);
        await filter.check();
        await page.locator('.chapter-button').nth(2).click();
        await expect(page.locator('.translation-row')).toHaveCount(1);                    // chapter 3: one paragraph, not proofread
        await expect(page.locator('.translation-row:visible')).toHaveCount(1);
        await expect(page.locator('#unproofread-filter-count')).toHaveText('(показано 1 з 1)');
        await page.locator('.chapter-button').nth(1).click();                               // chapter 2: all proofread
        await expect(page.locator('.translation-row:visible')).toHaveCount(0);
        await expect(page.locator('#unproofread-filter-count')).toHaveText('(показано 0 з 1)');
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});
