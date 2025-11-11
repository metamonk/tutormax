# PWA Testing Guide for TutorMax

Comprehensive testing checklist for validating PWA implementation, mobile optimization, and performance metrics.

## 🧪 Testing Environment Setup

### Prerequisites

1. **Modern Browsers**:
   - Chrome/Edge 90+ (Desktop & Mobile)
   - Safari 14+ (iOS & macOS)
   - Firefox 90+

2. **Testing Tools**:
   - Chrome DevTools
   - Lighthouse
   - ngrok or similar tunneling (for mobile testing)
   - Real mobile devices (iOS & Android)

3. **Network Throttling**:
   - Chrome DevTools Network Tab
   - Slow 3G, Fast 3G, 4G presets

### Local Setup

```bash
# Build production version
cd /Users/zeno/Projects/tutormax/frontend
pnpm build

# Start production server
pnpm start

# Access at https://localhost:3000
```

## ✅ PWA Core Features Testing

### 1. Manifest Validation

**Chrome DevTools** → Application → Manifest

- [ ] Manifest loads without errors
- [ ] Name: "TutorMax - Tutor Performance Evaluation"
- [ ] Short name: "TutorMax"
- [ ] Start URL: "/"
- [ ] Display: "standalone"
- [ ] Theme color: "#3b82f6"
- [ ] Background color: "#ffffff"
- [ ] Icons array contains 8 sizes (72-512px)
- [ ] Screenshots present (wide and narrow)
- [ ] Shortcuts defined (3 items)

**Expected Result**: All manifest properties valid, no warnings.

### 2. Service Worker Registration

**Chrome DevTools** → Application → Service Workers

- [ ] Service worker registered
- [ ] Status: "activated and running"
- [ ] Scope: "/"
- [ ] Update on reload option works
- [ ] Skip waiting functionality works

**Test Steps**:
1. Open DevTools
2. Navigate to Application > Service Workers
3. Verify active service worker
4. Click "Update" - should update without errors
5. Click "Skip waiting" - should activate immediately

**Expected Result**: Service worker active and responsive to commands.

### 3. Offline Functionality

**Chrome DevTools** → Network → Throttling: Offline

- [ ] App loads while offline (cached)
- [ ] Offline indicator appears
- [ ] Previously visited pages accessible
- [ ] Images cached and displayed
- [ ] Graceful degradation for API calls

**Test Steps**:
1. Visit all main pages while online
2. Set Network to "Offline" in DevTools
3. Reload page
4. Navigate between pages
5. Attempt API actions

**Expected Result**: Core UI loads, cached content accessible, clear offline messaging.

### 4. Caching Strategy

**Chrome DevTools** → Application → Cache Storage

- [ ] workbox-precache exists
- [ ] offlineCache exists
- [ ] Static assets cached (JS, CSS, images)
- [ ] API responses cached appropriately
- [ ] Cache size reasonable (< 50MB)

**Test Steps**:
1. Clear all caches
2. Visit homepage
3. Navigate to dashboard
4. Check Cache Storage for entries
5. Verify asset types cached

**Expected Result**: Efficient caching, critical assets precached.

## 📱 Mobile Optimization Testing

### 1. Responsive Design

**Viewports to Test**:
- iPhone SE (375x667)
- iPhone 12 Pro (390x844)
- iPhone 14 Pro Max (430x932)
- Pixel 5 (393x851)
- Galaxy S21 (360x800)
- iPad (768x1024)
- iPad Pro (1024x1366)

**Checklist per Viewport**:
- [ ] No horizontal scrolling
- [ ] Text readable without zoom
- [ ] Buttons accessible
- [ ] Navigation functional
- [ ] Cards/components stack properly
- [ ] Images responsive

**Test Steps**:
1. Open DevTools Device Mode
2. Test each viewport
3. Rotate to landscape
4. Test all main pages

**Expected Result**: Perfect display across all viewports.

### 2. Touch Interactions

**Device: Real iOS/Android**

