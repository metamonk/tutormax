# Animation System Documentation

This document describes the animation system used throughout the TutorMax application.

## Overview

The animation system is built on top of Tailwind CSS v4 and provides:
- Consistent animation timing and easing
- Accessibility support (prefers-reduced-motion)
- Performance-optimized animations
- Reusable animation utilities
- React hooks for dynamic animations

## Files

- `lib/animations.ts` - Core animation utilities and configurations
- `hooks/use-animations.ts` - React hooks for animations
- `app/globals.css` - Animation keyframes and utility classes

## Quick Start

### Using CSS Classes

```tsx
import { Button } from '@/components/ui/button';

// Button with hover scale effect
<Button className="hover-scale">
  Click me
</Button>

// Card with hover lift effect
<div className="transition-card hover-lift">
  Card content
</div>

// Fade in animation
<div className="animate-fade-in">
  Content
</div>
```

### Using Animation Utilities

```tsx
import { animationClasses, combineAnimations } from '@/lib/animations';

// Button with combined animations
<button
  className={combineAnimations(
    animationClasses.button.base,
    animationClasses.button.hover,
    animationClasses.button.focus
  )}
>
  Click me
</button>

// Card with interactive animations
<div
  className={combineAnimations(
    animationClasses.card.base,
    animationClasses.card.interactive
  )}
>
  Card content
</div>
```

### Using React Hooks

```tsx
import { usePrefersReducedMotion, useStaggeredAnimation } from '@/hooks/use-animations';

function MyComponent() {
  const prefersReducedMotion = usePrefersReducedMotion();
  const staggerDelays = useStaggeredAnimation(items.length);

  return (
    <div>
      {items.map((item, index) => (
        <div
          key={item.id}
          style={{
            animationDelay: `${staggerDelays[index]}ms`,
          }}
          className={!prefersReducedMotion ? 'animate-slide-in-bottom' : ''}
        >
          {item.content}
        </div>
      ))}
    </div>
  );
}
```

## Available Animations

### CSS Classes

#### Duration Classes
- `.animate-fast` - 150ms
- `.animate-normal` - 250ms (default)
- `.animate-slow` - 350ms
- `.animate-slower` - 500ms

#### Entry Animations
- `.animate-fade-in` - Fade in
- `.animate-slide-in-bottom` - Slide in from bottom
- `.animate-slide-in-top` - Slide in from top
- `.animate-slide-in-left` - Slide in from left
- `.animate-slide-in-right` - Slide in from right
- `.animate-scale-in` - Scale in

#### Exit Animations
- `.animate-fade-out` - Fade out
- `.animate-scale-out` - Scale out

#### Interactive Effects
- `.hover-scale` - Scale on hover, reduce on active
- `.hover-lift` - Lift on hover (translate up)
- `.transition-interactive` - General interactive transitions
- `.transition-card` - Card-specific transitions
- `.focus-ring` - Focus ring with offset

#### Loading Animations
- `.skeleton` - Skeleton loading animation
- `.shimmer` - Shimmer effect
- `.pulse-ring` - Pulse animation for notifications
- `.bounce-subtle` - Subtle bounce effect

### Animation Keyframes

Custom keyframes defined in `globals.css`:

- `skeleton-loading` - Gradient background animation
- `shimmer` - Shimmer effect for loading states
- `pulse-ring` - Pulsing ring animation
- `bounce-subtle` - Subtle bounce
- `slide-in-bottom/top/left/right` - Slide animations
- `scale-in/out` - Scale animations
- `fade-in/out` - Fade animations
- `progress-indeterminate` - Indeterminate progress bar

## Animation Configuration

### Timing Functions

```typescript
import { animationEasing } from '@/lib/animations';

// Available easing functions
animationEasing.easeInOut  // cubic-bezier(0.4, 0, 0.2, 1)
animationEasing.easeOut    // cubic-bezier(0, 0, 0.2, 1)
animationEasing.easeIn     // cubic-bezier(0.4, 0, 1, 1)
animationEasing.spring     // cubic-bezier(0.34, 1.56, 0.64, 1)
animationEasing.bounce     // cubic-bezier(0.68, -0.55, 0.265, 1.55)
```

