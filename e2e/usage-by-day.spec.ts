import { expect, test, type APIRequestContext, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// «По днях» in the project's «Вартість» dialog, Settings → «Витрати», and the price refresh.
// e2e/server.py answers every LLM call with 10 input / 5 output tokens and serves a small fixed
// price list (no network). Needs WORKBENCH_CREDENTIALS_KEY.

const SEED = [
    { model: 'claude-sonnet-5-5', inputPerMTok: 2, outputPerMTok: 10, cacheReadPerMTok: 0.2, cacheWritePerMTok: 2.5 },
    { model: 'gpt-5.5', inputPerMTok: 5, outputPerMTok: 30, cacheReadPerMTok: null, cacheWritePerMTok: null },
    { model: 'gemini-3.6-flash', inputPerMTok: 1.5, outputPerMTok: 7.5, cacheReadPerMTok: null, cacheWritePerMTok: null },
];

async function resetPrices(request: APIRequestContext) {
    // Back to the initial table whatever a test did: delete the initial models and restore them.
    await request.put('/api/model-prices', { data: { prices: [...SEED.map(({ model }) => ({ model })), { model: 'e2e-custom-model' }, { model: 'gpt-4.1-nano' }] } });
    await request.post('/api/model-prices/restore-defaults', { data: {} });
}

async function createProjectWithBook(request: APIRequestContext, title: string) {
    const created = await request.post('/api/projects', { data: { title, status: 'translation' } });
    expect(created.ok()).toBeTruthy();
    const project = await created.json();
    const epubPath = path.join(__dirname, '..', 'test-data', 'sample-without-cover.epub');
    const upload = await request.post('/upload', {
        headers: { 'X-Project-Id': project.projectId },
        multipart: { file: { name: 'sample-without-cover.epub', mimeType: 'application/epub+zip', buffer: fs.readFileSync(epubPath) } },
    });
    expect(upload.ok()).toBeTruthy();
    return project;
}

async function createConnection(request: APIRequestContext, providerId: string) {
    const response = await request.post('/api/connections', {
        data: { providerId, displayName: `${providerId} days e2e`, credentials: { apiKey: `${providerId}-e2e-key` } },
    });
    expect(response.ok(), await response.text()).toBeTruthy();
    const connection = await response.json();
    expect((await request.post(`/api/connections/${connection.connectionId}/test`)).ok()).toBeTruthy();
    return connection;
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

async function translateChapter(page: Page, engine: string) {
    const toggle = page.locator('#translation-provider-toggle');
    await toggle.getByText(engine, { exact: true }).click();
    await expect(toggle.getByLabel(engine)).toBeChecked();
    const button = page.locator('#translate-chapter-button');
    await button.click();
    await expect(button).toHaveText('Перекласти розділ');
    await expect(button).toBeEnabled();
}

const kyivDay = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'Europe/Kyiv' }).format(new Date());

