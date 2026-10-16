import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Active working time: the heartbeat pings every 30 s only in an open project, in a visible focused tab, and only while the last
// user action is under 90 s old. Time is a fake clock, so nothing here waits for real minutes.

async function createProject(request: APIRequestContext, title: string) {
    const project = await (await request.post('/api/projects', { data: { title, status: 'translation' } })).json();
    const upload = await request.post('/upload', {
        headers: { 'X-Project-Id': project.projectId },
        multipart: { file: { name: 'long-chapter.epub', mimeType: 'application/epub+zip', buffer: fs.readFileSync(path.join(__dirname, '..', 'test-data', 'long-chapter.epub')) } },
    });
    expect(upload.ok()).toBeTruthy();
    return project;
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

// every POST /api/activity of the page (answered here, so the real clock and database are not involved)
async function recordPings(page: Page) {
    const pings: Array<{ projectId: string; chapterId: string | null }> = [];
    await page.route('**/api/activity', async (route) => {
        if (route.request().method() === 'POST') {
            pings.push(route.request().postDataJSON());
            await route.fulfill({ status: 204 });
        } else {
            await route.continue();
        }
    });
    return pings;
}

async function focusEmulation(page: Page) {
    const cdp = await page.context().newCDPSession(page);
    await cdp.send('Emulation.setFocusEmulationEnabled', { enabled: true });
}

// pings are answered by this test's route handler asynchronously: give the ones sent by the last runFor time to arrive (the fake clock is paused, real time is not)
async function seen(page: Page, pings: unknown[]) {
    await page.waitForTimeout(300);
    return pings.length;
}

async function userAction(page: Page) {
    await page.keyboard.press('Shift'); // keydown on the document
}

// The first 30 s tick after setup is not predictable, so pings are counted over whole ranges.
async function openWithClock(page: Page, request: APIRequestContext, title: string) {
    await focusEmulation(page);
    await page.clock.install();
    const pings = await recordPings(page);
    await openFirstChapter(page, title);
    await page.clock.pauseAt(new Date(Date.now() + 5_000));
    expect(await page.evaluate(() => document.hasFocus() && document.visibilityState === 'visible')).toBe(true);
    return pings;
}

test.describe('heartbeat', () => {
    test('pings the open project and chapter every 30 s while the user is active', async ({ page, request }) => {
        test.setTimeout(120_000);
        const title = `Activity ${Date.now()}`;
        const project = await createProject(request, title);
        try {
            const pings = await openWithClock(page, request, title);
            await userAction(page);
            await page.clock.runFor(31_000);
            expect(await seen(page, pings)).toBe(1);
            expect(pings[0].projectId).toBe(project.projectId);
            expect(typeof pings[0].chapterId).toBe('string');
            expect(Object.keys(pings[0]).sort()).toEqual(['chapterId', 'projectId']); // no client time, no text
            await userAction(page);
            await page.clock.runFor(30_000);
            expect(await seen(page, pings)).toBe(2);
        } finally {
            await request.delete(`/api/projects/${project.projectId}`);
        }
    });

    test('no pings from a background tab, an unfocused window, or the project list', async ({ page, request }) => {
        test.setTimeout(120_000);
        const title = `Activity bg ${Date.now()}`;
        const project = await createProject(request, title);
        try {
            const pings = await openWithClock(page, request, title);
            const setState = (visibility: string, focused: boolean) => page.evaluate(([v, f]) => {
                Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => v });
                document.hasFocus = () => f as boolean;
            }, [visibility, focused] as const);

            await setState('hidden', true);
            await userAction(page);
            await page.clock.runFor(95_000);
            expect(await seen(page, pings)).toBe(0);

            await setState('visible', false);
            await userAction(page);
            await page.clock.runFor(65_000);
            expect(await seen(page, pings)).toBe(0);

            await setState('visible', true);
            await userAction(page);
            await page.clock.runFor(31_000);
            expect(await seen(page, pings)).toBe(1); // back in the foreground: counting resumes

            // the project list is not a project workspace
            await page.locator('#back-to-projects').click();
            await expect(page.locator('#project-workspace-view')).toBeHidden();
            await userAction(page);
            await page.clock.runFor(95_000);
            expect(await seen(page, pings)).toBe(1);
        } finally {
            await request.delete(`/api/projects/${project.projectId}`);
        }
    });

    test('stops after 90 s without an action and resumes with the next one', async ({ page, request }) => {
        test.setTimeout(120_000);
        const title = `Activity idle ${Date.now()}`;
        const project = await createProject(request, title);
        try {
            const pings = await openWithClock(page, request, title);
            await userAction(page);
            await page.clock.runFor(100_000);
            const whileActive = await seen(page, pings);
            expect(whileActive).toBeGreaterThanOrEqual(2);
            expect(whileActive).toBeLessThanOrEqual(3); // ticks inside the 90 s after the action
            await page.clock.runFor(120_000);           // idle: nothing more
            expect(await seen(page, pings)).toBe(whileActive);
            await page.mouse.move(5, 5);                // a move is not an action
            await page.clock.runFor(60_000);
            expect(await seen(page, pings)).toBe(whileActive);
            await page.mouse.click(5, 5);               // pointerdown is
            await page.clock.runFor(31_000);
            expect(await seen(page, pings)).toBe(whileActive + 1);
        } finally {
            await request.delete(`/api/projects/${project.projectId}`);
        }
    });

    test('a failing ping is dropped silently: no message, no retry', async ({ page, request }) => {
        test.setTimeout(120_000);
        const title = `Activity fail ${Date.now()}`;
        const project = await createProject(request, title);
        try {
            await focusEmulation(page);
            await page.clock.install();
            let attempts = 0;
            await page.route('**/api/activity', async (route) => {
                if (route.request().method() !== 'POST') return route.continue();
                attempts += 1;
                return route.abort('failed');
            });
            const dialogs: string[] = [];
            page.on('dialog', (dialog) => { dialogs.push(dialog.message()); void dialog.dismiss(); });
            await openFirstChapter(page, title);
            await page.clock.pauseAt(new Date(Date.now() + 5_000));
            await userAction(page);
            await page.clock.runFor(31_000);
            await page.waitForTimeout(300);
            expect(attempts).toBe(1);
            await page.clock.runFor(10_000); // no retry in between
            await page.waitForTimeout(300);
            expect(attempts).toBe(1);
            expect(dialogs).toEqual([]);
            await expect(page.locator('[role="alert"]:visible')).toHaveCount(0);
        } finally {
            await request.delete(`/api/projects/${project.projectId}`);
        }
    });
});

