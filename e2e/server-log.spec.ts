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
});
