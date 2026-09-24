import { expect, test } from '@playwright/test';

async function captureErrors(page: import('@playwright/test').Page) {
    await page.addInitScript(() => {
        (window as any).__errors = [];
        const orig = console.error;
        console.error = (...args: any[]) => {
            (window as any).__errors.push(args.map((a) => (a && a.message) ? a.message : String(a)).join(' | '));
            orig(...args);
        };
    });
}

// listAuthors is a GET request, so a non-JSON/bad response is retried once (~2s) before
// the real error surfaces — these waits account for that.

test('a non-JSON, non-Cloudflare response is not blamed on Cloudflare', async ({ page }) => {
    await captureErrors(page);
    await page.route('**/api/authors', (route) => route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: '<html><body>some unrelated proxy error page</body></html>',
    }));

    await page.goto('/');
    await page.waitForTimeout(2500);

    const errors = (await page.evaluate(() => (window as any).__errors)).join('\n');
    expect(errors).toContain('без JSON');
    expect(errors).not.toContain('Cloudflare');
});

test('an HTML response carrying Cloudflare Access branding is reported as a session issue', async ({ page }) => {
    await captureErrors(page);
    await page.route('**/api/authors', (route) => route.fulfill({
        status: 200,
        contentType: 'text/html',
        body: '<html><body>Sign in with Cloudflare Access to continue</body></html>',
    }));

    await page.goto('/');
    await page.waitForTimeout(2500);

    const errors = (await page.evaluate(() => (window as any).__errors)).join('\n');
    expect(errors).toContain('Сесія Cloudflare');
});

test('a real backend JSON error is shown as-is, not as a Cloudflare message', async ({ page }) => {
    await captureErrors(page);
    await page.route('**/api/authors', (route) => route.fulfill({
        status: 502,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'DeepL не зміг виконати переклад (HTTP 502). Bad gateway.' }),
    }));

    await page.goto('/');
    await page.waitForTimeout(300);

    const errors = (await page.evaluate(() => (window as any).__errors)).join('\n');
    expect(errors).toContain('DeepL не зміг виконати переклад');
    expect(errors).not.toContain('Cloudflare');
});
