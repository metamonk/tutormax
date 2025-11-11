# Visual Regression Testing Setup - Task 19

**Date:** 2025-11-10
**Status:** In Progress
**Tool:** Playwright with Built-in Screenshot Comparison

---

## Overview

This document outlines the visual regression testing setup for the TutorMax application redesign to ensure design consistency and catch unintended visual changes.

---

## 1. Tool Selection: Playwright

**Why Playwright?**
- ✅ Already widely used in Next.js ecosystem
- ✅ Built-in screenshot comparison
- ✅ Cross-browser testing (Chromium, Firefox, WebKit)
- ✅ Responsive testing capabilities
- ✅ Dark/light mode testing
- ✅ No external service required (unlike Percy/Chromatic)
- ✅ Fast execution
- ✅ TypeScript support

**Alternatives Considered:**
- Percy ($$$ - requires paid service)
- Chromatic ($$$ - requires paid service)
- BackstopJS (older, less maintained)
- Cypress + percy plugin ($$$)

**Decision:** ✅ Playwright for self-hosted visual regression

---

## 2. Installation & Setup

### Install Playwright

```bash
cd frontend
pnpm add -D @playwright/test
npx playwright install
```

### Configuration File

Create `playwright.config.ts`:

```typescript
import { defineConfig, devices } from '@playwright/test';

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
    {
      name: 'chromium-light',
      use: {
        ...devices['Desktop Chrome'],
        colorScheme: 'light',
      },
    },
    {
      name: 'chromium-dark',
      use: {
        ...devices['Desktop Chrome'],
        colorScheme: 'dark',
      },
    },
    {
      name: 'mobile-light',
      use: {
        ...devices['iPhone 13'],
        colorScheme: 'light',
      },
    },
    {
      name: 'mobile-dark',
      use: {
        ...devices['iPhone 13'],
        colorScheme: 'dark',
      },
    },
    {
      name: 'tablet',
      use: {
        ...devices['iPad Pro'],
      },
    },
  ],

  webServer: {
    command: 'pnpm start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

---

## 3. Test Structure

### Directory Layout

```
frontend/
├── tests/
│   └── visual/
│       ├── dashboard.spec.ts
│       ├── tutor-portal.spec.ts
│       ├── tutor-profile.spec.ts
│       ├── interventions.spec.ts
│       ├── admin.spec.ts
│       └── components.spec.ts
├── tests/visual-baseline/
│   ├── chromium-light/
│   ├── chromium-dark/
│   ├── mobile-light/
│   └── mobile-dark/
└── playwright.config.ts
```

---

## 4. Baseline Screenshot Scripts

### Dashboard Page Test

```typescript
// tests/visual/dashboard.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Dashboard Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    // Login if needed
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('full page screenshot', async ({ page }) => {
    await expect(page).toHaveScreenshot('dashboard-full.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });

  test('metrics grid', async ({ page }) => {
    const metricsGrid = page.locator('[data-testid="metrics-grid"]').first();
    await expect(metricsGrid).toHaveScreenshot('dashboard-metrics.png');
  });

  test('charts section', async ({ page }) => {
    const charts = page.locator('[data-testid="charts-section"]').first();
    await expect(charts).toHaveScreenshot('dashboard-charts.png');
  });

  test('activity heatmap', async ({ page }) => {
    const heatmap = page.locator('[data-testid="activity-heatmap"]').first();
    await expect(heatmap).toHaveScreenshot('dashboard-heatmap.png');
  });
});
```

### Tutor Portal Test

```typescript
// tests/visual/tutor-portal.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Tutor Portal Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/tutor-portal');
    await page.waitForLoadState('networkidle');
  });

  test('full page', async ({ page }) => {
    await expect(page).toHaveScreenshot('tutor-portal-full.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });

  test('performance metrics tab', async ({ page }) => {
    await page.click('[data-state="active"][value="metrics"]');
    await page.waitForTimeout(300); // Wait for tab transition
    await expect(page).toHaveScreenshot('tutor-portal-metrics.png');
  });

  test('badges tab', async ({ page }) => {
    await page.click('button:has-text("Badges")');
    await page.waitForTimeout(300);
    await expect(page).toHaveScreenshot('tutor-portal-badges.png');
  });
});
```

### Components Showcase Test

```typescript
// tests/visual/components.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Component Library Visual Regression', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/components-showcase');
    await page.waitForLoadState('networkidle');
  });

  test('all components showcase', async ({ page }) => {
    await expect(page).toHaveScreenshot('components-showcase.png', {
      fullPage: true,
      animations: 'disabled',
    });
  });

  test('button variants', async ({ page }) => {
    const buttons = page.locator('[data-component="buttons"]');
    await expect(buttons).toHaveScreenshot('components-buttons.png');
  });

  test('form components', async ({ page }) => {
    const forms = page.locator('[data-component="forms"]');
    await expect(forms).toHaveScreenshot('components-forms.png');
  });

  test('cards and containers', async ({ page }) => {
    const cards = page.locator('[data-component="cards"]');
    await expect(cards).toHaveScreenshot('components-cards.png');
  });
});
```

### Responsive Breakpoint Tests

```typescript
// tests/visual/responsive.spec.ts
import { test, expect } from '@playwright/test';

