import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// «Вичитано» (the second stage after «Перевірено») and the progress figures: the checkbox, the chapter bulk marks,
// the bars on the chapter chips, on the project page and on the project cards, in paragraphs or words.
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

async function structure(request: APIRequestContext, projectId: string) {
    return (await (await request.get(`/api/projects/${projectId}/book/structure`)).json()).chapters;
}

const put = async (request: APIRequestContext, paragraphId: string, data: Record<string, unknown>) =>
    expect((await request.put(`/api/paragraphs/${paragraphId}`, { data })).ok()).toBeTruthy();

// Chapter 1: the last paragraph is service text; paragraphs 1–10 are translated, no. 1 is also reviewed and proofread.
// Chapter 2: translated, reviewed and proofread (a whole chapter proofread). Chapter 3: translated only.
// Chapter 4: «Не експортувати», translated, reviewed and proofread (not counted anywhere).
async function prepare(request: APIRequestContext, title: string) {
    const project = await createProject(request, title);
    const chapters = await structure(request, project.projectId);
    const ids = chapters.map((chapter: any) => chapter.elements.filter((element: any) => element.type === 'paragraph').map((element: any) => element.paragraphId));
    for (let index = 0; index < 10; index += 1) {
        await put(request, ids[0][index], { translationText: `Переклад ${index + 1}`, reviewed: index === 0, proofread: index === 0 });
    }
    await put(request, ids[0][79], { translationText: null, reviewed: false, isService: true });
    await put(request, ids[1][0], { translationText: 'Розділ 2', reviewed: true, proofread: true });
    await put(request, ids[2][0], { translationText: 'Розділ 3', reviewed: false });
    await put(request, ids[3][0], { translationText: 'Розділ 4', reviewed: true, proofread: true });
    expect((await request.patch(`/api/projects/${project.projectId}/chapters/${chapters[3].chapterId}/export-flag`, { data: { excludeFromExport: true } })).ok()).toBeTruthy();
    return { project, chapters, ids };
}

// What the page should show, computed here from the book itself: paragraphs and words of the original.
async function expected(request: APIRequestContext, projectId: string) {
    const chapters = await structure(request, projectId);
    const sums = { paragraphs: [0, 0, 0, 0], words: [0, 0, 0, 0] };
    chapters.filter((chapter: any) => !chapter.excludeFromExport).forEach((chapter: any) => {
        chapter.elements.filter((element: any) => element.type === 'paragraph' && !element.isService && (element.originalText || '').trim()).forEach((element: any) => {
            const flags = [true, Boolean((element.translationText || '').trim()), element.reviewed, element.proofread];
            flags.forEach((flag, position) => {
                if (!flag) return;
                sums.paragraphs[position] += 1;
                sums.words[position] += element.wordCount || 0;
            });
        });
    });
    return sums;
}

const percent = (part: number, total: number) => (total ? (part / total) * 100 : 0);
const rounded = (value: number) => `${Math.round(value)} %`;
const overall = (counts: number[]) => (percent(counts[1], counts[0]) + percent(counts[2], counts[0]) + percent(counts[3], counts[0])) / 3;

async function openProject(page: Page, title: string) {
    await page.goto('/');
    await page.locator('.project-card').filter({ hasText: title }).getByRole('button', { name: 'Відкрити проєкт' }).click();
}

async function openFirstChapter(page: Page, title: string) {
    await openProject(page, title);
    await page.getByRole('button', { name: 'Переклад', exact: true }).click();
    const showStructure = page.getByRole('button', { name: 'Переглянути структуру книги' });
    const firstChapter = page.locator('.chapter-button').first();
    await expect(showStructure.or(firstChapter).first()).toBeVisible();
    if (!(await firstChapter.isVisible())) await showStructure.click();
    await firstChapter.click();
    await expect(page.locator('.translation-row')).toHaveCount(80);
}

const row = (page: Page, index: number) => page.locator('.translation-row').nth(index);
const proofreadBox = (page: Page, index: number) => row(page, index).locator('.paragraph-proofread input');
const reviewedBox = (page: Page, index: number) => row(page, index).locator('.paragraph-review').first().locator('input');
const apiParagraph = async (request: APIRequestContext, projectId: string, paragraphId: string) => {
    for (const chapter of await structure(request, projectId)) {
        const found = chapter.elements.find((element: any) => element.paragraphId === paragraphId);
        if (found) return found;
    }
    throw new Error('no paragraph');
};

test.afterEach(async ({ page }) => {
    await page.evaluate(() => { try { localStorage.removeItem('workbench.progressUnit'); } catch { /* ignore */ } }).catch(() => {});
});

