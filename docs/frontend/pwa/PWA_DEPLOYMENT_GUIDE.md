# PWA Deployment Guide - TutorMax

## Overview

This guide covers deploying the TutorMax Progressive Web App to production with optimal performance and PWA features enabled.

## Prerequisites

- [x] Production build passes
- [x] Service Worker implemented
- [x] Manifest.json configured
- [x] HTTPS certificate ready
- [ ] Environment variables configured
- [ ] CDN/hosting platform selected

## Deployment Platforms

### Option 1: Vercel (Recommended)

Vercel provides automatic HTTPS, optimal caching, and edge network deployment.

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy to production
cd frontend
vercel --prod

# Configure environment variables in Vercel dashboard
# - NEXT_PUBLIC_API_URL
```

**Advantages**:
- ✅ Automatic HTTPS
- ✅ Edge network (CDN)
- ✅ Zero-config deployment
- ✅ Automatic invalidation
- ✅ Preview deployments

### Option 2: Render

Already configured in `render.yaml` for backend. Can host static frontend.

```yaml
# render.yaml (add frontend service)
services:
  - type: web
    name: tutormax-frontend
    env: static
    buildCommand: cd frontend && pnpm install && pnpm build
    staticPublishPath: frontend/.next
    headers:
      - path: /sw.js
        name: Service-Worker-Allowed
        value: /
      - path: /sw.js
        name: Cache-Control
        value: public, max-age=0, must-revalidate
```

### Option 3: Cloudflare Pages

Free tier with excellent PWA support.

```bash
# Deploy via Git integration or CLI
npx wrangler pages deploy frontend/.next --project-name=tutormax
```

### Option 4: Self-Hosted (Docker)

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

## Configuration

### 1. Environment Variables

Create `.env.production`:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://api.tutormax.com
NEXT_PUBLIC_WS_URL=wss://api.tutormax.com/ws

# Optional: Analytics
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
```

### 2. Service Worker Headers

Ensure your hosting platform serves Service Worker with correct headers:

```nginx
# For nginx
location /sw.js {
    add_header Cache-Control "public, max-age=0, must-revalidate";
    add_header Service-Worker-Allowed "/";
}

location /manifest.json {
    add_header Cache-Control "public, max-age=604800, immutable";
}

location ~* \.(png|jpg|jpeg|svg|webp|avif|ico)$ {
    add_header Cache-Control "public, max-age=31536000, immutable";
}
```

### 3. Caching Strategy

```javascript
// next.config.ts includes optimal caching
// Verify these settings are applied:

module.exports = {
  output: 'standalone', // For Docker deployments
  compress: true,       // Gzip compression
  poweredByHeader: false, // Remove X-Powered-By

  headers: async () => [
    {
      source: '/sw.js',
      headers: [
        {
          key: 'Cache-Control',
          value: 'public, max-age=0, must-revalidate',
        },
        {
          key: 'Service-Worker-Allowed',
          value: '/',
        },
      ],
    },
  ],
};
```

## Pre-Deployment Checklist

### Build Verification
```bash
cd frontend

# 1. Clean build
rm -rf .next node_modules/.cache
pnpm install
pnpm build

# 2. Verify build output
ls -lh .next/static
ls -lh public/sw.js

# 3. Test production locally
pnpm start
# Open http://localhost:3000
```

### PWA Validation
```bash
# 1. Check Service Worker registration
# Open DevTools > Application > Service Workers

# 2. Verify manifest
# Open DevTools > Application > Manifest

# 3. Test offline mode
# DevTools > Network > Offline checkbox

# 4. Run Lighthouse audit
# DevTools > Lighthouse > Generate report
```

### Security Headers
```nginx
# Add to nginx or hosting config
add_header X-Frame-Options "SAMEORIGIN";
add_header X-Content-Type-Options "nosniff";
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline';";
```

## Deployment Steps

### 1. Build for Production

```bash
cd frontend

# Install dependencies
pnpm install --frozen-lockfile

# Run type checking
pnpm type-check

# Build optimized bundle
pnpm build

# Verify build size
du -sh .next
```

### 2. Deploy to Platform

#### Vercel:
```bash
vercel --prod
```

#### Render:
```bash
git push origin main
# Render auto-deploys on push
```

#### Docker:
```bash
docker build -t tutormax-frontend .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=https://api.tutormax.com tutormax-frontend
```

### 3. Post-Deployment Verification

```bash
# 1. Check HTTPS
curl -I https://tutormax.com

# 2. Verify Service Worker
curl https://tutormax.com/sw.js

# 3. Check manifest
curl https://tutormax.com/manifest.json

# 4. Test API connectivity
curl https://tutormax.com/api/health
```

## Monitoring & Analytics

### 1. Web Vitals Tracking

Already implemented in `usePerformance.ts`:

```typescript
// Automatically tracks:
// - FCP (First Contentful Paint)
// - LCP (Largest Contentful Paint)
// - FID (First Input Delay)
// - CLS (Cumulative Layout Shift)
// - TTFB (Time to First Byte)
```

### 2. PWA Installation Tracking

Add to your analytics:

```typescript
// Track install prompt shown
window.addEventListener('beforeinstallprompt', (e) => {
  analytics.track('PWA Install Prompt Shown');
});

// Track installation
window.addEventListener('appinstalled', () => {
  analytics.track('PWA Installed');
});
```

### 3. Service Worker Analytics

Monitor Service Worker lifecycle:

```typescript
// In ServiceWorkerRegistration component
navigator.serviceWorker.addEventListener('controllerchange', () => {
  analytics.track('Service Worker Updated');
});
```

### 4. Recommended Monitoring Tools

**Performance Monitoring**:
- Google Analytics 4 (Web Vitals)
- Sentry (Error tracking)
- New Relic (APM)
- Vercel Analytics (if using Vercel)

