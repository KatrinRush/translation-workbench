import { expect, test } from '@playwright/test';

test.describe('Glossary catalog picker', () => {
    test('groups catalog entries by series/author, collapses non-priority groups, and adds a term on click', async ({ page, request }) => {
        const stamp = Date.now();
        const author = await (await request.post('/api/authors', { data: { name: `Author ${stamp}` } })).json();
        const currentSeries = await (await request.post('/api/series', { data: { name: `Current Series ${stamp}` } })).json();
        const otherSeries = await (await request.post('/api/series', { data: { name: `Other Series ${stamp}` } })).json();

        const currentSeriesEntry = await (await request.post('/api/glossary', {
            data: { source: `wraith-${stamp}`, target: 'привид' },
        })).json();
        const otherSeriesEntry = await (await request.post('/api/glossary', {
            data: { source: `ghoul-${stamp}`, target: 'вурдалак' },
        })).json();
        const orphanEntry = await (await request.post('/api/glossary', {
            data: { source: `imp-${stamp}`, target: 'біс' },
        })).json();

        const currentProject = await (await request.post('/api/projects', {
            data: {
                title: `Fool Me Once ${stamp}`,
                authorId: author.authorId,
                seriesId: currentSeries.seriesId,
                status: 'translation',
                projectGlossaryEntryIds: [currentSeriesEntry.glossaryEntryId],
            },
        })).json();
        const otherProject = await (await request.post('/api/projects', {
            data: {
                title: `Other Book ${stamp}`,
                authorId: author.authorId,
                seriesId: otherSeries.seriesId,
                status: 'translation',
                projectGlossaryEntryIds: [otherSeriesEntry.glossaryEntryId],
            },
        })).json();

        try {
            await page.goto('/');
            const card = page.locator('.project-card').filter({ hasText: currentProject.title });
            await card.getByRole('button', { name: 'Відкрити проєкт' }).click();
            await expect(page.locator('#project-page-title')).toHaveText(currentProject.title);

            await page.getByRole('button', { name: 'Переклад', exact: true }).click();
            await page.getByRole('button', { name: 'Структуровані правила' }).click();
            await page.getByRole('button', { name: '＋ Додати правило' }).click();
            await page.locator('#translation-glossary-editor-toggle').click();

            await page.getByRole('button', { name: 'Додати з довідника' }).click();
            const dialog = page.locator('#glossary-catalog-dialog');
            await expect(dialog).toBeVisible();

            const groups = dialog.locator('.glossary-catalog-group');
            const currentGroup = groups.filter({ has: page.locator('.glossary-catalog-group-current') }).first();
            const currentGroupHeader = dialog.locator('.glossary-catalog-group-current .glossary-catalog-group-header');
            await expect(currentGroupHeader).toContainText('З цієї серії');
            await expect(currentGroupHeader).toHaveAttribute('aria-expanded', 'true');

            const currentTerm = dialog.locator('.glossary-catalog-group-current .glossary-catalog-term', { hasText: `wraith-${stamp}` });
            await expect(currentTerm).toBeVisible();
            await expect(currentTerm).toContainText(`${currentSeries.name} / ${currentProject.title}`);

            // Other groups (a different series, and "Без прив'язки") start collapsed.
            const otherSeriesHeader = dialog.locator('.glossary-catalog-group-header', { hasText: otherSeries.name });
            await expect(otherSeriesHeader).toHaveAttribute('aria-expanded', 'false');
            const otherSeriesTerm = dialog.locator('.glossary-catalog-term', { hasText: `ghoul-${stamp}` });
            await expect(otherSeriesTerm).toBeHidden();

            await otherSeriesHeader.click();
            await expect(otherSeriesHeader).toHaveAttribute('aria-expanded', 'true');
            await expect(otherSeriesTerm).toBeVisible();
            await expect(otherSeriesTerm).toContainText(`${otherSeries.name} / ${otherProject.title}`);

            const orphanHeader = dialog.locator('.glossary-catalog-group-header', { hasText: 'Без прив’язки' });
            await expect(orphanHeader).toHaveAttribute('aria-expanded', 'false');
            const orphanTerm = dialog.locator('.glossary-catalog-term', { hasText: `imp-${stamp}` });
            await expect(orphanTerm).toBeHidden();
            await orphanHeader.click();
            await expect(orphanTerm).toBeVisible();
            await expect(orphanTerm).not.toContainText('—');

            // Clicking a term adds it to the project's translation glossary draft and the
            // dialog stays open (so several terms can be added one after another).
            await currentTerm.click();
            await expect(dialog).toBeVisible();
            await expect(currentTerm).toHaveCount(0);
            await expect(page.locator('.translation-glossary-card-title', { hasText: `wraith-${stamp}` })).toBeVisible();

            await page.locator('#close-glossary-catalog-dialog').click();
            await expect(dialog).toBeHidden();

            await page.screenshot({ path: 'test-results/glossary-catalog-dialog.png' });
        } finally {
            await request.delete(`/api/projects/${currentProject.projectId}`);
            await request.delete(`/api/projects/${otherProject.projectId}`);
            await request.delete(`/api/glossary/${currentSeriesEntry.glossaryEntryId}`);
            await request.delete(`/api/glossary/${otherSeriesEntry.glossaryEntryId}`);
            await request.delete(`/api/glossary/${orphanEntry.glossaryEntryId}`);
            await request.delete(`/api/series/${currentSeries.seriesId}`);
            await request.delete(`/api/series/${otherSeries.seriesId}`);
            await request.delete(`/api/authors/${author.authorId}`);
        }
    });
});
