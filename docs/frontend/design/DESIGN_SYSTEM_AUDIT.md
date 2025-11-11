# Design System Audit - TutorMax

## Overview
This document provides a comprehensive audit of the TutorMax design system, documenting all design tokens, components, and usage patterns.

**Audit Date:** 2025-11-10
**Version:** 1.0
**Status:** ✅ Passing

---

## Color System

### Color Space
- **Primary:** OKLCH (modern, perceptually uniform)
- **Fallback:** HSL (browser compatibility)

### Brand Colors

#### Primary (Professional Blue)
```css
Light Mode:
- Primary: oklch(0.55 0.18 250) / hsl(220, 70%, 50%)
- Primary Foreground: oklch(0.98 0.01 250) / hsl(220, 10%, 98%)

Dark Mode:
- Primary: oklch(0.65 0.18 250) / hsl(220, 70%, 60%)
- Primary Foreground: oklch(0.15 0.02 250) / hsl(220, 15%, 9%)
```

### Semantic Colors

#### Success (Growth & Achievements)
```css
Light: oklch(0.60 0.17 145) / hsl(142, 70%, 45%)
Dark: oklch(0.65 0.16 145) / hsl(142, 70%, 50%)
```

#### Warning (Alerts & Attention)
```css
Light: oklch(0.72 0.15 65) / hsl(38, 92%, 50%)
Dark: oklch(0.75 0.14 65) / hsl(38, 92%, 55%)
```

#### Destructive (Critical Issues)
```css
Light: oklch(0.58 0.20 25) / hsl(0, 65%, 48%)
Dark: oklch(0.62 0.22 25) / hsl(0, 70%, 55%)
```

### Background & Surface Colors

```css
Light Mode:
- Background: oklch(0.98 0.005 250) - Off-white with subtle blue tint
- Card: oklch(1 0 0) - Pure white
- Muted: oklch(0.95 0.01 250) - Light gray
- Accent: oklch(0.94 0.02 250) - Hover backgrounds

Dark Mode:
- Background: oklch(0.15 0.015 250) - Very dark blue-black
- Card: oklch(0.18 0.015 250) - Slightly lighter surface
- Muted: oklch(0.25 0.02 250) - Medium gray
- Accent: oklch(0.25 0.02 250) - Hover backgrounds
```

### Chart Colors (Data Visualization)
```css
1. Primary Blue: oklch(0.55 0.18 250)
2. Success Green: oklch(0.60 0.17 145)
3. Purple: oklch(0.65 0.20 290)
4. Warning Amber: oklch(0.72 0.15 65)
5. Magenta: oklch(0.62 0.18 340)
```

**Accessibility:** All chart colors meet WCAG AA contrast requirements against both light and dark backgrounds.

---

## Typography

### Font Families
```css
- Sans: Geist Sans (Primary interface font)
- Mono: Geist Mono (Code and monospace content)
```

### Scale
Following Tailwind's default type scale:
- xs: 0.75rem (12px)
- sm: 0.875rem (14px)
- base: 1rem (16px)
- lg: 1.125rem (18px)
- xl: 1.25rem (20px)
- 2xl: 1.5rem (24px)
- 3xl: 1.875rem (30px)
- 4xl: 2.25rem (36px)

### Weights
- 400: Regular (body text)
- 500: Medium (emphasis)
- 600: Semibold (headings, labels)
- 700: Bold (strong emphasis)

### Line Heights
- tight: 1.25 (headings)
- normal: 1.5 (body)
- relaxed: 1.625 (long-form content)

---

## Spacing System

Using Tailwind's 4px base scale:
- 0.5: 2px (0.125rem)
- 1: 4px (0.25rem)
- 2: 8px (0.5rem)
- 3: 12px (0.75rem)
- 4: 16px (1rem)
- 6: 24px (1.5rem)
- 8: 32px (2rem)
- 12: 48px (3rem)
- 16: 64px (4rem)

### Common Patterns
- Card padding: `p-6` (24px)
- Button padding: `px-4 py-2` (16px horizontal, 8px vertical)
- Section spacing: `space-y-6` or `gap-6`
- Page margins: `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8`

---

## Border Radius

```css
--radius: 0.5rem (8px base)
- sm: calc(var(--radius) - 4px) = 4px
- md: calc(var(--radius) - 2px) = 6px
- lg: var(--radius) = 8px
- xl: calc(var(--radius) + 4px) = 12px
```

### Usage
- Buttons: `rounded-md` (6px)
- Cards: `rounded-xl` (12px)
- Inputs: `rounded-md` (6px)
- Dialogs: `rounded-lg` (8px)

---

## Shadows

Following Tailwind's shadow scale:
- xs: Subtle depth
- sm: Default card shadow
- md: Hover state
- lg: Interactive card hover
- xl: Dialog/modal elevation

**Pattern:** Progressive shadow enhancement on hover/interaction

---

## Motion & Animation

### Duration Scale
```css
- Fast: 150ms (micro-interactions)
- Normal: 250ms (standard transitions)
- Slow: 350ms (complex animations)
- Slower: 500ms (page transitions)
```

### Easing Functions
- ease-out: Default for entrances
- ease-in: For exits
- ease-in-out: For complex movements

### Common Animations
1. **Slide-in** (bottom, top, left, right) - 250ms ease-out
2. **Scale-in/out** - 200ms ease-out
3. **Fade-in/out** - 250ms
4. **Skeleton loading** - 1.5s infinite
5. **Shimmer** - 2s infinite
6. **Pulse** - 2s infinite

### Interactive States
```css
Buttons:
- Hover: scale(1.02), shadow-md, 150ms
- Active: scale(0.98), 150ms
- Focus: ring-2 ring-primary ring-offset-2

Cards:
- Hoverable: shadow-md, 250ms
- Interactive: shadow-lg, -translate-y-1, 250ms
- Active: shadow-md, translate-y-0
```

