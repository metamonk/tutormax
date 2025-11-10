# TutorMax PWA - Quick Reference Card

## 🚀 Quick Start

```bash
# Development (PWA disabled)
pnpm dev

# Production (PWA enabled)
pnpm build && pnpm start

# Generate PWA assets
pnpm run generate:pwa
```

## 📱 React Hooks

### PWA Installation
```tsx
import { usePWA } from '@/hooks/usePWA';

function InstallButton() {
  const { isInstalled, isInstallable, promptInstall } = usePWA();

  if (isInstalled || !isInstallable) return null;

  return <button onClick={promptInstall}>Install App</button>;
}
```

### Service Worker
```tsx
import { useServiceWorker } from '@/hooks/useServiceWorker';

function UpdateChecker() {
  const { isUpdateAvailable, skipWaiting } = useServiceWorker();

  return isUpdateAvailable ? (
    <button onClick={skipWaiting}>Update Now</button>
  ) : null;
}
```

### Network Status
```tsx
import { useNetworkStatus } from '@/hooks/useNetworkStatus';

function NetworkBanner() {
  const { online, effectiveType, isSlowConnection } = useNetworkStatus();

  return (
    <div>
      {!online && <p>You're offline</p>}
      {isSlowConnection && <p>Slow connection: {effectiveType}</p>}
    </div>
  );
}
```

### Performance Metrics
```tsx
import { usePerformance, getPerformanceScore } from '@/hooks/usePerformance';

function PerformanceMonitor() {
  const metrics = usePerformance();
  const score = getPerformanceScore(metrics);

  return (
    <div>
      <p>Score: {score}/100</p>
      <p>LCP: {metrics.lcp}ms</p>
      <p>FID: {metrics.fid}ms</p>
      <p>CLS: {metrics.cls}</p>
    </div>
  );
}
```

## 🛠️ PWA Utilities

### Device Detection
```typescript
import {
  isPWA,
  canInstallPWA,
  hasTouch,
  isLandscape,
  getDevicePixelRatio
} from '@/lib/pwa-utils';

// Check if running as PWA
if (isPWA()) {
  console.log('Running as installed PWA');
}

// Check if installable
if (canInstallPWA()) {
  console.log('Can show install prompt');
}

// Check touch support
if (hasTouch()) {
  console.log('Touch device');
}
```

### Network Information
```typescript
import {
  getNetworkInfo,
  isSlowConnection,
  hasDataSaver
} from '@/lib/pwa-utils';

const connection = getNetworkInfo();
console.log('Type:', connection?.effectiveType); // '4g'
console.log('Downlink:', connection?.downlink, 'Mbps');
console.log('RTT:', connection?.rtt, 'ms');

if (isSlowConnection()) {
  // Load lower quality assets
}

if (hasDataSaver()) {
  // Skip non-essential loading
}
```

### Geolocation
```typescript
import { getCurrentLocation, hasGeolocation } from '@/lib/pwa-utils';

if (hasGeolocation()) {
  const position = await getCurrentLocation();
  const { latitude, longitude } = position.coords;
  console.log(`Location: ${latitude}, ${longitude}`);
}
```

### Camera Access
```typescript
import { requestCameraAccess, hasCameraAccess } from '@/lib/pwa-utils';

if (hasCameraAccess()) {
  const stream = await requestCameraAccess();
  videoElement.srcObject = stream;

  // Stop when done
  stream.getTracks().forEach(track => track.stop());
}
```

### Notifications
```typescript
import {
  requestNotificationPermission,
  showNotification
} from '@/lib/pwa-utils';

// Request permission
const permission = await requestNotificationPermission();

if (permission === 'granted') {
  // Show notification
  await showNotification('New Alert', {
    body: 'Tutor performance update available',
    icon: '/icon-192x192.png',
    badge: '/icon-72x72.png',
    vibrate: [200, 100, 200],
    tag: 'performance-update',
    requireInteraction: true
  });
}
```

### Biometric Auth
```typescript
import {
  hasBiometricAuth,
  authenticateWithBiometrics
} from '@/lib/pwa-utils';

if (hasBiometricAuth()) {
  const authenticated = await authenticateWithBiometrics();
  if (authenticated) {
    // Proceed with secure action
  }
}
```

### Web Share
```typescript
import { shareContent } from '@/lib/pwa-utils';

const shared = await shareContent({
  title: 'TutorMax Performance',
  text: 'Check out this tutor\'s progress!',
  url: window.location.href
});

if (shared) {
  console.log('Content shared successfully');
}
```

### Vibration
```typescript
import { vibrate } from '@/lib/pwa-utils';

// Single vibration
vibrate(200);

// Pattern (vibrate, pause, vibrate)
vibrate([200, 100, 200]);
```

## 🎨 UI Components

### Lazy Loading Images
```tsx
import { LazyImage } from '@/components/ui/lazy-image';

<LazyImage
  src="/high-quality.jpg"
  lowQualitySrc="/low-quality.jpg"  // Optional LQIP
  alt="Tutor profile"
  aspectRatio="1/1"
  priority={false}  // true for above-the-fold
  className="rounded-lg"
/>
```