**PWA Specific**:
- Chrome DevTools Lighthouse
- PageSpeed Insights
- WebPageTest.org

## Performance Optimization

### 1. Lighthouse Audit

Run regular Lighthouse audits:

```bash
# Install Lighthouse CLI
npm install -g lighthouse

# Run audit
lighthouse https://tutormax.com \
  --output=html \
  --output-path=./lighthouse-report.html \
  --view

# CI/CD integration
lighthouse https://tutormax.com \
  --preset=desktop \
  --chrome-flags="--headless" \
  --quiet \
  --output=json \
  --output-path=./lighthouse-results.json
```

**Target Scores**:
- PWA: 90+
- Performance: 90+
- Accessibility: 95+
- Best Practices: 95+
- SEO: 90+

### 2. Bundle Analysis

```bash
cd frontend

# Analyze bundle size
pnpm build:analyze

# Opens bundle analyzer in browser
```

**Optimization Tips**:
- Keep main bundle < 200KB (gzipped)
- Lazy load heavy components
- Use dynamic imports for routes
- Optimize images with sharp

### 3. Caching Optimization

Monitor cache effectiveness:

```javascript
// Add to Service Worker analytics
self.addEventListener('fetch', (event) => {
  const startTime = performance.now();

  event.respondWith(
    caches.match(event.request).then((response) => {
      const cacheHit = !!response;
      const endTime = performance.now();

      // Track cache performance
      if (cacheHit) {
        console.log(`Cache hit: ${event.request.url} (${endTime - startTime}ms)`);
      }

      return response || fetch(event.request);
    })
  );
});
```

## Troubleshooting

### Service Worker Not Registering

**Issue**: Service Worker fails to register in production

**Solutions**:
1. Verify HTTPS is enabled
2. Check Service-Worker-Allowed header
3. Verify sw.js is served from root path
4. Check browser console for errors

```bash
# Test Service Worker manually
curl -I https://tutormax.com/sw.js

# Should return:
# Cache-Control: public, max-age=0, must-revalidate
# Service-Worker-Allowed: /
```

### App Not Installable

**Issue**: Install prompt doesn't appear

**Checklist**:
- [ ] HTTPS enabled
- [ ] manifest.json valid and accessible
- [ ] Service Worker registered
- [ ] All required icons present
- [ ] Display mode set to "standalone"
- [ ] start_url accessible

```bash
# Validate manifest
curl https://tutormax.com/manifest.json | jq

# Check icons
curl -I https://tutormax.com/icon-192x192.png
```

### Offline Mode Not Working

**Issue**: Pages don't load offline

**Debug Steps**:

1. Check Service Worker status:
```javascript
navigator.serviceWorker.getRegistration().then(reg => {
  console.log('SW status:', reg.active ? 'active' : 'inactive');
});
```

2. Verify cache:
```javascript
caches.keys().then(keys => {
  console.log('Cache keys:', keys);
});
```

3. Test cache match:
```javascript
caches.match('/').then(response => {
  console.log('Root cached:', !!response);
});
```

### Performance Issues

**Issue**: Slow load times on mobile

**Optimization**:

1. Enable compression:
```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript;
gzip_min_length 1000;
```

2. Optimize images:
```bash
# Use sharp for image optimization
npm install sharp

# Optimize in build
node scripts/optimize-images.js
```

3. Reduce bundle size:
```bash
# Analyze and reduce
pnpm build:analyze

# Remove unused dependencies
npx depcheck
```

## Rollback Plan

### Quick Rollback

```bash
# Vercel
vercel rollback

# Render
# Use Render dashboard to redeploy previous commit

# Docker
docker run -p 3000:3000 tutormax-frontend:previous-tag
```

### Service Worker Update

If Service Worker causes issues:

```javascript
// Emergency SW bypass (add to public/sw-bypass.js)
navigator.serviceWorker.getRegistrations().then(registrations => {
  registrations.forEach(reg => reg.unregister());
});
```

## Maintenance

### Regular Tasks

**Weekly**:
- [ ] Run Lighthouse audit
- [ ] Check Web Vitals metrics
- [ ] Review error logs
- [ ] Monitor cache hit rate

**Monthly**:
- [ ] Update dependencies
- [ ] Review bundle size
- [ ] Test on new devices/browsers
- [ ] Update Service Worker cache version

**Quarterly**:
- [ ] Security audit
- [ ] Performance review
- [ ] User feedback analysis
- [ ] PWA feature usage analysis

### Service Worker Updates

When updating Service Worker:

```bash
# 1. Update CACHE_VERSION in sw.js
const CACHE_VERSION = 'v2';

# 2. Deploy new version

# 3. Users automatically get update notification

# 4. Monitor rollout
# Check SW version adoption rate
```

## Success Metrics

### Key Performance Indicators

**Technical Metrics**:
- Lighthouse PWA score > 90
- Page load time < 3s on 3G
- Service Worker activation rate > 80%
- Cache hit rate > 70%

**User Metrics**:
- PWA install rate
- Return visit rate (PWA vs web)
- Offline usage sessions
- Feature adoption (camera, geolocation, etc.)

**Business Metrics**:
- User engagement increase
- Session duration
- Bounce rate reduction
- Mobile conversion rate

## Additional Resources

- [PWA_IMPLEMENTATION.md](./PWA_IMPLEMENTATION.md) - Implementation details
- [PWA_TESTING_REPORT.md](./PWA_TESTING_REPORT.md) - Testing results
- [Web.dev PWA Checklist](https://web.dev/pwa-checklist/)
- [Next.js Deployment Docs](https://nextjs.org/docs/deployment)

---

**Status**: Ready for Deployment ✅
**Last Updated**: November 9, 2025
