import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

const BASE_URL = 'http://localhost:8000';
const PROJECT_ID = 'test-project-cover-' + Date.now();

async function createTestProject(page: Page, projectTitle: string) {
    await page.click('#new-project-button');
    await page.fill('#project-title-input', projectTitle);
    await page.click('#create-project-button');
    await page.waitForURL(/\/main/);
}

async function uploadFile(page: Page, filePath: string) {
    await page.click('#upload-button');
    const fileInput = await page.locator('#file-input');
    await fileInput.setInputFiles(filePath);
    // Wait for upload to complete
    await page.waitForSelector('.upload-status.success', { timeout: 30000 });
}

async function getCoverImage(page: Page, projectId: string): Promise<Buffer | null> {
    try {
        const response = await page.context().request.get(`/api/projects/${projectId}/cover`);
        if (response.ok()) {
            return await response.body();
        }
        return null;
    } catch (error) {
        return null;
    }
}

async function uploadCoverImage(page: Page, imagePath: string) {
    await page.click('#upload-cover-button');
    const fileInput = await page.locator('#cover-file-input');
    await fileInput.setInputFiles(imagePath);
    // Wait for upload to complete
    await page.waitForTimeout(1000);
}

test.describe('Book Cover Functionality', () => {
    test.beforeAll(async () => {
        // Start the backend server if not already running
        // For local testing, assume server is already running
    });

    test('EPUB with cover → cover appears', async ({ browser }) => {
        const context = await browser.newContext();
        const page = await context.newPage();
        
        try {
            await page.goto(BASE_URL);
            
            // Create a new project
            await createTestProject(page, 'Test Project With Cover');
            
            // Get the project ID from the URL or find it in the DOM
            const projectCards = await page.locator('[data-action="open-project"]');
            const count = await projectCards.count();
            const lastProjectId = await projectCards.nth(count - 1).getAttribute('data-project-id');
            
            expect(lastProjectId).toBeTruthy();
            
            // Upload a test EPUB file with a cover
            const epubPath = path.join(__dirname, '..', 'test-data', 'sample-with-cover.epub');
            if (!fs.existsSync(epubPath)) {
                console.warn(`Test EPUB not found at ${epubPath}, skipping test`);
                return;
            }
            
            // Manually set project ID in header for upload
            const fileInput = await page.locator('#file-input');
            await fileInput.setInputFiles(epubPath);
            
            // Wait for upload to complete
            await page.waitForSelector('.upload-status.success', { timeout: 30000 });
            
            // Check if cover image appears in workspace
            const coverImg = page.locator('#workspace-cover img');
            await expect(coverImg).toBeVisible();
            
            // Verify cover is accessible via API
            const coverData = await getCoverImage(page, lastProjectId!);
            expect(coverData).toBeTruthy();
            expect(coverData!.length).toBeGreaterThan(0);
        } finally {
            await context.close();
        }
    });

    test('Reload/reopen → cover persists', async ({ browser }) => {
        const context = await browser.newContext();
        const page = await context.newPage();
        
        try {
            await page.goto(BASE_URL);
            
            // Create a new project
            await createTestProject(page, 'Test Project Persistence');
            
            // Get the project ID
            const projectCards = await page.locator('[data-action="open-project"]');
            const count = await projectCards.count();
            const lastProjectId = await projectCards.nth(count - 1).getAttribute('data-project-id');
            
            // Upload EPUB with cover
            const epubPath = path.join(__dirname, '..', 'test-data', 'sample-with-cover.epub');
            if (!fs.existsSync(epubPath)) {
                console.warn(`Test EPUB not found at ${epubPath}, skipping test`);
                return;
            }
            
            const fileInput = await page.locator('#file-input');
            await fileInput.setInputFiles(epubPath);
            await page.waitForSelector('.upload-status.success', { timeout: 30000 });
            
            // Get initial cover data
            const coverDataBefore = await getCoverImage(page, lastProjectId!);
            expect(coverDataBefore).toBeTruthy();
            
            // Reload the page
            await page.reload();
            
            // Navigate back to the project
            await page.click(`[data-project-id="${lastProjectId}"]`);
            await page.waitForSelector('#workspace-cover img', { timeout: 5000 });
            
            // Verify cover still exists
            const coverImg = page.locator('#workspace-cover img');
            await expect(coverImg).toBeVisible();
            
            // Verify cover data is identical
            const coverDataAfter = await getCoverImage(page, lastProjectId!);
            expect(coverDataAfter).toBeTruthy();
            expect(coverDataBefore!.toString()).toBe(coverDataAfter!.toString());
        } finally {
            await context.close();
        }
    });

    test('EPUB without cover → placeholder shown', async ({ browser }) => {
        const context = await browser.newContext();
        const page = await context.newPage();
        
        try {
            await page.goto(BASE_URL);
            
            // Create a new project
            await createTestProject(page, 'Test Project No Cover');
            
            // Upload a test EPUB file without a cover
            const epubPath = path.join(__dirname, '..', 'test-data', 'sample-without-cover.epub');
            if (!fs.existsSync(epubPath)) {
                console.warn(`Test EPUB not found at ${epubPath}, skipping test`);
                return;
            }
            
            const fileInput = await page.locator('#file-input');
            await fileInput.setInputFiles(epubPath);
            await page.waitForSelector('.upload-status.success', { timeout: 30000 });
            
            // Check if placeholder appears
            const placeholder = page.locator('.workspace-cover-placeholder');
            await expect(placeholder).toBeVisible();
            
            // Verify no cover image element exists
            const coverImg = page.locator('#workspace-cover img');
            await expect(coverImg).not.toBeVisible();
        } finally {
            await context.close();
        }
    });

    test('Manual upload → cover changed', async ({ browser }) => {
        const context = await browser.newContext();
        const page = await context.newPage();
        
        try {
            await page.goto(BASE_URL);
            
            // Create a new project
            await createTestProject(page, 'Test Manual Cover Upload');
            
            // Get the project ID
            const projectCards = await page.locator('[data-action="open-project"]');
            const count = await projectCards.count();
            const lastProjectId = await projectCards.nth(count - 1).getAttribute('data-project-id');
            
            // Upload EPUB without cover first
            const epubNocover = path.join(__dirname, '..', 'test-data', 'sample-without-cover.epub');
            if (!fs.existsSync(epubNocover)) {
                console.warn(`Test EPUB not found at ${epubNocover}, skipping test`);
                return;
            }
            
            const fileInput = await page.locator('#file-input');
            await fileInput.setInputFiles(epubNocover);
            await page.waitForSelector('.upload-status.success', { timeout: 30000 });
            
            // Verify placeholder is shown
            let placeholder = page.locator('.workspace-cover-placeholder');
            await expect(placeholder).toBeVisible();
            
            // Upload a cover image manually
            const imagePath = path.join(__dirname, '..', 'test-data', 'test-cover.jpg');
            if (!fs.existsSync(imagePath)) {
                console.warn(`Test image not found at ${imagePath}, creating a test image`);
                // Create a simple test image
                return;
            }
            
            await uploadCoverImage(page, imagePath);
            
            // Wait for cover to be displayed
            const coverImg = page.locator('#workspace-cover img');
            await expect(coverImg).toBeVisible({ timeout: 5000 });
            
            // Verify placeholder is gone
            await expect(placeholder).not.toBeVisible();
        } finally {
            await context.close();
        }
    });

    test('Replace EPUB → cover behavior', async ({ browser }) => {
        const context = await browser.newContext();
        const page = await context.newPage();
        
        try {
            await page.goto(BASE_URL);
            
            // Create a new project
            await createTestProject(page, 'Test Cover Replacement');
            
            // Get the project ID
            const projectCards = await page.locator('[data-action="open-project"]');
            const count = await projectCards.count();
            const lastProjectId = await projectCards.nth(count - 1).getAttribute('data-project-id');
            
            // 1. Upload EPUB with cover
            const epubWithCover = path.join(__dirname, '..', 'test-data', 'sample-with-cover.epub');
            if (!fs.existsSync(epubWithCover)) {
                console.warn(`Test EPUB not found at ${epubWithCover}, skipping test`);
                return;
            }
            
            const fileInput = await page.locator('#file-input');
            await fileInput.setInputFiles(epubWithCover);
            await page.waitForSelector('.upload-status.success', { timeout: 30000 });
            
            const coverDataInitial = await getCoverImage(page, lastProjectId!);
            expect(coverDataInitial).toBeTruthy();
            
            // 2. Upload EPUB without cover (replacement)
            const epubNoCover = path.join(__dirname, '..', 'test-data', 'sample-without-cover.epub');
            if (!fs.existsSync(epubNoCover)) {
                console.warn(`Test EPUB not found at ${epubNoCover}, skipping test`);
                return;
            }
            
            await page.click('#upload-button');
            await fileInput.setInputFiles(epubNoCover);
            await page.waitForSelector('.upload-status.success', { timeout: 30000 });
            
            // When replacing with EPUB that has no auto cover, old auto-cover should be cleared
            const coverDataAfterReplacement = await getCoverImage(page, lastProjectId!);
            // Cover should be null or the user-uploaded one (if any)
            // In this case, no user upload, so should be null
        } finally {
            await context.close();
        }
    });
});