test('the «Вичитано» box: independent of «Перевірено», saved, undone, remembered', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Proofread box ${Date.now()}`;
    const { project, ids } = await prepare(request, title);
    try {
        await page.setViewportSize({ width: 1440, height: 900 });
        await openFirstChapter(page, title);
        await expect(proofreadBox(page, 0)).toBeChecked();             // paragraph 1 came proofread and reviewed
        await expect(reviewedBox(page, 0)).toBeChecked();
        await expect(proofreadBox(page, 2)).not.toBeChecked();
        await expect(row(page, 2).locator('.paragraph-proofread')).toContainText('Вичитано');

        // proofread without «Перевірено»; the paragraph is unsaved until the chapter is saved
        await proofreadBox(page, 2).check();
        await expect(reviewedBox(page, 2)).not.toBeChecked();
        await expect(page.locator('#save-translation')).toBeEnabled();
        await page.locator('#undo-translation').click();
        await expect(proofreadBox(page, 2)).not.toBeChecked();
        await page.locator('#redo-translation').click();
        await expect(proofreadBox(page, 2)).toBeChecked();
        await page.locator('#save-translation').click();
        await expect.poll(async () => {
            const saved = await apiParagraph(request, project.projectId, ids[0][2]);
            return [saved.proofread, saved.reviewed];
        }).toEqual([true, false]);

        // a manual edit does not clear it; reloading shows the saved state
        await row(page, 2).locator('.translation-paragraph').click();
        await page.keyboard.type(' правка');
        await page.locator('#save-translation').click();
        await expect.poll(async () => (await apiParagraph(request, project.projectId, ids[0][2])).translationText).toContain('правка');
        expect((await apiParagraph(request, project.projectId, ids[0][2])).proofread).toBe(true);
        await page.reload();
        await openFirstChapter(page, title);
        await expect(proofreadBox(page, 2)).toBeChecked();
        // 44 px targets are covered by the compact-layout spec; the box is next to «Перевірено» in the same bar
        const bar = await row(page, 2).locator('.para-bar').boundingBox();
        const mark = await row(page, 2).locator('.paragraph-proofread').boundingBox();
        expect(mark!.y).toBeGreaterThanOrEqual(bar!.y - 1);
        expect(mark!.y + mark!.height).toBeLessThanOrEqual(bar!.y + bar!.height + 1);
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});

test('the chapter menu marks or clears a whole chapter: service text skipped, a counted confirmation, one undo step', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Proofread bulk ${Date.now()}`;
    const { project, ids } = await prepare(request, title);
    try {
        await page.setViewportSize({ width: 1440, height: 900 });
        await openFirstChapter(page, title);
        const message = { text: '' };
        page.on('dialog', async (dialog) => { message.text = dialog.message(); await dialog.accept(); });
        const menu = async (id: string) => { await page.locator('#chapter-more-button').click(); await page.locator(id).click(); };

        // 79 paragraphs count (the service one is skipped), 1 of them is already proofread → 78 change
        await menu('#mark-chapter-proofread');
        expect(message.text).toContain('78 абзаців');
        expect(message.text).toContain('Службовий текст пропускається (1)');
        await expect(proofreadBox(page, 5)).toBeChecked();
        await expect(proofreadBox(page, 79)).not.toBeChecked();                 // the service paragraph is untouched
        await expect(page.locator('#chapter-bulk-status')).toContainText('Позначено «Вичитано»: 78');

        // one undo step takes all of it back (paragraph 1 stays proofread as it was)
        await page.locator('#undo-translation').click();
        await expect(proofreadBox(page, 5)).not.toBeChecked();
        await expect(proofreadBox(page, 0)).toBeChecked();
        await page.locator('#redo-translation').click();
        await expect(proofreadBox(page, 5)).toBeChecked();

        await page.locator('#save-translation').click();
        await expect.poll(async () => (await apiParagraph(request, project.projectId, ids[0][5])).proofread).toBe(true);
        expect((await apiParagraph(request, project.projectId, ids[0][79])).proofread).toBe(false);

        // «Перевірено» the same way, then both can be taken off
        await menu('#mark-chapter-reviewed');
        expect(message.text).toContain('«Перевірено»');
        await expect(reviewedBox(page, 7)).toBeChecked();
        await menu('#unmark-chapter-proofread');
        expect(message.text).toContain('Зняти «Вичитано» з 79 абзаців');
        await expect(proofreadBox(page, 0)).not.toBeChecked();
        await menu('#unmark-chapter-proofread');                                // nothing left to take off: no question
        await expect(page.locator('#chapter-bulk-status')).toContainText('немає абзаців із «Вичитано»');
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});