test('«По днях»: table, chart, range, breakdowns, calls without a price and the CSV', async ({ page, request }) => {
    test.setTimeout(90_000);
    await resetPrices(request); // gpt-4.1-nano (what the fake GPT answers as) has no price
    const title = `Days ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    const connections = [await createConnection(request, 'claude'), await createConnection(request, 'openai')];
    try {
        await openFirstChapter(page, title);
        const dayBefore = kyivDay();
        await translateChapter(page, 'Claude');
        await translateChapter(page, 'GPT');
        const dayAfter = kyivDay();

        await page.locator('#project-cost-button').click();
        const dialog = page.locator('#project-cost-dialog');
        await expect(dialog.getByRole('tab', { name: 'Загалом' })).toHaveAttribute('aria-selected', 'true');
        await dialog.getByRole('tab', { name: 'По днях' }).click();
        const days = page.locator('#project-cost-days');
        await expect(days).toBeVisible();
        await expect(days.locator('.daily-range-button[aria-pressed="true"]')).toHaveText('7 днів');

        // today's row (Europe/Kyiv): two calls; one has no price, so the sum is marked incomplete
        const row = days.locator('.daily-usage-table tbody tr[data-date]').first();
        await expect(row).toBeVisible();
        const date = await row.getAttribute('data-date');
        expect([dayBefore, dayAfter]).toContain(date);
        await expect(row).toContainText('≥ $0.0001 + 1 виклик без ціни'); // Claude: 10 in + 5 out; GPT has no price
        await expect(row.locator('td').nth(2)).toHaveText('20'); // input tokens: 2 × 10
        await expect(row.locator('td').nth(3)).toHaveText('10');
        await expect(row.locator('td').nth(5)).toHaveText('2');
        await expect(days.locator('.daily-usage-summary')).toContainText('⚠ 1 виклик без ціни — сума неповна (gpt-4.1-nano)');
        await expect(days.locator('.daily-usage-note')).toContainText('Europe/Kyiv');

        // chart: one bar for today, hatched/different colour because the day is incomplete
        const bar = days.locator('.daily-chart-svg .daily-bar-incomplete');
        await expect(bar).toHaveCount(1);
        await expect(days.locator('.daily-chart-svg')).toHaveAttribute('role', 'img');
        await expect(days.locator('.daily-chart-svg rect[data-date]')).toHaveCount(1);

        // breakdown by engine and by kind of call, also per day
        await expect(days.locator('.daily-breakdown')).toContainText('claude');
        await expect(days.locator('.daily-breakdown')).toContainText('openai');
        await expect(days.locator('.daily-breakdown')).toContainText('Переклад');
        await row.getByRole('button', { name: date! }).click();
        await expect(days.locator('.daily-detail')).toContainText('Рушії — ');

        // range 30 / 90 keep the same totals and add empty days only
        await days.getByRole('button', { name: '30 днів' }).click();
        await expect(days.locator('.daily-range-button[aria-pressed="true"]')).toHaveText('30 днів');
        await expect(days.locator('.daily-usage-table tbody tr[data-date]')).toHaveCount(1);
        await expect(days.locator('.daily-chart-svg title')).toHaveCount(1); // only the day with a bar has a title
        await days.getByRole('button', { name: '90 днів' }).click();
        await expect(days.locator('.daily-usage-note')).toContainText(/\d{4}-\d{2}-\d{2} — \d{4}-\d{2}-\d{2}/);

        // CSV for the selected range: counts and names only
        const href = await days.getByRole('link', { name: 'Експорт CSV' }).getAttribute('href');
        expect(href).toContain('days=90');
        const csv = await request.get(href!);
        expect(csv.ok()).toBeTruthy();
        expect(csv.headers()['content-type']).toContain('text/csv');
        expect(csv.headers()['content-disposition']).toContain('usage-');
        const text = await csv.text();
        expect(text).toContain('date,project,engine,model,kind,calls,input_tokens,output_tokens');
        expect(text).toContain(`${title},claude,claude-sonnet-5-5,translate,1,10,5`);
        expect(text).toContain(`${title},openai,gpt-4.1-nano,translate,1,10,5,0,0,,no price`);
        expect(text).not.toContain('This is a test EPUB');
        expect((await request.get('/api/usage/export.csv?days=8')).status()).toBe(400);

        // «Загалом» is still there
        await dialog.getByRole('tab', { name: 'Загалом' }).click();
        await expect(dialog.locator('.project-cost-total')).toContainText('2 виклики');
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
        for (const connection of connections) await request.delete(`/api/connections/${connection.connectionId}`);
        await resetPrices(request);
    }
});

test('Settings → «Витрати»: all projects or one, time zone', async ({ page, request }) => {
    test.setTimeout(60_000);
    await resetPrices(request);
    const title = `Usage settings ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    const connection = await createConnection(request, 'claude');
    try {
        await openFirstChapter(page, title);
        await translateChapter(page, 'Claude');
        await page.goto('/');
        await page.getByRole('button', { name: /Налаштування/ }).first().click();
        const section = page.locator('#usage-settings-section');
        await expect(section).toBeVisible();
        await expect(section.locator('.daily-usage-summary')).not.toHaveText('Завантажуємо…');
        await section.locator('#usage-settings-project').selectOption({ label: title });
        await expect(section.locator('.daily-usage-summary')).toContainText('1 виклик · 15 токенів');
        await expect(section.locator('.daily-usage-table tbody tr[data-date]')).toHaveCount(1);
        await section.locator('#usage-settings-project').selectOption('');
        await expect(section.locator('.daily-usage-summary')).toContainText('токенів');

        // a time zone that does not exist is refused, a valid one is saved and the days are recounted
        await section.locator('#usage-settings-timezone').fill('Mars/Phobos');
        await section.getByRole('button', { name: 'Застосувати пояс' }).click();
        await expect(section.locator('#usage-settings-status')).toContainText('Невідомий часовий пояс');
        await section.locator('#usage-settings-timezone').fill('Pacific/Kiritimati');
        await section.getByRole('button', { name: 'Застосувати пояс' }).click();
        await expect(section.locator('#usage-settings-status')).toContainText('Дні перераховано, дані не змінено');
        await expect(section.locator('.daily-usage-note')).toContainText('Pacific/Kiritimati');
        expect((await (await request.get('/api/settings')).json()).timezone).toBe('Pacific/Kiritimati');
    } finally {
        await request.put('/api/settings', { data: { timezone: 'Europe/Kyiv' } });
        await request.delete(`/api/projects/${project.projectId}`);
        await request.delete(`/api/connections/${connection.connectionId}`);
        await resetPrices(request);
    }
});

