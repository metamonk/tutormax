# Animation Testing & Performance Guide

This guide covers testing and optimizing animations in the TutorMax application.

## Accessibility Testing

### Testing Prefers-Reduced-Motion

All animations in the app respect the `prefers-reduced-motion` user preference. Here's how to test it:

#### In Chrome/Edge:
1. Open DevTools (F12)
2. Open Command Palette (Cmd/Ctrl + Shift + P)
3. Type "Emulate CSS prefers-reduced-motion"
4. Select "prefers-reduced-motion: reduce"
5. Verify that animations are disabled or greatly reduced

#### In Firefox:
1. Open DevTools (F12)
2. Click the three-dot menu > Settings
3. Under "Inspector", check "Emulate prefers-reduced-motion: reduce"

#### In macOS System Settings:
1. System Settings > Accessibility > Display
2. Enable "Reduce motion"
3. Refresh the browser

#### In Windows Settings:
1. Settings > Accessibility > Visual effects
2. Toggle "Animation effects" to Off
3. Refresh the browser

### Expected Behavior with Reduced Motion

When prefers-reduced-motion is enabled:

- ✅ All CSS animations should have near-zero duration (0.01ms)
- ✅ React animation hooks return zero durations
- ✅ Page transitions should be instant
- ✅ Skeleton loaders should still be visible (static, no animation)
- ✅ Loading spinners should still rotate (essential for indicating loading state)

## Performance Testing

### FPS Monitoring

Use Chrome DevTools Performance tab:

1. Open DevTools > Performance tab
2. Click Record (or Cmd/Ctrl + E)
3. Interact with animated elements
4. Stop recording
5. Check the FPS graph - should maintain 60fps
6. Look for dropped frames (red bars)

### Animation Performance Checklist

- ✅ Animations use `transform` and `opacity` (GPU-accelerated)
- ✅ No animations of `width`, `height`, `top`, `left` (causes layout recalculation)
- ✅ `will-change` is used sparingly (only on frequently animated elements)
- ✅ `transform-gpu` class applied to animated elements
- ✅ Long lists use virtual scrolling (react-window)

### Performance Profiling

#### Check for Layout Thrashing:

```javascript
// In DevTools Console
performance.mark('start');
// Interact with animations
performance.mark('end');
performance.measure('animation-time', 'start', 'end');
console.table(performance.getEntriesByType('measure'));
```

#### Monitor Composite Layers:

1. Chrome DevTools > More tools > Layers
2. Interact with animated elements
3. Verify promoted layers are appropriate
4. Too many layers can hurt performance on mobile

### Mobile Performance

Test on real devices when possible:

- **Low-end Android**: Test on devices with 2GB RAM or less
- **Mid-range iOS**: iPhone SE (2nd gen) or similar
- **Target**: Maintain 60fps on animations
- **Acceptable**: 30fps on complex transitions

## Component-Specific Testing

### Button Animations

Test:
- ✅ Hover scale effect (should be subtle, 1.02 scale)
- ✅ Active scale effect (0.98 scale)
- ✅ Focus ring appears smoothly
- ✅ Touch devices: no hover effects, but active state works
- ✅ Disabled buttons: no animations

### Card Hover Effects

Test:
- ✅ Shadow elevation increases on hover
- ✅ Lift effect (-translate-y-1) on interactive cards
- ✅ Active state returns to default
- ✅ Non-interactive cards: no hover effects

### Loading States

Test:
- ✅ Skeleton loaders animate smoothly
- ✅ Shimmer effect doesn't cause jank
- ✅ Loading spinners maintain 60fps
- ✅ Progress bars transition smoothly

### Page Transitions

Test:
- ✅ Navigation feels smooth, not jarring
- ✅ No content flash during transition
- ✅ Transitions don't block user interaction
- ✅ Back button navigation animates correctly

## Performance Optimization Tips

### Do's ✅

1. **Use CSS transforms**
   ```css
   /* Good - GPU accelerated */
   transform: translateY(-4px);
   ```

2. **Use opacity for fades**
   ```css
   /* Good - GPU accelerated */
   opacity: 0.5;
   ```

3. **Apply GPU acceleration**
   ```tsx
   <div className="transform-gpu">
   ```

4. **Use CSS animations for simple effects**
   ```css
   /* Good - offloaded to compositor */
   animation: slide-in 250ms ease-out;
   ```

5. **Contain layout shifts**
   ```css
   /* Good - contains repaints */
   contain: layout;
   ```

### Don'ts ❌

