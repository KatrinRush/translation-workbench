import { expect, test, type APIRequestContext, type Locator, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Regression: the status colours (the chip background of a chapter: none / partly reviewed / all reviewed, and the
// stripe at the left of a paragraph: untranslated / translated / reviewed) must not depend on «Вичитано», and the
// three-part bar of a chip must show translated / reviewed / proofread separately — in paragraphs and in words,
// for the open chapter (drafts) and for the others (the server's figures), also after a reload.
// long-chapter.epub: chapter 1 has 80 paragraphs, then eleven one-paragraph chapters.

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

const put = async (request: APIRequestContext, paragraphId: string, data: Record<string, unknown>) =>
    expect((await request.put(`/api/paragraphs/${paragraphId}`, { data })).ok()).toBeTruthy();

// Chapter 1: paragraphs 1–10 translated, 1–5 of them reviewed (partly reviewed), 1 also proofread.
// Chapter 3: its only paragraph translated and reviewed (all reviewed). Chapter 5: nothing done.
async function prepare(request: APIRequestContext, title: string) {
    const project = await createProject(request, title);
    const chapters = (await (await request.get(`/api/projects/${project.projectId}/book/structure`)).json()).chapters;
    const paragraphs = chapters.map((chapter: any) => chapter.elements.filter((element: any) => element.type === 'paragraph'));
    for (let index = 0; index < 10; index += 1) {
        await put(request, paragraphs[0][index].paragraphId, { translationText: `Переклад ${index + 1}`, reviewed: index < 5, proofread: index === 0 });
    }
    await put(request, paragraphs[2][0].paragraphId, { translationText: 'Розділ 3', reviewed: true });
    return { project, paragraphs };
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

const chip = (page: Page, number: number) => page.locator('.chapter-button').nth(number - 1);
const background = (locator: Locator) => locator.evaluate((element) => getComputedStyle(element).backgroundColor);
const stripe = (locator: Locator) => locator.evaluate((element) => getComputedStyle(element).borderLeftColor);

// the filled part of a chip's bar, as a fraction (0..1) of its part; a visible minimum of 2 px counts as «there is some»
async function segment(locator: Locator, metric: string) {
    return locator.locator(`.chapter-progress i[data-metric="${metric}"]`).evaluate((part) => {
        const fill = part.querySelector('b') as HTMLElement;
        return { fill: fill.getBoundingClientRect().width, whole: part.getBoundingClientRect().width };
    });
}

async function expectSegments(locator: Locator, expected: { translated: number; reviewed: number; proofread: number }, label: string) {
    await expect.poll(async () => {
        const result: Record<string, boolean> = {};
        for (const metric of ['translated', 'reviewed', 'proofread'] as const) {
            const { fill, whole } = await segment(locator, metric);
            const want = expected[metric];
            result[metric] = want === 0 ? fill < 0.5 : (fill >= 1.9 && Math.abs(fill / whole - want) <= 0.03 + 2 / whole);
        }
        return result;
    }, { message: `${label}: the three parts of the bar show translated / reviewed / proofread separately` }).toEqual({ translated: true, reviewed: true, proofread: true });
}

// counts of chapter 1 (79 paragraphs: the last... none is service here, 80), in paragraphs and in words of the original
function shares(paragraphs: any[], flags: (index: number) => [boolean, boolean, boolean], unit: 'paragraphs' | 'words') {
    const weight = (element: any) => (unit === 'words' ? element.wordCount : 1);
    const total = paragraphs.reduce((sum, element) => sum + weight(element), 0);
    const sums = [0, 0, 0];
    paragraphs.forEach((element, index) => flags(index).forEach((flag, position) => { if (flag) sums[position] += weight(element); }));
    return { translated: sums[0] / total, reviewed: sums[1] / total, proofread: sums[2] / total };
}

for (const unit of ['paragraphs', 'words'] as const) {
    test(`status colours and the bar of a chip stay right after «Вичитано» is ticked (${unit}), also after a reload`, async ({ page, request }) => {
        test.setTimeout(150_000);
        const title = `Status colours ${unit} ${Date.now()}`;
        const { project, paragraphs } = await prepare(request, title);
        try {
            await page.addInitScript((value) => { try { localStorage.setItem('workbench.progressUnit', value); } catch { /* ignore */ } }, unit);
            await page.setViewportSize({ width: 1440, height: 900 });
            await openFirstChapter(page, title);
            const rows = page.locator('.translation-row');

            // --- before: the colours of the chips and of the paragraph stripes
            const plainBackground = await background(chip(page, 5));                       // nothing done in chapter 5
            await expect(chip(page, 1)).toHaveClass(/reviewed-partial/);
            await expect(chip(page, 3)).toHaveClass(/reviewed-all/);
            const partial = await background(chip(page, 1));
            const allReviewed = await background(chip(page, 3));
            expect(new Set([plainBackground, partial, allReviewed]).size).toBe(3);        // three different colours
            const stripes = { reviewed: await stripe(rows.nth(1)), translated: await stripe(rows.nth(7)), untranslated: await stripe(rows.nth(20)) };
            expect(new Set(Object.values(stripes)).size).toBe(3);
            await expect(rows.nth(1)).toHaveClass(/paragraph-reviewed/);
            await expect(rows.nth(7)).toHaveClass(/paragraph-translated/);
            await expect(rows.nth(20)).toHaveClass(/paragraph-untranslated/);

            // the bar of the open chapter (drafts) and of the others (the server's figures)
            const chapterOne = (proofread: (index: number) => boolean) =>
                shares(paragraphs[0], (index) => [index < 10, index < 5, proofread(index)], unit);
            await expectSegments(chip(page, 1), chapterOne((index) => index === 0), 'chapter 1 before');
            await expectSegments(chip(page, 3), { translated: 1, reviewed: 1, proofread: 0 }, 'chapter 3 before');

            // --- «Вичитано» on several paragraphs (some reviewed, some translated only, some empty)
            for (const index of [1, 7, 20, 21]) await rows.nth(index).locator('.paragraph-proofread input').check();
            const proofreadAfter = (index: number) => [0, 1, 7, 20, 21].includes(index);
            await expectSegments(chip(page, 1), chapterOne(proofreadAfter), 'chapter 1 after ticking');
            await expect(chip(page, 1)).toHaveClass(/reviewed-partial/);
            expect(await background(chip(page, 1))).toBe(partial);
            await expect(chip(page, 3)).toHaveClass(/reviewed-all/);
            expect(await background(chip(page, 3))).toBe(allReviewed);
            expect(await stripe(rows.nth(1))).toBe(stripes.reviewed);
            expect(await stripe(rows.nth(7))).toBe(stripes.translated);
            expect(await stripe(rows.nth(20))).toBe(stripes.untranslated);
            await expect(rows.nth(1)).toHaveClass(/paragraph-reviewed/);

            // the marks are independent: proofread without translation and without «Перевірено» changes nothing else
            const bar = await segment(chip(page, 1), 'translated');
            await page.locator('#save-translation').click();
            await expect.poll(() => page.evaluate('isTranslationDirty(selectedChapterIndex)')).toBe(false);
            await expectSegments(chip(page, 1), chapterOne(proofreadAfter), 'chapter 1 after saving');
            expect((await segment(chip(page, 1), 'translated')).fill).toBeCloseTo(bar.fill, 1);

            // --- after a reload: the same colours, the bar from the server's figures, then from the drafts of the opened chapter
            await page.reload();
            await expect(page.locator('.project-card').first()).toBeVisible();
            await page.locator('.project-card').filter({ hasText: title }).getByRole('button', { name: 'Відкрити проєкт' }).click();
            await page.getByRole('button', { name: 'Переклад', exact: true }).click();
            const showStructure = page.getByRole('button', { name: 'Переглянути структуру книги' });
            if (await showStructure.isVisible()) await showStructure.click();
            await expect(chip(page, 1)).toHaveClass(/reviewed-partial/);
            await expect(chip(page, 3)).toHaveClass(/reviewed-all/);
            expect(await background(chip(page, 1))).toBe(partial);
            expect(await background(chip(page, 3))).toBe(allReviewed);
            await expectSegments(chip(page, 1), chapterOne(proofreadAfter), 'chapter 1 after reload (not opened)');
            await expectSegments(chip(page, 3), { translated: 1, reviewed: 1, proofread: 0 }, 'chapter 3 after reload');
            await chip(page, 1).click();
            await expect(rows).toHaveCount(80);
            expect(await stripe(rows.nth(1))).toBe(stripes.reviewed);
            expect(await stripe(rows.nth(7))).toBe(stripes.translated);
            await expectSegments(chip(page, 1), chapterOne(proofreadAfter), 'chapter 1 after reload (opened)');
        } finally {
            await request.delete(`/api/projects/${project.projectId}`);
        }
    });
}

test('switching the unit to words while a chapter is open keeps the bars of the chips (no zeros), both ways', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Status colours switch ${Date.now()}`;
    const { project, paragraphs } = await prepare(request, title);
    try {
        await page.setViewportSize({ width: 1440, height: 900 });
        await openFirstChapter(page, title);
        const flags = (index: number): [boolean, boolean, boolean] => [index < 10, index < 5, index === 0];
        await expectSegments(chip(page, 1), shares(paragraphs[0], flags, 'paragraphs'), 'paragraphs');
        await page.locator('.project-mode-navigation-button[data-project-mode="book-info"]').click();
        await page.locator('#project-progress-block').getByRole('radio', { name: 'Слова' }).click();
        await page.getByRole('button', { name: 'Переклад', exact: true }).click();
        await expect(chip(page, 1)).toHaveClass(/reviewed-partial/);                      // the colours do not depend on the unit
        await expectSegments(chip(page, 1), shares(paragraphs[0], flags, 'words'), 'words');
        await expectSegments(chip(page, 3), { translated: 1, reviewed: 1, proofread: 0 }, 'words, chapter 3');
        await page.locator('.project-mode-navigation-button[data-project-mode="book-info"]').click();
        await page.locator('#project-progress-block').getByRole('radio', { name: 'Абзаци' }).click();
        await page.getByRole('button', { name: 'Переклад', exact: true }).click();
        await expectSegments(chip(page, 1), shares(paragraphs[0], flags, 'paragraphs'), 'paragraphs again');
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});
