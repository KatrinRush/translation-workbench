import { expect, test } from '@playwright/test';


test.describe('Projects list', () => {
    test('renders project metadata and opens the full project detail', async ({ page, request }) => {
        const title = `Projects summary ${Date.now()}`;
        const createResponse = await request.post('/api/projects', {
            data: {
                title,
                authorId: null,
                seriesId: null,
                status: 'analysis',
                analysisResult: { marker: 'detail-only' },
            },
        });
        expect(createResponse.ok()).toBeTruthy();
        const project = await createResponse.json();

        try {
            await page.goto('/');
            const card = page.locator('.project-card').filter({ hasText: title });
            await expect(card).toBeVisible();
            await expect(card).toContainText('Аналіз');

            await card.getByRole('button', { name: 'Відкрити проєкт' }).click();

            await expect(page.locator('#project-page-title')).toHaveText(title);
            const detailResponse = await request.get(`/api/projects/${project.projectId}`);
            expect(detailResponse.ok()).toBeTruthy();
            expect((await detailResponse.json()).analysisResult).toEqual({ marker: 'detail-only' });
        } finally {
            await request.delete(`/api/projects/${project.projectId}`);
        }
    });
});