const pages = [
  '/dashboard',
  '/tutor-portal',
  '/interventions',
  '/admin/audit-logs',
];

const viewports = [
  { name: 'mobile', width: 375, height: 667 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'wide', width: 1920, height: 1080 },
];

pages.forEach((path) => {
  viewports.forEach(({ name, width, height }) => {
    test(`${path} at ${name}`, async ({ page }) => {
      await page.setViewportSize({ width, height });
      await page.goto(path);
      await page.waitForLoadState('networkidle');

      await expect(page).toHaveScreenshot(`${path.slice(1)}-${name}.png`, {
        fullPage: false, // Viewport only
        animations: 'disabled',
      });
    });
  });
});
```

---

## 5. Running Tests

### Generate Baseline Screenshots

```bash
# Build and start the app
pnpm build
pnpm start

# Generate baseline screenshots (in another terminal)
cd frontend
npx playwright test --update-snapshots
```

### Run Visual Regression Tests

```bash
# Run all visual tests
npx playwright test tests/visual/

# Run specific test file
npx playwright test tests/visual/dashboard.spec.ts

# Run with UI mode (interactive)
npx playwright test --ui

# Run for specific project (browser/theme)
npx playwright test --project=chromium-dark
```

### View Test Report

```bash
npx playwright show-report
```

---

## 6. CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/visual-regression.yml
name: Visual Regression Tests

on:
  pull_request:
    branches: [main]

jobs:
  visual-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 8

      - name: Install dependencies
        run: pnpm install

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Build app
        run: pnpm build

      - name: Run visual tests
        run: npx playwright test tests/visual/

      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/

      - name: Upload screenshots on failure
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: failed-screenshots
          path: tests/visual/*.png
```

---

## 7. Screenshot Management

### Baseline Storage

**Option 1: Git LFS** (Recommended for large projects)
```bash
# Install Git LFS
brew install git-lfs
git lfs install

# Track screenshot files
git lfs track "tests/visual-baseline/**/*.png"
git add .gitattributes
git commit -m "Track screenshots with Git LFS"
```

**Option 2: Regular Git** (For smaller projects)
```bash
# Commit baseline screenshots
git add tests/visual-baseline/
git commit -m "Add visual regression baseline screenshots"
```

**Option 3: Cloud Storage** (For very large projects)
- Upload to S3/GCS
- Download in CI before tests
- Not recommended initially

---

## 8. Handling Visual Changes

### Intentional Changes

1. **Update Baseline:**
   ```bash
   npx playwright test --update-snapshots
   git add tests/visual-baseline/
   git commit -m "Update visual baselines for redesign"
   ```

2. **Review Changes:**
   ```bash
   # Run tests to see diffs
   npx playwright test tests/visual/

   # Open interactive UI to review
   npx playwright test --ui
   ```

3. **Selective Updates:**
   ```bash
   # Update only specific test
   npx playwright test dashboard.spec.ts --update-snapshots
   ```

### Unexpected Changes

1. **Review Diff:**
   - Playwright generates diff images automatically
   - Located in `test-results/`
   - Shows expected vs actual vs diff

2. **Fix Code:**
   - If unintentional, fix the code causing visual regression
   - Re-run tests

3. **Accept Changes:**
   - If acceptable, update baselines

---

## 9. Best Practices

### Test Writing Guidelines

