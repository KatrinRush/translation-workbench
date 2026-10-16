import { expect, test } from '@playwright/test';

test.describe('Server log viewer', () => {
	test('frontend assets are served revalidated so deploys are picked up', async ({ request }) => {
		for (const asset of ['/', '/app.js?v=2', '/api.js?v=2', '/styles.css?v=2']) {
			const response = await request.get(asset);
			expect(response.ok()).toBeTruthy();
			expect(response.headers()['cache-control']).toBe('no-cache');
		}
	});

	test('opens the log dialog and loads lines from /api/logs', async ({ page }) => {
		await page.goto('/');
		await page.getByRole('button', { name: /Налаштування/ }).click();

		const logResponse = page.waitForResponse((response) => response.url().includes('/api/logs') && response.status() === 200);
		await page.getByRole('button', { name: /Лог сервера/ }).click();
		await logResponse;

		await expect(page.locator('#server-log-dialog')).toBeVisible();
		await expect(page.locator('#server-log-error')).toBeHidden();
		await expect(page.locator('#server-log-output')).not.toBeEmpty();

		await page.locator('#close-server-log-dialog').click();
		await expect(page.locator('#server-log-dialog')).toBeHidden();
	});

	test('an auto-refresh does not yank a scrolled-up reader back to the bottom', async ({ page }) => {
		await page.goto('/');
		await page.getByRole('button', { name: /Налаштування/ }).click();

		const manyLines = Array.from({ length: 200 }, (_, i) => `[INFO] line ${i}`);
		await page.route('**/api/logs*', (route) => route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ lines: manyLines }),
		}));

		await page.getByRole('button', { name: /Лог сервера/ }).click();
		const output = page.locator('#server-log-output');
		await expect(output).not.toBeEmpty();

		// The dialog opens caught up to the latest line, same as before.
		const scrollAtOpen = await output.evaluate((el) => el.scrollTop);
		expect(scrollAtOpen).toBeGreaterThan(0);

		// Scroll away from the bottom, as if reading an earlier error.
		await output.evaluate((el) => { el.scrollTop = 0; });

		// Simulate the periodic auto-refresh firing while scrolled up.
		await page.evaluate(() => (window as unknown as { loadServerLog(): Promise<void> }).loadServerLog());
		await expect(output).not.toBeEmpty();

		expect(await output.evaluate((el) => el.scrollTop)).toBe(0);
	});

	test('successful requests are hidden by default; «Показувати запити» brings them back, also on auto-refresh, and resets on reopen', async ({ page }) => {
		const request = (path: string, status: number) => `2026-10-16 22:00:00,000 [ERROR] 127.0.0.1 - - [16/Oct/2026 22:00:00] "GET ${path} HTTP/1.1" ${status} -`;
		const quiet = ['2026-10-16 22:00:01,000 [INFO] service started', request('/api/missing', 404)];
		const all = [request('/api/projects', 200), ...quiet, request('/app.js', 304)];
		const asked: string[] = [];
		await page.route('**/api/logs*', (route) => {
			const url = new URL(route.request().url());
			asked.push(url.searchParams.get('includeRequests') ?? 'none');
			return route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({ lines: url.searchParams.get('includeRequests') === '1' ? all : quiet }),
			});
		});
		await page.goto('/');
		await page.getByRole('button', { name: /Налаштування/ }).click();
		await page.getByRole('button', { name: /Лог сервера/ }).click();
		const output = page.locator('#server-log-output');
		const toggle = page.getByLabel('Показувати запити');
		await expect(toggle).not.toBeChecked();
		await expect(output).toContainText('service started');
		await expect(output).toContainText('/api/missing HTTP/1.1" 404');
		await expect(output).not.toContainText('/api/projects');
		expect(asked).toEqual(['0']);

		await toggle.check();
		await expect(output).toContainText('/api/projects HTTP/1.1" 200');
		await expect(output).toContainText('/app.js HTTP/1.1" 304');
		expect(asked.at(-1)).toBe('1');

		// the periodic refresh keeps the choice
		await page.evaluate(() => (window as unknown as { loadServerLog(): Promise<void> }).loadServerLog());
		await expect(output).toContainText('/api/projects');
		expect(asked.at(-1)).toBe('1');

		await toggle.uncheck();
		await expect(output).not.toContainText('/api/projects');
		expect(asked.at(-1)).toBe('0');

		// the state is not kept between openings
		await toggle.check();
		await page.locator('#close-server-log-dialog').click();
		await page.getByRole('button', { name: /Лог сервера/ }).click();
		await expect(page.getByLabel('Показувати запити')).not.toBeChecked();
		await expect(output).not.toContainText('/api/projects');
		expect(asked.at(-1)).toBe('0');
	});
});
