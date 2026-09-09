import { expect, test } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';


test('chapter export flag auto-saves and both DOCX formats download', async ({ page, request }) => {
    const title = `DOCX export ${Date.now()}`;
    const createResponse = await request.post('/api/projects', {
        data: { title, status: 'translation' },
    });
    expect(createResponse.ok()).toBeTruthy();
    const project = await createResponse.json();

    try {
        const epubPath = path.join(__dirname, '..', 'test-data', 'sample-without-cover.epub');
        const uploadResponse = await request.post('/upload', {
            headers: { 'X-Project-Id': project.projectId },
            multipart: {
                file: {
                    name: 'sample-without-cover.epub',
                    mimeType: 'application/epub+zip',
                    buffer: fs.readFileSync(epubPath),
                },
            },
        });
        expect(uploadResponse.ok()).toBeTruthy();

        await page.goto('/');
        await page.locator('.project-card').filter({ hasText: title }).getByRole('button', { name: 'Відкрити проєкт' }).click();
        await page.getByRole('button', { name: 'Переклад', exact: true }).click();
        await page.getByRole('button', { name: 'Переглянути структуру книги' }).click();
        await page.locator('.chapter-button').first().click();

        const exportCheckbox = page.locator('.chapter-export-toggle input').first();
        await expect(exportCheckbox).toBeVisible();
        await exportCheckbox.check();
        await expect(page.locator('.chapter-button').first()).toHaveClass(/excluded-from-export/);
        await expect.poll(async () => {
            const response = await request.get(`/api/projects/${project.projectId}/book/structure`);
            return (await response.json()).chapters[0].excludeFromExport;
        }).toBe(true);

        for (const buttonName of [
            'Завантажити .docx (оригінал + переклад)',
            'Завантажити .docx (тільки переклад)',
        ]) {
            const downloadPromise = page.waitForEvent('download');
            await page.getByRole('button', { name: buttonName }).click();
            const download = await downloadPromise;
            expect(download.suggestedFilename()).toMatch(/\.docx$/);
            const stream = await download.createReadStream();
            const chunks: Buffer[] = [];
            for await (const chunk of stream) chunks.push(Buffer.from(chunk));
            expect(Buffer.concat(chunks).subarray(0, 2).toString()).toBe('PK');
        }
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
    }
});
