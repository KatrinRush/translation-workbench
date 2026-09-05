import { expect, Page, test } from '@playwright/test';

type ParagraphHeights = {
    originalHeight: number;
    originalScrollHeight: number;
    translationHeight: number;
    translationScrollHeight: number;
};

async function paragraphHeights(page: Page): Promise<ParagraphHeights> {
    return page.locator('.translation-row').evaluate((row) => {
        const original = row.querySelector<HTMLElement>('.original-paragraph')!;
        const translation = row.querySelector<HTMLTextAreaElement>('.translation-paragraph')!;
        return {
            originalHeight: original.offsetHeight,
            originalScrollHeight: original.scrollHeight,
            translationHeight: translation.offsetHeight,
            translationScrollHeight: translation.scrollHeight,
        };
    });
}

async function expectParagraphsToFit(page: Page) {
    await expect.poll(async () => {
        const heights = await paragraphHeights(page);
        return {
            equal: heights.originalHeight === heights.translationHeight,
            originalFits: heights.originalHeight >= heights.originalScrollHeight,
            translationFits: heights.translationHeight >= heights.translationScrollHeight,
        };
    }).toEqual({ equal: true, originalFits: true, translationFits: true });
}

test('paragraph pairs resize after rendering, translation updates, and viewport changes', async ({ page }) => {
    await page.goto('/');
    await page.evaluate(() => {
        const rows = document.querySelector('#translation-rows')!;
        document.body.append(rows);

        const row = document.createElement('div');
        row.className = 'translation-row';
        const original = document.createElement('div');
        original.className = 'original-paragraph';
        original.textContent = 'Long original paragraph '.repeat(80);
        const control = document.createElement('div');
        control.className = 'translation-control';
        const translation = document.createElement('textarea');
        translation.className = 'translation-paragraph';
        const review = document.createElement('label');
        review.className = 'paragraph-review';
        review.append(document.createElement('input'));
        const status = document.createElement('span');
        status.className = 'paragraph-status';
        control.append(translation);
        row.append(original, control, review, status);
        rows.append(row);

        (window as typeof window & { renderTranslationFields(values: unknown[]): void }).renderTranslationFields([{
            paragraphId: 'paragraph-1',
            translationText: 'Long translated paragraph '.repeat(100),
            reviewed: false,
        }]);
    });

    await expectParagraphsToFit(page);
    const desktopHeight = (await paragraphHeights(page)).originalHeight;

    await page.setViewportSize({ width: 820, height: 900 });
    await expectParagraphsToFit(page);

    await page.setViewportSize({ width: 390, height: 844 });
    await expectParagraphsToFit(page);
    expect((await paragraphHeights(page)).originalHeight).toBeGreaterThan(desktopHeight);
});
