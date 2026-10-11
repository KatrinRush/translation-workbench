import { expect, test, type Page, type APIRequestContext } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// Connections are mocked at the network layer: the e2e server may run without a
// credential vault, and the test must never touch real connections in the local DB.
const CLAUDE_CONNECTION = {
    connectionId: 'connection-e2e-claude',
    providerId: 'claude',
    displayName: 'Claude e2e',
    enabled: true,
    status: 'connected',
};

async function createProjectWithBook(request: APIRequestContext, title: string) {
    const createResponse = await request.post('/api/projects', { data: { title, status: 'translation' } });
    expect(createResponse.ok()).toBeTruthy();
    const project = await createResponse.json();
    const epubPath = path.join(__dirname, '..', 'test-data', 'sample-without-cover.epub');
    const uploadResponse = await request.post('/upload', {
        headers: { 'X-Project-Id': project.projectId },
        multipart: {
            file: { name: 'sample-without-cover.epub', mimeType: 'application/epub+zip', buffer: fs.readFileSync(epubPath) },
        },
    });
    expect(uploadResponse.ok()).toBeTruthy();
    return project;
}

async function openFirstChapter(page: Page, title: string) {
    await page.goto('/');
    await page.locator('.project-card').filter({ hasText: title }).getByRole('button', { name: 'Відкрити проєкт' }).click();
    await page.getByRole('button', { name: 'Переклад', exact: true }).click();
    await page.getByRole('button', { name: 'Переглянути структуру книги' }).click();
    await page.locator('.chapter-button').first().click();
}

test.describe('Translation provider toggle', () => {
    test('defaults to DeepL and explains where to add a missing Claude connection', async ({ page, request }) => {
        const title = `Provider toggle empty ${Date.now()}`;
        const project = await createProjectWithBook(request, title);
        await page.route('**/api/connections', (route) => route.fulfill({ json: [] }));
        const projectWrites: string[] = [];
        page.on('request', (item) => {
            if (item.method() === 'PUT' && item.url().endsWith(`/api/projects/${project.projectId}`)) {
                projectWrites.push(item.url());
            }
        });

        try {
            await openFirstChapter(page, title);
            const toggle = page.locator('#translation-provider-toggle');
            await expect(toggle.getByLabel('DeepL')).toBeChecked();
            await expect(page.locator('.translate-paragraph-button').first()).toHaveText('Перекласти DeepL');

            await toggle.getByText('Claude').click();

            const hint = page.locator('#translation-provider-hint');
            await expect(hint).toBeVisible();
            await expect(hint).toContainText('Немає підключення Claude');
            await expect(hint).toContainText('Connections');
            await expect(toggle.getByLabel('DeepL')).toBeChecked();
            expect(projectWrites).toEqual([]);

            await hint.getByRole('button', { name: 'Відкрити Connections' }).click();
            await expect(page.locator('#connections-title')).toBeVisible();
        } finally {
            await request.delete(`/api/projects/${project.projectId}`);
        }
    });

    test('switching to Claude is saved on the project, synced with settings and drives batched translation', async ({ page, request }) => {
        const title = `Provider toggle claude ${Date.now()}`;
        const project = await createProjectWithBook(request, title);
        let savedProject = { ...project, aiConfiguration: {} };
        const projectBodies: any[] = [];
        const translateBodies: any[] = [];

        await page.route('**/api/connections', (route) => route.fulfill({ json: [CLAUDE_CONNECTION] }));
        await page.route(`**/api/projects/${project.projectId}`, async (route) => {
            if (route.request().method() !== 'PUT') {
                return route.fallback();
            }
            const body = route.request().postDataJSON();
            projectBodies.push(body);
            savedProject = { ...savedProject, ...body };
            return route.fulfill({ json: savedProject });
        });
        await page.route('**/chapters/*/translate', async (route) => {
            const body = route.request().postDataJSON();
            translateBodies.push(body);
            const structure = await (await request.get(`/api/projects/${project.projectId}/book/structure`)).json();
            const paragraphIds = structure.chapters[0].elements
                .filter((element: any) => element.type === 'paragraph')
                .map((element: any) => element.paragraphId);
            const batch = body.batchIndex === 0 ? paragraphIds.slice(0, 1) : paragraphIds.slice(1, 2);
            return route.fulfill({
                json: {
                    providerId: 'claude',
                    connectionId: CLAUDE_CONNECTION.connectionId,
                    batchIndex: body.batchIndex,
                    totalBatches: 2,
                    paragraphs: batch.map((paragraphId: string) => ({
                        paragraphId,
                        translationText: `Claude ${body.batchIndex}`,
                        reviewed: false,
                    })),
                },
            });
        });

        try {
            await openFirstChapter(page, title);
            const toggle = page.locator('#translation-provider-toggle');
            await toggle.getByText('Claude').click();

            await expect.poll(() => projectBodies.length).toBe(1);
            expect(projectBodies[0].aiConfiguration.translationConnectionId).toBe(CLAUDE_CONNECTION.connectionId);
            await expect(toggle.getByLabel('Claude')).toBeChecked();
            await expect(page.locator('#translation-provider-hint')).toBeHidden();
            await expect(page.locator('.translate-paragraph-button').first()).toHaveText('Перекласти Claude');

            await page.locator('#translate-chapter-button').click();
            await expect.poll(() => translateBodies.map((body) => body.batchIndex)).toEqual([0, 1]);
            await expect(page.locator('.translation-paragraph').filter({ hasText: 'Claude 0' })).toHaveCount(1);
            await expect(page.locator('.translation-paragraph').filter({ hasText: 'Claude 1' })).toHaveCount(1);
            await expect(page.locator('#translate-chapter-button')).toBeEnabled();

            await page.getByRole('button', { name: 'Інформація про проєкт' }).click();
            await page.locator('#edit-current-project').click();
            await expect(page.locator('#project-translation-connection')).toHaveValue(CLAUDE_CONNECTION.connectionId);
            await expect(page.locator('#project-translation-connection option')).toHaveText(['DeepL (за замовчуванням)', /Claude e2e/]);
        } finally {
            await request.delete(`/api/projects/${project.projectId}`);
        }
    });
});
