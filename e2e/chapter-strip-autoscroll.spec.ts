import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// test-data/many-long-chapters.epub: twelve chapters of 40 paragraphs, so the chapter strip
// scrolls sideways and the page is tall enough for the strip to be pinned.
// Opening a project must bring the remembered (active) chapter's chip into view.

async function createLongProject(request: APIRequestContext, title: string) {
    const created = await request.post('/api/projects', { data: { title, status: 'translation' } });
    expect(created.ok()).toBeTruthy();
    const project = await created.json();
    const upload = await request.post('/upload', {
        headers: { 'X-Project-Id': project.projectId },
        multipart: {
            file: {
                name: 'many-long-chapters.epub',
                mimeType: 'application/epub+zip',
                buffer: fs.readFileSync(path.join(__dirname, '..', 'test-data', 'many-long-chapters.epub')),
            },
        },
    });
    expect(upload.ok()).toBeTruthy();
    return project;
}

async function openProject(page: Page, title: string) {
    await page.goto('/');
    await page.locator('.project-card').filter({ hasText: title }).getByRole('button', { name: 'Відкрити проєкт' }).click();
    await page.getByRole('button', { name: 'Переклад', exact: true }).click();
}

// The active chip lies completely inside the strip's visible box (and the strip is on screen).
async function activeChipIsVisibleInStrip(page: Page) {
    return page.evaluate(() => {
        const strip = document.querySelector('#chapter-list')!.getBoundingClientRect();
        const chip = document.querySelector('#chapter-list .chapter-button.active')?.getBoundingClientRect();
        if (!chip) return 'no active chip';
        const inside = chip.left >= strip.left - 1 && chip.right <= strip.right + 1;
        const stripOnScreen = strip.bottom > 0 && strip.top < window.innerHeight;
        return inside && stripOnScreen ? 'visible' : `chip ${Math.round(chip.left)}–${Math.round(chip.right)} strip ${Math.round(strip.left)}–${Math.round(strip.right)}`;
    });
}

for (const viewport of [{ width: 1280, height: 800 }, { width: 820, height: 1180 }, { width: 390, height: 844 }]) {
    test(`opening a project scrolls the chapter strip to the active chapter (${viewport.width}px)`, async ({ page, request }) => {
        await page.setViewportSize(viewport);
        const title = `Strip autoscroll ${Date.now()}`;
        const project = await createLongProject(request, title);
        try {
            await openProject(page, title);
            const showStructure = page.getByRole('button', { name: 'Переглянути структуру книги' });
            if (await showStructure.isVisible()) await showStructure.click();
            const lastChip = page.locator('#chapter-list .chapter-button').last();
            await lastChip.scrollIntoViewIfNeeded();
            await lastChip.click();
            await expect(lastChip).toHaveClass(/active/);

            // Reopen the project: the remembered chapter is active, the strip starts at its left edge.
            await openProject(page, title);
            await expect(page.locator('#chapter-list .chapter-button.active')).toHaveCount(1);
            // on a phone the project information (one column of cards) pushes the strip below the first screen
            await page.locator('#chapter-list').scrollIntoViewIfNeeded();
            await expect.poll(() => activeChipIsVisibleInStrip(page), { message: 'active chip must be scrolled into the strip' }).toBe('visible');

            // Same after the strip has been pinned under the top bar (smaller chips, fixed position).
            await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight)); // well past the strip, however tall the info above it is
            await expect(page.locator('.chapter-list.chapters-strip--stuck')).toHaveCount(1);
            await expect.poll(() => activeChipIsVisibleInStrip(page), { message: 'pinning the strip must keep the active chip in view' }).toBe('visible');
            await page.reload();
            await page.locator('.project-card').filter({ hasText: title }).getByRole('button', { name: 'Відкрити проєкт' }).click();
            await page.getByRole('button', { name: 'Переклад', exact: true }).click();
            await page.locator('#chapter-list').scrollIntoViewIfNeeded();
            await expect.poll(() => activeChipIsVisibleInStrip(page)).toBe('visible');
        } finally {
            await request.delete(`/api/projects/${project.projectId}`);
        }
    });
}