1. **Don't animate layout properties**
   ```css
   /* Bad - triggers layout */
   width: 100%; /* animated */
   height: 100%; /* animated */
   top: 0; /* animated */
   left: 0; /* animated */
   ```

2. **Don't overuse will-change**
   ```css
   /* Bad - wastes GPU memory */
   * {
     will-change: transform;
   }
   ```

3. **Don't nest too many animated elements**
   ```tsx
   {/* Bad - compounds animation overhead */}
   <Animated>
     <Animated>
       <Animated>
         Content
       </Animated>
     </Animated>
   </Animated>
   ```

4. **Don't animate during critical loading**
   ```tsx
   {/* Bad - delays content */}
   <PageTransition duration={1000}>
     <CriticalContent />
   </PageTransition>
   ```

## Browser Compatibility

### Supported Features

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| CSS Transforms | ✅ | ✅ | ✅ | ✅ |
| CSS Animations | ✅ | ✅ | ✅ | ✅ |
| prefers-reduced-motion | ✅ | ✅ | ✅ | ✅ |
| Intersection Observer | ✅ | ✅ | ✅ | ✅ |
| GPU Acceleration | ✅ | ✅ | ✅ | ✅ |

### Fallbacks

All animations gracefully degrade:
- Older browsers: animations are simplified or removed
- No JavaScript: CSS animations still work
- Reduced motion: instant transitions

## Common Issues & Solutions

### Issue: Animations feel janky

**Solutions:**
1. Check FPS in Performance tab
2. Verify using `transform` instead of layout properties
3. Add `transform-gpu` class
4. Reduce animation complexity
5. Test on target devices

### Issue: Animations don't respect reduced motion

**Solutions:**
1. Verify hooks return zero duration
2. Check CSS has `@media (prefers-reduced-motion: reduce)` rules
3. Ensure components use `usePrefersReducedMotion()` hook
4. Test with browser emulation

### Issue: Flash of unstyled content

**Solutions:**
1. Use `animationFillMode: 'both'` for staggered animations
2. Set initial state to match final animated state
3. Use `opacity: 0` in CSS, not just on mount
4. Consider using `FadeInWhenVisible` for below-fold content

### Issue: Touch devices have hover stuck states

**Solutions:**
1. Use `@media (hover: hover)` for hover-only styles
2. Add `no-tap-highlight` class to remove tap flash
3. Ensure `active` states work correctly
4. Test on real devices, not just emulators

## Automated Testing

### Jest/Vitest Tests

```typescript
import { render } from '@testing-library/react';
import { Button } from '@/components/ui/button';

test('button applies hover scale effect', () => {
  const { container } = render(<Button>Click me</Button>);
  const button = container.querySelector('button');

  expect(button).toHaveClass('hover:scale-[1.02]');
});

test('respects prefers-reduced-motion', () => {
  // Mock matchMedia
  Object.defineProperty(window, 'matchMedia', {
    value: jest.fn().mockImplementation(query => ({
      matches: query === '(prefers-reduced-motion: reduce)',
      media: query,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    })),
  });

  const { result } = renderHook(() => usePrefersReducedMotion());
  expect(result.current).toBe(true);
});
```

### E2E Testing (Playwright)

```typescript
test('page transitions work correctly', async ({ page }) => {
  await page.goto('/dashboard');

  // Wait for page to load
  await page.waitForSelector('[data-testid="dashboard"]');

  // Navigate to another page
  await page.click('a[href="/interventions"]');

  // Check for transition
  const content = page.locator('[data-testid="interventions"]');
  await expect(content).toBeVisible();

  // Verify no content flash
  await page.screenshot({ path: 'transition.png' });
});
```

## Performance Budgets

Target performance metrics:

- **Animation FPS**: Maintain 60fps
- **Time to Interactive**: < 3s
- **Total Animation JS**: < 10KB gzipped
- **Paint time**: < 16ms per frame
- **Composite time**: < 2ms per frame

## Monitoring in Production

Consider adding performance monitoring:

```typescript
// Report slow animations
if (performance.getEntriesByType('measure')) {
  const measures = performance.getEntriesByType('measure');
  measures.forEach(measure => {
    if (measure.duration > 100) {
      console.warn(`Slow animation: ${measure.name} took ${measure.duration}ms`);
    }
  });
}
```

## Resources

- [Web Animations API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API)
- [CSS Transforms Performance](https://www.html5rocks.com/en/tutorials/speed/high-performance-animations/)
- [Prefers Reduced Motion](https://web.dev/prefers-reduced-motion/)
- [Chrome DevTools Performance](https://developer.chrome.com/docs/devtools/performance/)