### PWA Components
```tsx
import {
  InstallPrompt,
  UpdateNotification,
  OfflineIndicator,
  MobileNav
} from '@/components/pwa';

// In app/layout.tsx (already added)
<OfflineIndicator />
<UpdateNotification />
<MobileNav />
<InstallPrompt />
```

## 🎯 Mobile CSS Utilities

### Safe Area Insets
```css
/* Use for notched devices */
.safe-area-inset-top { padding-top: env(safe-area-inset-top); }
.safe-area-inset-bottom { padding-bottom: env(safe-area-inset-bottom); }
.pb-safe { padding-bottom: max(1rem, env(safe-area-inset-bottom)); }
```

### Touch Optimization
```css
/* Minimum tap target size */
.touch-target { min-width: 44px; min-height: 44px; }

/* Remove tap highlight */
.no-tap-highlight { -webkit-tap-highlight-color: transparent; }

/* Smooth scrolling on iOS */
.momentum-scroll { -webkit-overflow-scrolling: touch; }
```

### Loading States
```css
/* Animated skeleton placeholder */
.skeleton {
  background: linear-gradient(90deg, ...);
  animation: skeleton-loading 1.5s ease-in-out infinite;
}
```

## 🔧 Next.js Configuration

### PWA Config
```typescript
// next.config.ts
import withPWA from 'next-pwa';

export default withPWA({
  dest: 'public',
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === 'development',
  runtimeCaching: [
    {
      urlPattern: /^https?.*/,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'offlineCache',
        expiration: { maxEntries: 200 }
      }
    }
  ]
})(nextConfig);
```

### Viewport Config
```typescript
// app/layout.tsx
export const viewport: Viewport = {
  themeColor: "#3b82f6",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  viewportFit: "cover",
};
```

### Metadata Config
```typescript
export const metadata: Metadata = {
  title: "TutorMax",
  applicationName: "TutorMax",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "TutorMax",
  },
  manifest: "/manifest.json",
};
```

## 📊 Performance Targets

### Lighthouse Scores (Target: ≥90)
- Performance: 90+
- Accessibility: 90+
- Best Practices: 90+
- SEO: 90+
- PWA: 90+

### Core Web Vitals (Good Thresholds)
- LCP: < 2.5s
- FID: < 100ms
- CLS: < 0.1
- FCP: < 1.8s
- TTFB: < 600ms

### Mobile Performance
- 3G Load: < 3s
- Bundle Size: < 500KB (gzipped)

## 🧪 Testing Commands

```bash
# Run Lighthouse audit
npx lighthouse http://localhost:3000 --view

# Check bundle size
pnpm build
# Look for "First Load JS" in output

# Test offline (Chrome DevTools)
# Network tab → Throttling → Offline

# Test on mobile device
# Use ngrok for HTTPS tunnel
npx ngrok http 3000
```

## 🐛 Troubleshooting

### Service Worker Not Registering
```bash
# Must build for production
pnpm build && pnpm start

# SW disabled in dev mode by default
```

### Install Prompt Not Showing
```javascript
// Clear dismissed state
localStorage.removeItem('pwa-install-dismissed');

// Wait 30 seconds after page load
// Must be HTTPS or localhost
```

### Icons Not Loading
```bash
# Regenerate icons
pnpm run generate:icons

# Check paths match manifest.json
```

### Offline Not Working
```bash
# Check service worker status
# DevTools → Application → Service Workers

# Verify caching strategy
# DevTools → Application → Cache Storage
```

## 📱 Browser Support

| Browser | Version | Support |
|---------|---------|---------|
| Chrome Desktop | 80+ | ✅ Full |
| Chrome Android | 80+ | ✅ Full |
| Safari iOS | 14+ | ✅ Full* |
| Safari macOS | 14+ | ✅ Full* |
| Firefox | 90+ | ✅ Full |
| Edge | 80+ | ✅ Full |
| Samsung Internet | 12+ | ✅ Full |

*No push notifications on iOS

## 📚 Key Files

```
frontend/
├── hooks/
│   ├── usePWA.ts              # Install logic
│   ├── useServiceWorker.ts    # SW state
│   ├── useNetworkStatus.ts    # Network info
│   └── usePerformance.ts      # Metrics
├── lib/
│   └── pwa-utils.ts           # All utilities
├── components/
│   ├── pwa/                   # PWA components
│   └── ui/lazy-image.tsx      # Image optimization
├── public/
│   ├── manifest.json          # PWA manifest
│   └── icon-*.png            # Icons
└── next.config.ts             # PWA config
```

## 🔗 Resources

- [Implementation Guide](./PWA_IMPLEMENTATION.md)
- [Testing Guide](./PWA_TESTING_GUIDE.md)
- [Task Summary](./TASK_13_IMPLEMENTATION_SUMMARY.md)
