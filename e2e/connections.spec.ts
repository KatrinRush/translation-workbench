import { expect, test } from '@playwright/test';


test.describe('Connections', () => {
	test('adds, verifies, masks, and persists an OpenAI connection', async ({ page, request }) => {
		const existingResponse = await request.get('/api/connections');
		expect(existingResponse.ok()).toBeTruthy();
		const existingConnections = await existingResponse.json();
		for (const connection of existingConnections.filter((item) => item.providerId === 'openai')) {
			await request.delete(`/api/connections/${connection.connectionId}`);
		}

		try {
			await page.goto('/');
			await page.getByRole('button', { name: /Налаштування/ }).click();

			const card = page.locator('.connection-item').filter({ hasText: 'OpenAI / GPT' });
			await expect(card).toBeVisible();
			await expect(card).toContainText('Не налаштовано');
			await card.getByRole('button', { name: 'Додати' }).click();

			const apiKeyInput = page.getByLabel('API key');
			await expect(apiKeyInput).toHaveAttribute('type', 'password');
			await apiKeyInput.fill('sk-e2e-secret');
			await page.getByRole('button', { name: 'Зберегти' }).click();

			await expect(card).toContainText('Не перевірено');
			const storedResponse = await request.get('/api/connections');
			expect(await storedResponse.text()).not.toContain('sk-e2e-secret');

			await card.getByRole('button', { name: 'Перевірити' }).click();
			await expect(card).toContainText('Підключено');

			await card.getByRole('button', { name: 'Редагувати' }).click();
			await expect(page.getByLabel('API key')).toHaveValue('');
			await expect(page.locator('#connection-credential-hint')).toContainText('порожніми');
			await page.getByRole('button', { name: 'Скасувати' }).click();

			await page.reload();
			await page.getByRole('button', { name: /Налаштування/ }).click();
			await expect(page.locator('.connection-item').filter({ hasText: 'OpenAI / GPT' })).toContainText('Підключено');
		} finally {
			const connectionsResponse = await request.get('/api/connections');
			if (connectionsResponse.ok()) {
				const connections = await connectionsResponse.json();
				for (const connection of connections.filter((item) => item.providerId === 'openai')) {
					await request.delete(`/api/connections/${connection.connectionId}`);
				}
			}
		}
	});
});