- [ ] All buttons respond to tap
- [ ] Tap targets minimum 44x44px
- [ ] No tap delay (300ms)
- [ ] Tap highlight disabled
- [ ] Swipe gestures work in nav
- [ ] Pull-to-refresh disabled (or custom)
- [ ] Long-press actions work

**Test Steps**:
1. Test on real device
2. Tap all interactive elements
3. Try swipe left/right in bottom nav
4. Check for lag or delay
5. Verify haptic feedback (if enabled)

**Expected Result**: Instant, native-like touch response.

### 3. Safe Area Insets (Notched Devices)

**Device: iPhone X or newer**

- [ ] Content doesn't hide behind notch
- [ ] Bottom nav respects home indicator
- [ ] Full-screen mode works properly
- [ ] Landscape mode safe areas correct
- [ ] No content cut off

**Test Steps**:
1. Open on iPhone with notch
2. Install as PWA
3. Check top and bottom safe areas
4. Rotate to landscape
5. Verify all content visible

**Expected Result**: Content within safe areas, no clipping.

### 4. Bottom Navigation

**Mobile Only**

- [ ] Visible on all pages
- [ ] Active state highlights current page
- [ ] Swipe gestures navigate
- [ ] Icons clear and recognizable
- [ ] Labels readable
- [ ] Role-based items shown correctly
- [ ] Smooth animations

**Test Steps**:
1. Navigate through app
2. Verify active state changes
3. Swipe left/right to navigate
4. Test with different user roles

**Expected Result**: Intuitive, smooth navigation experience.

## 🚀 Performance Testing

### 1. Lighthouse Audit

**Chrome DevTools** → Lighthouse → Generate Report

**Target Scores**:
- [ ] Performance: ≥ 90
- [ ] Accessibility: ≥ 90
- [ ] Best Practices: ≥ 90
- [ ] SEO: ≥ 90
- [ ] PWA: ≥ 90

**Test Steps**:
1. Build production version
2. Open in Incognito mode
3. Run Lighthouse audit
4. Review opportunities and diagnostics

**Expected Result**: All scores ≥ 90.

### 2. Core Web Vitals

**Use PageSpeed Insights or Lighthouse**

**Target Metrics**:
- [ ] LCP (Largest Contentful Paint): < 2.5s
- [ ] FID (First Input Delay): < 100ms
- [ ] CLS (Cumulative Layout Shift): < 0.1
- [ ] FCP (First Contentful Paint): < 1.8s
- [ ] TTFB (Time to First Byte): < 600ms

**Test Steps**:
1. Run Lighthouse audit
2. Check "View Trace" for details
3. Use Performance panel for recording
4. Test on 3G network simulation

**Expected Result**: All vitals in "Good" range.

### 3. Page Load Performance

**Network Throttling: Slow 3G**

- [ ] Initial load < 5s on Slow 3G
- [ ] Interactive < 7s on Slow 3G
- [ ] Dashboard loads < 3s on Fast 3G
- [ ] Images lazy load properly
- [ ] No render-blocking resources
- [ ] Fonts load without FOIT

**Test Steps**:
1. Clear cache and reload
2. Set throttling to Slow 3G
3. Record load time
4. Check for loading states
5. Verify progressive enhancement

**Expected Result**: Acceptable load times even on slow networks.

### 4. Bundle Size Analysis

**Next.js Build Output**

- [ ] Total bundle size < 500KB (gzipped)
- [ ] Main JS bundle < 200KB
- [ ] CSS bundle < 50KB
- [ ] Largest chunk < 100KB
- [ ] No duplicate dependencies

**Test Steps**:
```bash
pnpm build
# Check output for bundle sizes
```

**Expected Result**: Optimized bundle sizes, efficient code splitting.

## 🔧 Installation Testing

### 1. Desktop Installation

**Chrome/Edge Desktop**

- [ ] Install button appears in address bar
- [ ] Install prompt shows (after 30s)
- [ ] App installs successfully
- [ ] Desktop icon created
- [ ] Launches in standalone mode
- [ ] No browser UI visible

**Test Steps**:
1. Visit site in Chrome
2. Wait 30 seconds
3. Click install prompt or address bar icon
4. Confirm installation
5. Launch from desktop/start menu