test('«Оновити ціни»: comparison, which key matched, warnings, manual edits, deleting and restoring', async ({ page, request }) => {
    test.setTimeout(90_000);
    await resetPrices(request);
    const title = `Price refresh ${Date.now()}`;
    const project = await createProjectWithBook(request, title);
    try {
        // Manual edits: Claude is 4x off the list (suspicious) and a custom model is not in the list.
        await request.put('/api/model-prices', { data: { prices: [
            { model: 'claude-sonnet-5-5', inputPerMTok: 0.5, outputPerMTok: 10, cacheReadPerMTok: 0.2, cacheWritePerMTok: 2.5 },
            { model: 'e2e-custom-model', inputPerMTok: 1, outputPerMTok: 2 },
        ] } });
        await openFirstChapter(page, title);
        await page.locator('#translation-settings-button').click();
        const settings = page.locator('#translation-settings-dialog');
        await expect(settings.locator('.model-price-row[aria-label="gemini-3.6-flash"] .model-price-origin')).toContainText('початкова');
        await expect(settings.locator('.model-price-row[aria-label="claude-sonnet-5-5"] .model-price-origin')).toContainText('вручну');
        await expect(settings.locator('#model-prices-status')).toContainText(/Ціни/); // «ще не оновлювались» or the date of the last update (global state)

        await settings.getByRole('button', { name: 'Оновити ціни' }).click();
        const panel = settings.locator('#price-refresh-panel');
        await expect(panel).toBeVisible();
        await expect(panel).toContainText('список LiteLLM');
        await expect(panel).toContainText('Нічого не змінено, доки ви не підтвердите');

        // Gemini: the Gemini API key is preferred over the bare (Vertex) one; listed with was → will be
        const gemini = panel.locator('.price-comparison-row[data-model="gemini-3.6-flash"]');
        await expect(gemini).toContainText('вхід 1.5 → 0.75');
        await expect(gemini).toContainText('вихід 7.5 → 3.75');
        await expect(gemini).toContainText('збіг: gemini/gemini-3.6-flash');
        await expect(gemini.locator('.price-comparison-select')).toBeChecked();
        // GPT: only the exact name matches (gpt-5.5-pro is a different model)
        const gpt = panel.locator('.price-comparison-row[data-model="gpt-5.5"]');
        await expect(gpt).toContainText('збіг: gpt-5.5');
        await expect(gpt).not.toContainText('gpt-5.5-pro');
        // Claude: more than twice off -> warning, not selected; it is also a manual edit
        const claude = panel.locator('.price-comparison-row[data-model="claude-sonnet-5-5"]');
        await expect(claude).toContainText('більш ніж удвічі');
        await expect(claude).toContainText('ручна правка');
        await expect(claude.locator('.price-comparison-select')).not.toBeChecked();
        await expect(panel.locator('.price-comparison-row[data-model="e2e-custom-model"]')).toContainText('немає в списку');
        await expect(panel.locator('.price-comparison-row[data-model="e2e-custom-model"] input')).toBeDisabled();

        // Apply the defaults (Gemini and GPT); nothing was written before this click
        await panel.getByRole('button', { name: 'Застосувати вибране' }).click();
        await expect(panel).toBeHidden();
        await expect(settings.locator('#model-prices-status')).toContainText('застосовано: 2');
        await expect(settings.locator('#model-prices-status')).toContainText('джерело: список LiteLLM');
        await expect(settings.locator('.model-price-row[aria-label="gemini-3.6-flash"] .model-price-origin')).toContainText('зі списку');
        await expect(settings.getByLabel('Вхід · gemini-3.6-flash')).toHaveValue('0.75');
        await expect(settings.getByLabel('Читання кешу · gemini-3.6-flash')).toHaveValue('0.075');
        const prices = (await (await request.get('/api/model-prices')).json()).prices;
        expect(prices.find((item: any) => item.model === 'claude-sonnet-5-5')).toMatchObject({ inputPerMTok: 0.5, source: 'manual' }); // untouched

        // A manual price is skipped unless «Перезаписати й ручні» is ticked
        await settings.getByRole('button', { name: 'Оновити ціни' }).click();
        await expect(panel.locator('.price-comparison-row[data-model="claude-sonnet-5-5"]')).toBeVisible();
        await panel.locator('.price-comparison-row[data-model="claude-sonnet-5-5"] .price-comparison-select').check();
        await panel.getByRole('button', { name: 'Застосувати вибране' }).click();
        await expect(settings.locator('#model-prices-status')).toContainText('пропущено ручних: 1');
        await expect(settings.getByLabel('Вхід · claude-sonnet-5-5')).toHaveValue('0.5');
        await settings.getByRole('button', { name: 'Оновити ціни' }).click();
        await panel.locator('.price-comparison-row[data-model="claude-sonnet-5-5"] .price-comparison-select').check();
        await panel.getByLabel('Перезаписати й ручні').check();
        await panel.getByRole('button', { name: 'Застосувати вибране' }).click();
        await expect(settings.getByLabel('Вхід · claude-sonnet-5-5')).toHaveValue('2');
        await expect(settings.locator('.model-price-row[aria-label="claude-sonnet-5-5"] .model-price-origin')).toContainText('зі списку');

        // Cancelling a comparison writes nothing
        await settings.getByRole('button', { name: 'Оновити ціни' }).click();
        await panel.getByRole('button', { name: 'Скасувати' }).click();
        await expect(panel).toBeHidden();

        // Clearing every price of a row deletes it, after a confirmation
        const custom = settings.locator('.model-price-row[aria-label="e2e-custom-model"]');
        for (const label of ['Вхід', 'Вихід']) await custom.getByLabel(`${label} · e2e-custom-model`).fill('');
        let asked = '';
        page.once('dialog', (dialog) => { asked = dialog.message(); void dialog.dismiss(); });
        await settings.getByRole('button', { name: 'Зберегти' }).click();
        await expect(settings.locator('#translation-settings-error')).toContainText('не видалено');
        expect(asked).toBe('Видалити ціну моделі e2e-custom-model?');
        expect((await (await request.get('/api/model-prices')).json()).prices.some((item: any) => item.model === 'e2e-custom-model')).toBe(true);
        page.once('dialog', (dialog) => { void dialog.accept(); });
        await settings.getByRole('button', { name: 'Зберегти' }).click();
        await expect(settings).toBeHidden();
        expect((await (await request.get('/api/model-prices')).json()).prices.some((item: any) => item.model === 'e2e-custom-model')).toBe(false);

        // «Відновити стандартні» brings back a deleted initial model and leaves the others alone
        await request.put('/api/model-prices', { data: { prices: [{ model: 'gemini-3.6-flash' }] } });
        await page.locator('#translation-settings-button').click();
        await expect(settings.locator('.model-price-row[aria-label="gemini-3.6-flash"]')).toHaveCount(0);
        await settings.getByRole('button', { name: 'Відновити стандартні' }).click();
        await expect(settings.locator('#model-prices-status')).toContainText('відновлено: gemini-3.6-flash');
        await expect(settings.getByLabel('Вхід · gemini-3.6-flash')).toHaveValue('1.5');
        await expect(settings.getByLabel('Вхід · claude-sonnet-5-5')).toHaveValue('2');
        await expect(settings.locator('.model-price-row[aria-label="claude-sonnet-5-5"] .model-price-origin')).toContainText('зі списку');
    } finally {
        await request.delete(`/api/projects/${project.projectId}`);
        await resetPrices(request);
    }
});