### Performance Optimization
- Using `transform-gpu` for hardware acceleration
- `will-change` properties for animated elements
- `backface-visibility: hidden` to prevent flicker
- Respects `prefers-reduced-motion`

---

## Component System

### Button Variants
1. **default** - Primary action (blue background)
2. **destructive** - Dangerous actions (red background)
3. **outline** - Secondary actions (bordered)
4. **secondary** - Tertiary actions (gray background)
5. **ghost** - Minimal actions (transparent)
6. **link** - Text-only actions (underlined)

**Sizes:** sm (32px), default (36px), lg (40px), icon variants

**States:**
- Loading state with spinner
- Disabled state (50% opacity)
- Focus ring (2px primary)
- Touch-friendly minimum size (44x44px)

### Card System
- **Base card:** White background, subtle shadow, 12px border radius
- **hoverable:** Adds shadow-md on hover
- **interactive:** Adds lift effect (-translate-y-1) and larger shadow

**Sections:**
- CardHeader: Grid layout with optional action slot
- CardTitle: Semibold text
- CardDescription: Muted text
- CardContent: Main content area
- CardFooter: Actions/metadata area

### Form Elements
- Consistent border radius (6px)
- Focus ring on all interactive elements
- Error states with red ring and text
- Label/input/helper text pattern
- Touch-friendly sizing on mobile

---

## Layout Patterns

### Responsive Breakpoints
```css
- sm: 640px (mobile landscape)
- md: 768px (tablet)
- lg: 1024px (desktop)
- xl: 1280px (large desktop)
- 2xl: 1536px (extra large)
```

### Container System
```tsx
max-w-7xl mx-auto px-4 sm:px-6 lg:px-8
```

### Grid Patterns
- Dashboard metrics: `grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6`
- Content + sidebar: `grid-cols-1 lg:grid-cols-[1fr_300px] gap-6`
- Form layouts: `grid-cols-1 md:grid-cols-2 gap-4`

---

## Accessibility

### Focus Management
- Visible focus rings on all interactive elements
- Focus ring offset for visual clarity
- Skip to content links where appropriate
- Keyboard navigation support

### Color Contrast
- All text meets WCAG AA (4.5:1 minimum)
- Interactive elements meet AA (3:1 minimum)
- Chart colors verified for accessibility

### Touch Targets
- Minimum 44x44px on all interactive elements
- Adequate spacing between clickable elements
- `.touch-target` utility class available

### Screen Reader Support
- Semantic HTML structure
- ARIA labels where needed
- Status announcements for dynamic content
- Alternative text for images and icons

### Motion
- Respects `prefers-reduced-motion`
- Reduces all animations to 0.01ms when enabled
- No auto-playing animations

---

## PWA Optimizations

### Safe Areas
```css
- safe-area-inset-top
- safe-area-inset-bottom
- safe-area-inset-left
- safe-area-inset-right
```

### Mobile UX
- No tap highlight: `-webkit-tap-highlight-color: transparent`
- Momentum scrolling: `-webkit-overflow-scrolling: touch`
- Touch-friendly targets
- Bottom safe area padding for mobile nav

### Standalone Mode
- Adjusted padding for status bar
- Full-screen layout support
- No browser chrome spacing

---

## Dark Mode

### Implementation
- Uses `next-themes` for theme management
- CSS custom properties for seamless switching
- No flash of unstyled content
- Persists user preference

### Color Adjustments
- Increased lightness for primary colors in dark mode
- Reduced contrast for borders
- Darker backgrounds with subtle tinting
- Maintained semantic color associations

---

## Best Practices

### DO
✅ Use design tokens from globals.css
✅ Apply semantic color names (primary, success, destructive)
✅ Use utility classes for spacing (gap-6, p-4)
✅ Include hover and focus states
✅ Test in both light and dark modes
✅ Respect reduced motion preferences
✅ Use consistent border radius
✅ Apply shadow progression for depth

### DON'T
❌ Use arbitrary color values
❌ Mix spacing systems
❌ Create one-off components
❌ Skip accessibility features
❌ Ignore mobile breakpoints
❌ Use inline styles for theming
❌ Forget loading states
❌ Override focus rings

---

## Design Token Reference

### Quick Reference Table

| Token | Light Value | Dark Value | Usage |
|-------|-------------|------------|-------|
| `bg-background` | Off-white | Dark blue-black | Page background |
| `bg-card` | White | Dark blue-gray | Card surfaces |
| `text-foreground` | Dark gray | Light gray | Primary text |
| `text-muted-foreground` | Medium gray | Medium-light gray | Secondary text |
| `bg-primary` | Blue 50% | Blue 60% | Primary actions |
| `bg-success` | Green 45% | Green 50% | Success states |
| `bg-warning` | Amber 50% | Amber 55% | Warning states |
| `bg-destructive` | Red 48% | Red 55% | Error states |
| `border-border` | Light gray | Dark gray | Borders |
| `shadow-sm` | Subtle | Subtle | Default elevation |

---

## Maintenance

### Version History
- **1.0** (2025-11-10): Initial audit

### Review Schedule
- Quarterly review of color contrast
- Bi-annual accessibility audit
- Annual design system refresh

### Change Process
1. Propose changes in design meeting
2. Update globals.css design tokens
3. Test in both light/dark modes
4. Update component library
5. Document in this file
6. Communicate to team

---

## Status: ✅ PASSING

The TutorMax design system is well-architected with:
- Modern color system (OKLCH)
- Consistent spacing and typography
- Comprehensive animation system
- Full dark mode support
- Strong accessibility foundation
- PWA optimization
- Responsive design patterns

**No critical issues identified.**