**Expected Result**: Smooth installation, native-like launch.

### 2. iOS Installation

**Safari iOS 14+**

- [ ] "Add to Home Screen" available
- [ ] Icon appears on home screen
- [ ] Splash screen shows
- [ ] Launches without Safari UI
- [ ] Status bar styled correctly
- [ ] No "Open in Safari" banner

**Test Steps**:
1. Open in Safari
2. Tap Share button
3. Tap "Add to Home Screen"
4. Confirm
5. Tap icon from home screen

**Expected Result**: App feels native, no browser chrome.

### 3. Android Installation

**Chrome Android**

- [ ] Install prompt appears
- [ ] "Add to Home Screen" available
- [ ] Icon appears on home screen
- [ ] App launches in standalone
- [ ] Splash screen displays
- [ ] Theme color applied

**Test Steps**:
1. Visit site in Chrome
2. Accept install prompt or use menu
3. Confirm installation
4. Launch from app drawer

**Expected Result**: Native-like installation and launch.

## 📲 Device API Testing

### 1. Geolocation

**Permission Required**

- [ ] Permission prompt appears
- [ ] Location acquired successfully
- [ ] Error handling for denied permission
- [ ] Timeout handled gracefully
- [ ] High accuracy mode works

**Test Code**:
```javascript
import { getCurrentLocation } from '@/lib/pwa-utils';

try {
  const position = await getCurrentLocation();
  console.log('Lat:', position.coords.latitude);
  console.log('Lng:', position.coords.longitude);
} catch (error) {
  console.error('Location error:', error);
}
```

**Expected Result**: Location acquired with proper error handling.

### 2. Camera Access

**Permission Required**

- [ ] Permission prompt appears
- [ ] Camera stream starts
- [ ] Video preview works
- [ ] Photo capture works
- [ ] Stream stops properly

**Test Code**:
```javascript
import { requestCameraAccess } from '@/lib/pwa-utils';

try {
  const stream = await requestCameraAccess();
  // Use stream for video element
  stream.getTracks().forEach(track => track.stop());
} catch (error) {
  console.error('Camera error:', error);
}
```

**Expected Result**: Camera access granted and functional.

### 3. Web Share API

**Mobile Devices**

- [ ] Share dialog appears
- [ ] Can share to installed apps
- [ ] Share text works
- [ ] Share URL works
- [ ] Share title works

**Test Code**:
```javascript
import { shareContent } from '@/lib/pwa-utils';

const shared = await shareContent({
  title: 'TutorMax',
  text: 'Check out this tutor performance!',
  url: window.location.href
});
```

**Expected Result**: Native share sheet appears with options.

### 4. Push Notifications

**Permission Required**

- [ ] Permission prompt appears
- [ ] Subscription created
- [ ] Notification sent successfully
- [ ] Notification appears
- [ ] Click action works
- [ ] Badge updates

**Test Steps**:
1. Request notification permission
2. Subscribe to push
3. Send test notification
4. Verify notification appears
5. Click notification
6. Check app badge

**Expected Result**: Notifications work end-to-end.

## 🌐 Network Awareness Testing

### 1. Connection Detection

**Network Panel**

- [ ] Online/offline status detected
- [ ] Connection type identified
- [ ] Slow connection warning shows
- [ ] Data saver mode respected
- [ ] Adaptive loading works

**Test Steps**:
1. Start online
2. Go offline
3. Come back online
4. Throttle to Slow 3G
5. Enable data saver

**Expected Result**: Appropriate UI feedback for all states.

### 2. Adaptive Image Loading

**Slow 3G Network**

- [ ] Low quality images load first
- [ ] High quality loads after delay
- [ ] Lazy loading works
- [ ] Images don't load if data saver enabled
- [ ] Skeleton placeholders shown

**Test Steps**:
1. Clear cache
2. Enable Slow 3G throttling
3. Scroll through image-heavy pages
4. Verify loading sequence

**Expected Result**: Progressive enhancement, bandwidth conscious.

## 🎯 Accessibility Testing

### 1. Keyboard Navigation

**Desktop**

