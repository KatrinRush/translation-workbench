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
});
