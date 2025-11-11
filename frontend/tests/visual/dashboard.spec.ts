import { test, expect } from '@playwright/test';

/**
 * Dashboard Visual Regression Tests
 *
 * Captures screenshots of the main dashboard to ensure visual consistency
 * across redesigns and updates.
 */
test.describe('Dashboard Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    // Wait for any lazy-loaded components
    await page.waitForTimeout(500);
  });

  test('full page screenshot', async ({ page }) => {
    await expect(page).toHaveScreenshot('dashboard-full.png', {
      fullPage: true,
      animations: 'disabled',
      timeout: 10000,
    });
  });

  test('above fold content', async ({ page }) => {
    await expect(page).toHaveScreenshot('dashboard-above-fold.png', {
      fullPage: false,
      animations: 'disabled',
    });
  });
});