- [ ] All interactive elements focusable
- [ ] Focus visible
- [ ] Tab order logical
- [ ] Skip links present
- [ ] Keyboard shortcuts work
- [ ] No focus traps

**Test Steps**:
1. Use only keyboard
2. Tab through all elements
3. Test Enter and Space keys
4. Verify focus visibility

**Expected Result**: Fully keyboard accessible.

### 2. Screen Reader

**NVDA/JAWS (Windows) or VoiceOver (Mac/iOS)**

- [ ] All content readable
- [ ] Images have alt text
- [ ] ARIA labels present
- [ ] Headings hierarchical
- [ ] Form labels associated
- [ ] Status messages announced

**Test Steps**:
1. Enable screen reader
2. Navigate through pages
3. Verify announcements
4. Test forms and buttons

**Expected Result**: Complete screen reader support.

### 3. Color Contrast

**Chrome DevTools or axe DevTools**

- [ ] Text meets WCAG AA (4.5:1)
- [ ] Large text meets WCAG AA (3:1)
- [ ] UI components meet WCAG AA (3:1)
- [ ] Focus indicators visible
- [ ] No color-only information

**Test Steps**:
1. Run axe DevTools audit
2. Check contrast ratios
3. Test in dark mode
4. Verify color blindness modes

**Expected Result**: All text passes WCAG AA.

## 📊 Performance Monitoring

### Using Built-in Hook

**Add to any component**:

```tsx
import { usePerformance, getPerformanceScore } from '@/hooks/usePerformance';

function PerformanceMonitor() {
  const metrics = usePerformance();
  const score = getPerformanceScore(metrics);

  return (
    <div>
      <h3>Performance Score: {score}/100</h3>
      <p>LCP: {metrics.lcp?.toFixed(0)}ms</p>
      <p>FID: {metrics.fid?.toFixed(0)}ms</p>
      <p>CLS: {metrics.cls?.toFixed(3)}</p>
      <p>FCP: {metrics.fcp?.toFixed(0)}ms</p>
      <p>TTFB: {metrics.ttfb?.toFixed(0)}ms</p>
    </div>
  );
}
```

## 🔍 Common Issues & Solutions

### Issue: Service Worker Not Updating

**Solution**:
```javascript
// In Chrome DevTools → Application → Service Workers
// 1. Check "Update on reload"
// 2. Click "Unregister"
// 3. Hard refresh (Cmd/Ctrl + Shift + R)
```

### Issue: Install Prompt Doesn't Show

**Solution**:
- Check console for errors
- Verify HTTPS or localhost
- Wait 30 seconds after page load
- Clear dismissed state: `localStorage.removeItem('pwa-install-dismissed')`

### Issue: Icons Not Displaying

**Solution**:
```bash
# Regenerate icons
pnpm run generate:pwa

# Verify paths in manifest.json match public/ files
```

### Issue: Offline Mode Not Working

**Solution**:
- Build production version (`pnpm build`)
- Check service worker is active
- Verify caching strategies in DevTools
- Check network requests in offline mode

## 📝 Test Results Template

```markdown
# PWA Test Results - [Date]

## Environment
- Browser: Chrome 120
- OS: macOS Sonoma
- Device: iPhone 14 Pro (real device)
- Network: Fast 4G

## Lighthouse Scores
- Performance: 95/100
- Accessibility: 98/100
- Best Practices: 100/100
- SEO: 100/100
- PWA: 100/100

## Core Web Vitals
- LCP: 1.8s ✅
- FID: 45ms ✅
- CLS: 0.05 ✅
- FCP: 1.2s ✅
- TTFB: 420ms ✅

## Installation Testing
- Desktop: ✅ Passed
- iOS: ✅ Passed
- Android: ✅ Passed

## Issues Found
1. [Description]
   - Severity: High/Medium/Low
   - Steps to reproduce
   - Expected vs Actual

## Recommendations
1. [Recommendation]
2. [Recommendation]
```

## 🎓 Resources

- [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci)
- [WebPageTest](https://www.webpagetest.org/)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)
- [PWA Builder](https://www.pwabuilder.com/)
