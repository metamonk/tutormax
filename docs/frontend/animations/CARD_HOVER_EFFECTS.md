# Card and Component Hover Effects - Implementation Guide

## Overview
This document details the hover effects and elevation animations implemented for cards and card-like components in Subtask 14.3.

## Card Component Enhancement

### New Props

The `Card` component now supports two hover-related props:

```typescript
<Card
  hoverable={boolean}    // Subtle hover feedback (non-clickable)
  interactive={boolean}  // Strong hover for clickable cards
/>
```

### Hover Variants

#### 1. **Default Card** (no props)
```tsx
<Card>
  {/* Content */}
</Card>
```
- No hover effect
- Static appearance
- Use for: Content that doesn't need hover feedback

#### 2. **Hoverable Card** (`hoverable={true}`)
```tsx
<Card hoverable>
  {/* Content */}
</Card>
```
- Subtle shadow increase: `shadow-sm → shadow-md`
- Border fade: `border → border-border/80`
- Duration: 250ms
- Use for: Cards that provide visual feedback but aren't clickable

#### 3. **Interactive Card** (`interactive={true}`)
```tsx
<Card interactive onClick={handleClick}>
  {/* Content */}
</Card>
```
- Strong shadow: `shadow-sm → shadow-lg`
- Lifts up: `-translate-y-1`
- Border glow: `border-primary/20`
- Active state: returns to 0 position
- Cursor: pointer
- Duration: 250ms
- Use for: Clickable cards, navigation cards, selection cards

## Animation Utility Classes

### TypeScript Utilities (`lib/animations.ts`)

#### Card Animation Patterns

```typescript
import { animationClasses } from '@/lib/animations'

// Subtle hover
animationClasses.card.base      // 'transition-all duration-250 transform-gpu'
animationClasses.card.subtle    // 'hover:shadow-md hover:border-border/80'

// Standard hover with lift
animationClasses.card.hover     // 'hover:shadow-lg hover:-translate-y-1'

// Interactive clickable
animationClasses.card.interactive // Full interactive animation
```

#### Metric Card Patterns

```typescript
// For smaller stat/metric cards
animationClasses.metricCard.base        // 'transition-all duration-200 transform-gpu'
animationClasses.metricCard.hover       // Includes bg-accent/5 tint
animationClasses.metricCard.interactive // Subtle lift (0.5px)
```

#### Pre-built Component Classes

```typescript
import { componentAnimations } from '@/lib/animations'

// Ready-to-use complete animation classes
componentAnimations.card                  // Subtle hover card
componentAnimations.cardInteractive       // Interactive card
componentAnimations.metricCard            // Metric card hover
componentAnimations.metricCardInteractive // Interactive metric card
```

### CSS Utility Classes (`app/globals.css`)

#### Card Hover Classes

```css
/* Subtle hover - minimal feedback */
.card-hover-subtle {
  @apply transition-all duration-250 hover:shadow-md hover:border-border/80;
}

/* Lift hover - elevates card */
.card-hover-lift {
  @apply transition-all duration-250 hover:shadow-lg hover:-translate-y-1 hover:border-border/60;
}

/* Interactive - full clickable experience */
.card-hover-interactive {
  @apply transition-all duration-250 cursor-pointer hover:shadow-xl hover:-translate-y-2 hover:border-primary/20 active:translate-y-0 active:shadow-md;
}
```

#### Metric Card Hover Classes

```css
/* Standard metric card hover */
.metric-card-hover {
  @apply transition-all duration-200 hover:shadow-md hover:border-border/80 hover:bg-accent/5;
}

/* Interactive metric card */
.metric-card-interactive {
  @apply transition-all duration-200 cursor-pointer hover:shadow-lg hover:-translate-y-0.5 hover:border-primary/30 active:translate-y-0;
}
```

## Usage Examples

### 1. Dashboard Metric Cards

```tsx
// Using Card component
<Card hoverable className="p-6">
  <div className="space-y-2">
    <p className="text-sm text-muted-foreground">Total Tutors</p>
    <p className="text-3xl font-bold">{count}</p>
  </div>
</Card>

// Using CSS utility
<div className="card-hover-subtle rounded-xl border bg-card p-6 shadow-sm">
  <div className="space-y-2">
    <p className="text-sm text-muted-foreground">Total Tutors</p>
    <p className="text-3xl font-bold">{count}</p>
  </div>
</div>

// Using TypeScript utility
<div className={cn(
  "rounded-xl border bg-card p-6 shadow-sm",
  componentAnimations.metricCard
)}>
  {/* Content */}
</div>
```

### 2. Clickable Navigation Cards

```tsx
// Using Card component
<Card interactive onClick={() => router.push('/path')}>
  <CardHeader>
    <CardTitle>Dashboard</CardTitle>
  </CardHeader>
  <CardContent>
    View analytics and reports
  </CardContent>
</Card>

// Using CSS utility
<div
  className="card-hover-interactive rounded-xl border bg-card p-6 shadow-sm"
  onClick={() => router.push('/path')}
>
  {/* Content */}
</div>
```

### 3. Large Content Cards