for (const [width, height] of [[1280, 900], [390, 844]] as const) {
    test(`«Час роботи» in the cost window at ${width}×${height}`, async ({ page, request }) => {
        test.setTimeout(120_000);
        await page.setViewportSize({ width, height });
        const title = `Activity stats ${width} ${Date.now()}`;
        const project = await createProject(request, title);
        try {
            const structure = await (await request.get(`/api/projects/${project.projectId}/book/structure`)).json();
            const chapter = structure.chapters[0];
            for (let i = 0; i < 3; i += 1) {
                // the real server clock: three pings in one minute are still one row
                expect((await request.post('/api/activity', { data: { projectId: project.projectId, chapterId: chapter.chapterId } })).status()).toBe(204);
            }
            await openFirstChapter(page, title);
            await page.locator('#project-cost-button').click();
            const dialog = page.locator('#project-cost-dialog');
            await dialog.getByRole('tab', { name: 'Час роботи' }).click();
            await expect(dialog.getByRole('tab', { name: 'Час роботи' })).toHaveAttribute('aria-selected', 'true');
            const view = dialog.locator('.activity-usage');
            await expect(view.locator('.activity-summary')).toContainText('Разом:');
            expect(await view.locator('.activity-summary').innerText()).toMatch(/^Разом: [12] хв$/); // one minute, or two if the minute turned
            await expect(view.locator('.daily-bar')).toHaveCount(1);
            await expect(view.locator('.activity-books-table')).toContainText(title);
            await expect(view.locator('.activity-chapters-table')).toContainText(chapter.title);
            await expect(view.getByRole('button', { name: '7 днів' })).toHaveAttribute('aria-pressed', 'true');
            await view.getByRole('button', { name: '30 днів' }).click();
            await expect(view.getByRole('button', { name: '30 днів' })).toHaveAttribute('aria-pressed', 'true');
            await expect(view.locator('.activity-export')).toHaveAttribute('href', /\/api\/activity\/export\?days=30$/);
            await view.locator('.activity-scope').selectOption({ label: 'Ця книга' });
            await expect(view.locator('.activity-export')).toHaveAttribute('href', new RegExp(`projectId=${project.projectId}`));
            const csv = await request.get(`/api/activity/export?days=7&projectId=${project.projectId}`);
            expect(csv.headers()['content-type']).toContain('text/csv');
            expect(await csv.text()).toContain(title);
            // fits the screen, targets are at least 44 px
            const box = await dialog.locator('.project-cost-content').boundingBox();
            expect((box?.x ?? 0) + (box?.width ?? 0)).toBeLessThanOrEqual(width);
            for (const control of await dialog.locator('.project-cost-tab:visible, .daily-range-button:visible, .activity-scope:visible').all()) {
                expect((await control.boundingBox())?.height ?? 0).toBeGreaterThanOrEqual(44);
            }
            expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
        } finally {
            await request.delete(`/api/projects/${project.projectId}`);
        }
    });
}
