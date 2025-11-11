import { defineConfig, devices } from '@playwright/test';

/**
 * Visual Regression Testing Configuration
 *
 * Tests screenshots across multiple browsers, themes, and viewports
 * to ensure design consistency after redesign.
 */
export default defineConfig({
  testDir: './tests/visual',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    // Desktop - Light Mode
    {
      name: 'chromium-light',
      use: {
        ...devices['Desktop Chrome'],
        colorScheme: 'light',
      },
    },
    // Desktop - Dark Mode
    {
      name: 'chromium-dark',
      use: {
        ...devices['Desktop Chrome'],
        colorScheme: 'dark',
      },
    },
    // Mobile - Light Mode
    {
      name: 'mobile-light',
      use: {
        ...devices['iPhone 13'],
        colorScheme: 'light',
      },
    },
    // Mobile - Dark Mode
    {
      name: 'mobile-dark',
      use: {
        ...devices['iPhone 13'],
        colorScheme: 'dark',
      },
    },
    // Tablet
    {
      name: 'tablet',
      use: {
        ...devices['iPad Pro'],
        colorScheme: 'light',
      },
    },
  ],

  webServer: {
    command: 'pnpm start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
