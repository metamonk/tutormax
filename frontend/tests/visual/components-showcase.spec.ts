import { test, expect } from '@playwright/test';

/**
 * Component Library Visual Regression Tests
 *
 * Captures all UI components in their various states to ensure
 * design system consistency.
 */
test.describe('Components Showcase Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/components-showcase');
    await page.waitForLoadState('networkidle');
  });

  test('full showcase page', async ({ page }) => {
    await expect(page).toHaveScreenshot('components-showcase.png', {
      fullPage: true,
      animations: 'disabled',
      timeout: 10000,
    });
  });
});