test('chips: a thin bar inside the chip, «✓» for a proofread chapter, numbers in the tooltip, the pinned row does not grow', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Proofread chips ${Date.now()}`;
    const { project } = await prepare(request, title);
    try {
        await page.setViewportSize({ width: 1440, height: 900 });
        await openFirstChapter(page, title);
        const chip = (number: number) => page.locator('.chapter-button').nth(number - 1);
        const fill = (number: number, metric: string) => chip(number).locator(`.chapter-progress i[data-metric="${metric}"] b`);
        const width = async (number: number, metric: string) => (await fill(number, metric).boundingBox())?.width ?? 0;

        // chapter 3: translated only; chapter 2: all three and «✓»; chapter 4 («Не експортувати») has no bar
        await expect.poll(async () => width(3, 'translated')).toBeGreaterThan(20);
        expect(await width(3, 'reviewed')).toBe(0);
        expect(await width(3, 'proofread')).toBe(0);
        await expect(chip(2).locator('.chapter-proofread-mark')).toBeVisible();
        await expect(chip(3).locator('.chapter-proofread-mark')).toBeHidden();
        await expect(chip(2)).toHaveClass(/proofread-all/);
        await expect(chip(4).locator('.chapter-progress')).toBeHidden();
        // chapter 1 (open): 10 of 79 translated, 1 reviewed, 1 proofread; the proofread part is thin but visible (≥ 2 px)
        expect(await width(1, 'proofread')).toBeGreaterThanOrEqual(1.9);
        expect(await width(1, 'translated')).toBeGreaterThan(await width(1, 'proofread'));
        await expect(chip(1)).toHaveAttribute('title', /Перекладено: 10 з 79 абзаців/);
        await expect(chip(1)).toHaveAttribute('title', /Вичитано: 1 з 79 абзаців/);
        // the bar is inside the chip: it adds nothing to its height
        expect(await chip(1).locator('.chapter-progress').evaluate((bar) => getComputedStyle(bar).position)).toBe('absolute');

        // it follows a ticked box at once (no save, no reload)
        const before = await width(1, 'reviewed');
        for (let index = 3; index < 23; index += 1) await reviewedBox(page, index).check();      // 21 of 79 now
        await expect.poll(async () => width(1, 'reviewed')).toBeGreaterThan(before + 5);

        // pinned: the strip stays about as tall as before (a chip is 40 px; the strip ≤ 49 px)
        await page.locator('.translation-row').nth(40).scrollIntoViewIfNeeded();
        await page.mouse.wheel(0, 300);
        await expect(page.locator('#chapter-list')).toHaveClass(/chapters-strip--stuck/);
        expect((await page.locator('#chapter-list').boundingBox())!.height).toBeLessThanOrEqual(49);
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});

test('the project page: four bars with «N з M · X %», paragraphs or words, one remembered unit', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Proofread page ${Date.now()}`;
    const { project } = await prepare(request, title);
    try {
        await page.setViewportSize({ width: 1440, height: 900 });
        const sums = await expected(request, project.projectId);
        expect(sums.paragraphs[0]).toBe(89);                               // 79 + 10 (the service line and the «Не експортувати» chapter are out)
        await openProject(page, title);
        const block = page.locator('#project-progress-block');
        const rowOf = (metric: string) => block.locator(`.progress-row[data-metric="${metric}"]`);
        await expect(block.locator('h3')).toHaveText('Прогрес');
        await expect(rowOf('translated')).toContainText(`${sums.paragraphs[1]} з ${sums.paragraphs[0]} · ${rounded(percent(sums.paragraphs[1], sums.paragraphs[0]))}`);
        await expect(rowOf('reviewed')).toContainText(`${sums.paragraphs[2]} з ${sums.paragraphs[0]} · ${rounded(percent(sums.paragraphs[2], sums.paragraphs[0]))}`);
        await expect(rowOf('proofread')).toContainText(`${sums.paragraphs[3]} з ${sums.paragraphs[0]} · ${rounded(percent(sums.paragraphs[3], sums.paragraphs[0]))}`);
        await expect(rowOf('overall')).toContainText(rounded(overall(sums.paragraphs)));
        await expect(rowOf('overall').locator('.progress-track')).toHaveAttribute('role', 'progressbar');
        await expect(rowOf('overall')).toHaveAttribute('title', /середнє трьох відсотків/);

        // words: the same four figures in words of the original, remembered and shared with the project list
        await block.getByRole('radio', { name: 'Слова' }).click();
        await expect(rowOf('translated')).toContainText(`${sums.words[1]} з ${sums.words[0]} · ${rounded(percent(sums.words[1], sums.words[0]))}`);
        await expect(rowOf('overall')).toContainText(rounded(overall(sums.words)));
        expect(await page.evaluate(() => localStorage.getItem('workbench.progressUnit'))).toBe('words');
        await page.reload();
        await openProject(page, title);
        await expect(page.locator('#project-progress-block').getByRole('radio', { name: 'Слова' })).toHaveAttribute('aria-checked', 'true');
        await expect(page.locator('#project-progress-block .progress-row[data-metric="translated"]')).toContainText(`${sums.words[1]} з ${sums.words[0]}`);
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});