### Duration Values

```typescript
import { animationDuration } from '@/lib/animations';

// Available durations
animationDuration.fast    // 150ms
animationDuration.normal  // 250ms
animationDuration.slow    // 350ms
animationDuration.slower  // 500ms
```

## Accessibility

### Prefers-Reduced-Motion Support

All animations automatically respect the `prefers-reduced-motion` media query:

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Using Hooks for Reduced Motion

```tsx
import { usePrefersReducedMotion } from '@/hooks/use-animations';

function MyComponent() {
  const prefersReducedMotion = usePrefersReducedMotion();

  return (
    <div
      className={prefersReducedMotion ? '' : 'animate-fade-in'}
    >
      Content
    </div>
  );
}
```

## Performance Optimization

### GPU Acceleration

Use these classes to promote elements to their own GPU layer:

```tsx
<div className="transform-gpu">
  Animated content
</div>
```

### Will-Change

For frequently animated elements:

```tsx
<div className="will-change-transform">
  Frequently animated content
</div>
```

### Best Practices

1. **Use `transform` and `opacity`** - These properties are GPU-accelerated
2. **Avoid animating `width`, `height`, `top`, `left`** - These trigger layout recalculations
3. **Use `will-change` sparingly** - Only on elements that will definitely animate
4. **Remove `will-change` after animation** - To free up GPU memory

## Common Patterns

### Button Animations

```tsx
import { animationClasses } from '@/lib/animations';

<button
  className={`
    ${animationClasses.button.base}
    ${animationClasses.button.hover}
    ${animationClasses.button.focus}
  `}
>
  Click me
</button>
```

### Card Animations

```tsx
import { animationClasses } from '@/lib/animations';

<div
  className={`
    ${animationClasses.card.base}
    ${animationClasses.card.hover}
  `}
>
  Card content
</div>
```

### List Item Stagger

```tsx
import { useStaggeredAnimation } from '@/hooks/use-animations';

function List({ items }) {
  const staggerDelays = useStaggeredAnimation(items.length);

  return (
    <div>
      {items.map((item, index) => (
        <div
          key={item.id}
          className="animate-slide-in-bottom"
          style={{ animationDelay: `${staggerDelays[index]}ms` }}
        >
          {item.content}
        </div>
      ))}
    </div>
  );
}
```

### Loading States

```tsx
// Skeleton loading
<div className="h-4 w-full rounded skeleton" />

// Shimmer effect
<div className="shimmer">
  <div className="h-20 w-full bg-muted rounded" />
</div>

// Pulse notification
<div className="pulse-ring">
  <BellIcon />
</div>
```

## Examples

### Modal/Dialog Animation

```tsx
import { animationClasses } from '@/lib/animations';

<Dialog>
  <DialogContent
    className={`
      ${animationClasses.scale.in}
      ${animationClasses.fade.in}
    `}
  >
    Dialog content
  </DialogContent>
</Dialog>
```

### Page Transitions

```tsx
'use client';

import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';

export function PageTransition({ children }) {
  const pathname = usePathname();
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    setIsVisible(false);
    const timeout = setTimeout(() => setIsVisible(true), 50);
    return () => clearTimeout(timeout);
  }, [pathname]);

  return (
    <div className={isVisible ? 'animate-fade-in' : 'opacity-0'}>
      {children}
    </div>
  );
}
```

### Tooltip Animation

```tsx
<Tooltip>
  <TooltipContent
    className="animate-slide-in-top"
  >
    Tooltip text
  </TooltipContent>
</Tooltip>
```

## Testing Animations

### Testing Reduced Motion

In your browser DevTools:

1. Open DevTools (F12)
2. Open Command Palette (Cmd/Ctrl + Shift + P)
3. Search for "Emulate CSS prefers-reduced-motion"
4. Toggle to test both modes

### Performance Testing

Use Chrome DevTools Performance tab:

1. Record while interacting with animated elements
2. Look for layout thrashing (yellow bars)
3. Check FPS (should maintain 60fps)
4. Verify GPU acceleration is active
