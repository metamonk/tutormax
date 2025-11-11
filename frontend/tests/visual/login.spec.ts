import { test, expect } from '@playwright/test';

/**
 * Login Page Visual Regression Tests
 */
test.describe('Login Page Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
  });

  test('login page', async ({ page }) => {
    await expect(page).toHaveScreenshot('login.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });
});