for (const viewport of [{ width: 1280, height: 800 }, { width: 390, height: 844 }]) {
    test(`the project card at ${viewport.width}px: four labelled bars with percent text, the unit switch, nothing wider than the screen`, async ({ page, request }) => {
        test.setTimeout(120_000);
        const title = `Proofread card ${viewport.width} ${Date.now()}`;
        const { project } = await prepare(request, title);
        try {
            await page.setViewportSize(viewport);
            const sums = await expected(request, project.projectId);
            await page.goto('/');
            const card = page.locator('.project-card').filter({ hasText: title });
            await expect(card).toBeVisible();
            const labels = await card.locator('.progress-name').allTextContents();
            expect(labels).toEqual(['Перекладено', 'Перевірено', 'Вичитано', 'Загальне']);
            const percents = await card.locator('.progress-percent').allTextContents();
            expect(percents).toEqual([
                rounded(percent(sums.paragraphs[1], sums.paragraphs[0])), rounded(percent(sums.paragraphs[2], sums.paragraphs[0])),
                rounded(percent(sums.paragraphs[3], sums.paragraphs[0])), rounded(overall(sums.paragraphs)),
            ]);
            await expect(card.locator('.progress-row[data-metric="translated"]')).toHaveAttribute('title', new RegExp(`${sums.paragraphs[1]} з ${sums.paragraphs[0]} абзаців`));
            // distinct colours for the four bars (the percent text carries the meaning too)
            const colours = await card.locator('.progress-value').evaluateAll((bars) => bars.map((bar) => getComputedStyle(bar).backgroundColor));
            expect(new Set(colours).size).toBe(4);
            // nothing is wider than the screen, no horizontal scroll
            const widest = await card.locator('.progress-row').evaluateAll((rows) => Math.max(...rows.map((item) => item.getBoundingClientRect().right)));
            expect(widest).toBeLessThanOrEqual(viewport.width);
            expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1)).toBe(true);

            // the unit switch is in the header of the project list; it redraws the card in words
            await page.locator('#progress-unit-slot').getByRole('radio', { name: 'Слова' }).click();
            await expect(card.locator('.progress-row[data-metric="translated"]')).toHaveAttribute('title', new RegExp(`${sums.words[1]} з ${sums.words[0]} слів`));
            expect(await card.locator('.progress-percent').allTextContents()).toEqual([
                rounded(percent(sums.words[1], sums.words[0])), rounded(percent(sums.words[2], sums.words[0])),
                rounded(percent(sums.words[3], sums.words[0])), rounded(overall(sums.words)),
            ]);
        } finally {
            await request.delete(`/api/projects/${project.projectId}`);
        }
    });
}

test('after a mark is changed and saved, the chapter chip, the project page and the project card follow', async ({ page, request }) => {
    test.setTimeout(120_000);
    const title = `Proofread follow ${Date.now()}`;
    const { project, ids } = await prepare(request, title);
    try {
        await page.setViewportSize({ width: 1440, height: 900 });
        await openFirstChapter(page, title);
        await proofreadBox(page, 4).check();
        await proofreadBox(page, 5).check();
        await page.locator('#save-translation').click();
        await expect.poll(async () => (await apiParagraph(request, project.projectId, ids[0][5])).proofread).toBe(true);
        const progress = await (await request.get(`/api/projects/${project.projectId}/progress`)).json();
        expect(progress.paragraphs.proofread).toBe(4);
        expect(progress.chapters[0].paragraphs.proofread).toBe(3);
        expect(progress.chapters[3].excluded).toBe(true);

        await expect(page.locator('.chapter-button').first()).toHaveAttribute('title', /Вичитано: 3 з 79 абзаців/);
        await page.locator('.project-mode-navigation-button[data-project-mode="book-info"]').click();
        await expect(page.locator('#project-progress-block .progress-row[data-metric="proofread"]')).toContainText('4 з 89');
        await page.goto('/');
        const card = page.locator('.project-card').filter({ hasText: title });
        await expect(card.locator('.progress-row[data-metric="proofread"] .progress-percent')).toHaveText(rounded(percent(4, 89)));
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});
