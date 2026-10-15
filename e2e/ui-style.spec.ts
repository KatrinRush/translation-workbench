import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// The look: badges only where a state is rare or describes a whole project or chapter (never one per paragraph), one dark primary
// action in the chapter actions, no emoji in the interface, Inter for Latin and Cyrillic (incl. ґ є і ї), 16px cards.

async function createProject(request: APIRequestContext, title: string) {
    const project = await (await request.post('/api/projects', { data: { title, status: 'translation' } })).json();
    const upload = await request.post('/upload', {
        headers: { 'X-Project-Id': project.projectId },
        multipart: { file: { name: 'long-chapter.epub', mimeType: 'application/epub+zip', buffer: fs.readFileSync(path.join(__dirname, '..', 'test-data', 'long-chapter.epub')) } },
    });
    expect(upload.ok()).toBeTruthy();
    const structure = await (await request.get(`/api/projects/${project.projectId}/book/structure`)).json();
    const ids = structure.chapters[0].elements.filter((e: any) => e.paragraphId).map((e: any) => e.paragraphId);
    for (const id of ids.slice(0, 3)) {
        await request.put(`/api/paragraphs/${id}`, { data: { translationText: 'Дрейвен прийшов до моря, де гуси сперечалися.', reviewed: false } });
    }
    return project;
}

// text a person can read: without the screen-reader-only marks, the sprite and scripts
async function readableText(page: Page) {
    return page.evaluate(() => {
        const clone = document.body.cloneNode(true) as HTMLElement;
        clone.querySelectorAll('.sr-only, svg, script, style, textarea').forEach((el) => el.remove());
        return clone.textContent || '';
    });
}

const PICTOGRAPH = /\p{Extended_Pictographic}|[▴▾▲▼✕✎⏭⋯]/u;

for (const [width, height] of [[390, 844], [1280, 900]] as const) {
    test(`look at ${width}×${height}: badges, icons, one primary action, 16px cards`, async ({ page, request }) => {
        test.setTimeout(120_000);
        await page.setViewportSize({ width, height });
        const title = `Look ${width} ${Date.now()}`;
        const project = await createProject(request, title);
        try {
            await page.goto('/');
            // the project list: the status is a badge; the card has a 16px radius and a shadow instead of a frame
            const card = page.locator('.project-card').filter({ hasText: title });
            await expect(card.locator('.badge')).toHaveText('У перекладі');
            const cardLook = await card.evaluate((el) => { const s = getComputedStyle(el); return { radius: s.borderTopLeftRadius, border: s.borderTopWidth, shadow: s.boxShadow }; });
            expect(cardLook.radius).toBe('16px');
            expect(cardLook.border).toBe('0px');
            expect(cardLook.shadow).not.toBe('none');
            expect(await readableText(page)).not.toMatch(PICTOGRAPH);

            await card.getByRole('button', { name: 'Відкрити проєкт' }).click();
            // the project title carries the status badge
            await expect(page.locator('#project-page-title')).toHaveText(title); // the title stays plain text
            await expect(page.locator('#project-status-badge')).toHaveText('У перекладі');
            expect(await readableText(page)).not.toMatch(PICTOGRAPH);

            await page.getByRole('button', { name: 'Переклад', exact: true }).click();
            const showStructure = page.getByRole('button', { name: 'Переглянути структуру книги' });
            const firstChapter = page.locator('.chapter-button').first();
            await expect(showStructure.or(firstChapter).first()).toBeVisible();
            if (!(await firstChapter.isVisible())) await showStructure.click();
            await firstChapter.click();
            await expect(page.locator('.translation-row').first()).toBeVisible();

            // no badge in a paragraph row: on thousands of paragraphs it is noise; the stripe and the boxes say it
            expect(await page.locator('.translation-row .badge').count()).toBe(0);

            // a chapter left out of the export says so in a badge on its chip
            await page.locator('#chapter-export-checkbox').check();
            await expect(page.locator('.chapter-button.excluded-from-export .chapter-excluded-badge').first()).toBeVisible();
            await page.locator('#chapter-export-checkbox').uncheck();
            await expect(page.locator('.chapter-excluded-badge')).toHaveCount(0);

            if (width > 720) {
                // one dark primary action in the actions row, the rest are white pills
                const row = page.locator('#chapter-actions-row');
                await expect(row.locator('.primary-btn')).toHaveCount(0);
                const translate = await page.locator('#translate-chapter-button').evaluate((el) => { const s = getComputedStyle(el); return { bg: s.backgroundColor, color: s.color, radius: s.borderTopLeftRadius }; });
                expect(translate.radius).not.toBe('0px');
                expect(translate.bg).toBe('rgb(48, 48, 48)'); // --ink on the light theme
                const others = await row.locator('.secondary-btn:not(#translate-chapter-button)').evaluateAll((els) => els.filter((el) => (el as HTMLElement).offsetParent !== null).map((el) => getComputedStyle(el).backgroundColor));
                expect(others.length).toBeGreaterThan(2);
                for (const background of others) expect(background).not.toBe('rgb(48, 48, 48)');
            }
            expect(await readableText(page)).not.toMatch(PICTOGRAPH);
        } finally {
            await request.delete(`/api/projects/${project.projectId}`);
        }
    });
}

test('Inter draws Latin and Cyrillic text, ґ є і ї included', async ({ page }) => {
    await page.goto('/');
    await page.evaluate(() => {
        const probe = document.createElement('p');
        probe.id = 'font-probe';
        probe.textContent = 'Ґанок, їжак, є, і, ґ, Є, І, Ї, Ґ: Дрейвен прийшов до моря';
        probe.style.cssText = 'position:absolute;top:0;left:0;font-size:20px;font-weight:600';
        document.body.append(probe);
    });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(1500);
    const cdp = await page.context().newCDPSession(page);
    await cdp.send('DOM.enable');
    await cdp.send('CSS.enable');
    const { root } = await cdp.send('DOM.getDocument');
    const { nodeId } = await cdp.send('DOM.querySelector', { nodeId: root.nodeId, selector: '#font-probe' });
    const { fonts } = await cdp.send('CSS.getPlatformFontsForNode', { nodeId });
    const inter = fonts.filter((font) => font.familyName === 'Inter' && font.isCustomFont);
    // the font comes from Google Fonts: without a network the stack falls back to the system fonts, which is allowed
    test.skip(inter.length === 0, 'Inter could not be loaded (no network): the fallback stack is used');
    const drawn = fonts.reduce((sum, font) => sum + font.glyphCount, 0);
    expect(inter.reduce((sum, font) => sum + font.glyphCount, 0), 'every glyph, ґ є і ї included, comes from Inter').toBe(drawn);
});