```tsx
// Subtle hover for better UX but not clickable
<Card hoverable>
  <CardHeader>
    <CardTitle>Performance Analytics</CardTitle>
    <CardDescription>Last 30 days overview</CardDescription>
  </CardHeader>
  <CardContent>
    {/* Charts and data */}
  </CardContent>
</Card>
```

### 4. List Item Cards (e.g., Tutor Cards)

```tsx
// Interactive card in a list
<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
  {tutors.map(tutor => (
    <Card
      key={tutor.id}
      interactive
      onClick={() => router.push(`/tutor/${tutor.id}`)}
    >
      <CardContent className="p-6">
        <div className="flex items-center gap-4">
          <Avatar>
            <AvatarImage src={tutor.avatar} />
            <AvatarFallback>{tutor.initials}</AvatarFallback>
          </Avatar>
          <div>
            <h3 className="font-semibold">{tutor.name}</h3>
            <p className="text-sm text-muted-foreground">{tutor.subject}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  ))}
</div>
```

## Design Principles

### Hover Effect Guidelines

1. **Subtle for Information** - Cards displaying static information get subtle hover (shadow only)
2. **Lift for Navigation** - Cards that navigate somewhere get lift animation
3. **Strong for Actions** - Cards triggering actions get pronounced effects
4. **Fast Transitions** - Metric cards use 200ms, standard cards use 250ms
5. **Consistent Shadows** - Use the shadow scale: `sm → md → lg → xl`

### Shadow Elevation Scale

```
No hover:    shadow-sm   (default card state)
Subtle:      shadow-md   (hoverable cards, metrics)
Standard:    shadow-lg   (interactive cards)
Prominent:   shadow-xl   (strongly interactive cards)
```

### Translation Distance

```
None:        0px         (static cards)
Subtle:      0.5px       (metric cards)
Standard:    4px (-translate-y-1)
Prominent:   8px (-translate-y-2)
```

### Border Color Changes

```
Static:      border
Hover:       border-border/80 (subtle fade)
Interactive: border-primary/20 (primary tint)
Active:      border-primary/30 (stronger tint)
```

## Performance Considerations

### GPU Acceleration

All card animations use `transform-gpu` for hardware acceleration:
- Transforms (translate, scale) run on GPU
- Smooth 60fps animations
- No layout thrashing

### Transition Properties

Limited to performant properties:
- `transform` - GPU accelerated
- `box-shadow` - GPU accelerated
- `border-color` - composited
- `background-color` - composited

Avoided properties:
- ❌ `height/width` - causes reflow
- ❌ `padding/margin` - causes reflow
- ❌ `font-size` - causes repaint

## Accessibility

### Keyboard Navigation

All interactive cards must be keyboard accessible:

```tsx
<Card
  interactive
  onClick={handleClick}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleClick()
    }
  }}
  tabIndex={0}
  role="button"
  aria-label="View tutor profile"
>
  {/* Content */}
</Card>
```

### Focus States

Interactive cards inherit focus-visible ring from base styles:
- 2px ring with primary color
- 2px offset for visibility
- Respects prefers-reduced-motion

### Reduced Motion Support

```typescript
// Animation utilities check prefers-reduced-motion
if (prefersReducedMotion()) {
  // Transitions disabled or duration set to 0ms
}
```

## Dark Mode Support

All hover effects work in both light and dark mode:
- Shadow colors adjust automatically
- Border colors use semantic tokens
- Background tints use theme-aware colors

```css
/* Automatically adjusts */
hover:border-border/80        /* Works in light and dark */
hover:bg-accent/5            /* Uses theme accent color */
hover:border-primary/20      /* Uses theme primary color */
```

## Testing Checklist

- [x] Hover effects work in light mode
- [x] Hover effects work in dark mode
- [x] Interactive cards show pointer cursor
- [x] Active states provide feedback on click
- [x] Keyboard navigation works (Tab, Enter, Space)
- [x] Focus indicators visible
- [x] Animations smooth at 60fps
- [x] No layout shift during hover
- [x] Touch devices show active state
- [x] Reduced motion respected

## Migration Guide

### Before (Inline Styles)

```tsx
// Old approach - inconsistent
<div className="rounded-xl border bg-card p-6 shadow-sm transition-shadow hover:shadow-md">
  {/* Content */}
</div>
```

### After (Using New System)

```tsx
// Recommended: Use Card component
<Card hoverable className="p-6">
  {/* Content */}
</Card>

// Alternative: Use CSS utility
<div className="card-hover-subtle rounded-xl border bg-card p-6 shadow-sm">
  {/* Content */}
</div>

// Advanced: Use TypeScript utility
<div className={cn(
  "rounded-xl border bg-card p-6 shadow-sm",
  componentAnimations.card
)}>
  {/* Content */}
</div>
```

## Related Tasks

- **14.1:** ✅ Set up animation library and utilities
- **14.2:** ✅ Implement button and interactive element transitions
- **14.3:** ✅ Add card and component hover effects (this task)
- **14.4:** Pending - Create loading and skeleton animations
- **14.5:** Pending - Implement page and route transition animations
- **14.6:** Pending - Add accessibility and performance optimizations

---

**Implementation Date:** 2025-11-10
**Developer:** Claude Code
**Review Status:** Ready for QA
