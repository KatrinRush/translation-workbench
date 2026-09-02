import { test, expect } from '@playwright/test';

test.describe('chapter AI analysis result windows', () => {
    test('renders one isolated window per provider result', async ({ page }) => {
        await page.goto('/');

        const renderResults = async (results: Record<string, object>, selectedProviders = Object.keys(results)) => {
            await page.evaluate((value) => {
                window.renderChapterAIAnalysisResults(value.results, new Set(value.selectedProviders));
            }, { results, selectedProviders });
            const windows = page.locator('#chapter-ai-analysis-results > .chapter-ai-analysis-result');
            return {
                count: await windows.count(),
                providers: await windows.evaluateAll((items) => items.map((item) => item.dataset.providerId)),
                headings: await windows.locator('h5').allTextContents(),
                texts: await windows.locator('pre').allTextContents(),
            };
        };

        expect(await renderResults({})).toEqual({ count: 0, providers: [], headings: [], texts: [] });
        expect(await renderResults({
            claude: { providerId: 'claude', status: 'completed', text: 'Claude result' },
            gemini: { providerId: 'gemini', status: 'completed', text: 'Gemini result' },
            openai: { providerId: 'openai', status: 'completed', text: 'GPT result' },
        }, ['claude'])).toEqual({
            count: 1,
            providers: ['claude'],
            headings: ['Claude'],
            texts: ['Claude result'],
        });
        expect(await renderResults({
            claude: { providerId: 'claude', status: 'completed', text: 'Claude result' },
            gemini: { providerId: 'gemini', status: 'completed', text: 'Gemini result' },
            openai: { providerId: 'openai', status: 'completed', text: 'GPT result' },
        }, ['claude', 'gemini'])).toEqual({
            count: 2,
            providers: ['claude', 'gemini'],
            headings: ['Claude', 'Gemini'],
            texts: ['Claude result', 'Gemini result'],
        });
        expect(await renderResults({
            claude: { providerId: 'claude', status: 'completed', text: 'Claude result' },
            gemini: { providerId: 'gemini', status: 'completed', text: 'Gemini result' },
            openai: { providerId: 'openai', status: 'completed', text: 'GPT result' },
        })).toEqual({
            count: 3,
            providers: ['claude', 'gemini', 'openai'],
            headings: ['Claude', 'Gemini', 'GPT'],
            texts: ['Claude result', 'Gemini result', 'GPT result'],
        });
    });

    test('removes a result window when its model is deselected', async ({ page }) => {
        await page.goto('/');
        await page.evaluate(() => {
            window.renderChapterAIAnalysisResults({
                claude: { providerId: 'claude', status: 'completed', text: 'Claude text' },
                gemini: { providerId: 'gemini', status: 'completed', text: 'Gemini text' },
                openai: { providerId: 'openai', status: 'completed', text: 'GPT text' },
            }, new Set(['claude', 'gemini', 'openai']));
        });
        await page.evaluate(() => window.renderChapterAIAnalysisResults({
            claude: { providerId: 'claude', status: 'completed', text: 'Claude text' },
            gemini: { providerId: 'gemini', status: 'completed', text: 'Gemini text' },
            openai: { providerId: 'openai', status: 'completed', text: 'GPT text' },
        }, new Set(['claude', 'gemini'])));
        await expect(page.locator('#chapter-ai-analysis-results > section')).toHaveCount(2);
        await expect(page.locator('#chapter-ai-analysis-results')).toContainText('Gemini text');
        await expect(page.locator('#chapter-ai-analysis-results')).toContainText('Claude text');
        await expect(page.locator('#chapter-ai-analysis-results')).not.toContainText('GPT text');
    });
});