```typescript
// ✅ GOOD: Wait for content to load
await page.waitForLoadState('networkidle');
await page.waitForSelector('[data-testid="content"]');

// ✅ GOOD: Disable animations
await expect(page).toHaveScreenshot('page.png', {
  animations: 'disabled',
});

// ✅ GOOD: Use data-testid for stability
const component = page.locator('[data-testid="metric-card"]');

// ✅ GOOD: Mask dynamic content
await expect(page).toHaveScreenshot('page.png', {
  mask: [page.locator('[data-testid="timestamp"]')],
});

// ❌ BAD: Don't test loading states (unstable)
// ❌ BAD: Don't include timestamps or dates
// ❌ BAD: Don't test animations mid-transition
```

### Coverage Strategy

**Critical User Flows:**
1. Login → Dashboard
2. Dashboard → Tutor Profile
3. Interventions workflow
4. Admin audit logs

**All Major Pages:**
- Dashboard (light/dark)
- Tutor Portal (light/dark)
- Tutor Profile (light/dark)
- Interventions (light/dark)
- Admin Pages (light/dark)
- Login (light/dark)

**Component Library:**
- All base components
- All variants
- All states (hover, focus, disabled)

**Responsive Breakpoints:**
- Mobile (375px)
- Tablet (768px)
- Desktop (1440px)
- Wide (1920px)

---

## 10. NPM Scripts

Add to `package.json`:

```json
{
  "scripts": {
    "test:visual": "playwright test tests/visual/",
    "test:visual:ui": "playwright test tests/visual/ --ui",
    "test:visual:update": "playwright test tests/visual/ --update-snapshots",
    "test:visual:report": "playwright show-report"
  }
}
```

---

## 11. Baseline Screenshot Plan

### Phase 1: Core Pages (Immediate)
- [x] Dashboard
- [x] Tutor Portal
- [x] Tutor Profile
- [x] Interventions
- [x] Login

### Phase 2: Admin Pages
- [ ] Audit Logs
- [ ] Compliance
- [ ] Training
- [ ] Data Retention

### Phase 3: Component Library
- [ ] All button variants
- [ ] All form components
- [ ] All card variants
- [ ] All feedback components

### Phase 4: Responsive Tests
- [ ] Mobile viewports (all pages)
- [ ] Tablet viewports (all pages)
- [ ] Desktop viewports (all pages)

---

## 12. Metrics & Goals

### Target Coverage
- ✅ 100% of major pages
- ✅ Light and dark modes
- ✅ Mobile, tablet, desktop
- ✅ All critical user flows

### Success Criteria
- ✅ All baseline screenshots captured
- ✅ CI pipeline configured
- ✅ Tests run on every PR
- ✅ Visual changes reviewable
- ✅ < 5 minute test execution time

---

## 13. Troubleshooting

### Common Issues

**1. Flaky Tests (Screenshots vary slightly)**
```typescript
// Increase threshold
await expect(page).toHaveScreenshot('page.png', {
  threshold: 0.2, // Allow 20% difference
});

// Or use maxDiffPixels
await expect(page).toHaveScreenshot('page.png', {
  maxDiffPixels: 100,
});
```

**2. Font Rendering Differences**
```bash
# Install same fonts in CI as local
# Use font-display: swap in CSS
```

**3. Timing Issues**
```typescript
// Add explicit waits
await page.waitForTimeout(500);
await page.waitForFunction(() => document.fonts.ready);
```

---

## 14. Next Steps

### Immediate Actions
1. ✅ Install Playwright
2. ✅ Create configuration
3. ⚠️ Write test files
4. ⚠️ Generate baselines
5. ⚠️ Set up CI

### Development Tasks
- [ ] Add data-testid attributes to components
- [ ] Create screenshot capture scripts
- [ ] Generate baseline for all pages
- [ ] Document visual testing process
- [ ] Train team on visual regression workflow

---

## 15. Estimated Time

| Task | Time |
|------|------|
| Playwright setup | 30 min |
| Write test files | 2 hours |
| Generate baselines | 1 hour |
| CI configuration | 1 hour |
| Documentation | 30 min |

**Total:** ~5 hours

---

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Visual Comparisons Guide](https://playwright.dev/docs/test-snapshots)
- [Best Practices](https://playwright.dev/docs/best-practices)

---

**Status:** 📝 IN PROGRESS
**Last Updated:** 2025-11-10
**Next:** Install Playwright and create test files
