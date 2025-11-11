# Dashboard Component Showcase

## Visual Preview of Components

### 1. Performance Tiers Component

```
┌─────────────────────────────────────────────────────────────────────┐
│  👥 Performance Tiers                                                │
│  Distribution of tutors across performance levels                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ ● Platinum│  │ ● Gold   │  │ ● Silver │  │ ● Bronze │           │
│  │ Exceptional│  │ Strong   │  │ Developing│  │ Needs   │           │
│  │ (≥90%)    │  │ (80-89%) │  │ (70-79%) │  │ (<70%)  │           │
│  │           │  │           │  │           │  │           │           │
│  │    12     │  │    25     │  │    18     │  │     8     │           │
│  │  tutors   │  │  tutors   │  │  tutors   │  │  tutors   │           │
│  │  ████ 19% │  │  ████ 40% │  │  ███ 29%  │  │  ██ 13%   │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
│                                                                      │
│  [Selected: Gold tier - Showing 25 tutors]                          │
└─────────────────────────────────────────────────────────────────────┘
```

**Features:**
- 4 interactive tier cards with gradient backgrounds
- Pill badges with status indicators
- Progress bars showing percentage distribution
- Click to filter (ring highlight on selection)
- Responsive grid layout

---

### 2. Activity Heatmap (Contribution Graph)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Activity Heatmap                                                    │
│  Daily activity overview for the past year                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Jan    Feb    Mar    Apr    May    Jun    Jul    Aug    Sep  ...   │
│  ▪▫▪▪▫▫▪▪▫▪▫▪▪▫▫▪▪▫▪▫▪▪▫▫▪▪▫▪▫▪▪▫▫▪▪▫▪▫▪▪▫▫▪▪▫▪▫▪▪▫▫▪▪▫▪▫  Sun      │
│  ▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫  Mon      │
│  ▪▫▪▪▫▫▪▪▫▪▫▪▪▫▫▪▪▫▪▫▪▪▫▫▪▪▫▪▫▪▪▫▫▪▪▫▪▫▪▪▫▫▪▪▫▪▫▪▪▫▫▪▪▫  Tue      │
│  ▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫  Wed      │
│  ▪▫▪▪▫▫▪▪▫▪▫▪▪▫▫▪▪▫▪▫▪▪▫▫▪▪▫▪▫▪▪▫▫▪▪▫▪▫▪▪▫▫▪▪▫▪▫▪▪▫▫▪▪▫  Thu      │
│  ▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫▫▪▫▪▪▫  Fri      │
│  ▪▫▪▪▫▫▪▪▫▪▫▪▪▫▫▪▪▫▪▫▪▪▫▫▪▪▫▪▫▪▪▫▫▪▪▫▪▫▪▪▫▫▪▪▫▪▫▪▪▫▫▪▪▫  Sat      │
│                                                                      │
│  2,847 activities in 2025          Less ▫▪▪▪▪ More                  │
└─────────────────────────────────────────────────────────────────────┘
```

**Features:**
- GitHub-style contribution graph
- 365 days of activity data
- 5 intensity levels (0-4)
- Month labels at top
- Hover tooltips (planned)
- Legend with total count

---

### 3. Enhanced Performance Analytics

#### Key Metrics (5-card layout)

```
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Total Tutors │ │ Avg Rating   │ │ Engagement   │ │ Sessions     │ │ Alerts       │
│              │ │              │ │   Score      │ │ (7 days)     │ │              │
│      63      │ │     4.57     │ │    87.3      │ │     284      │ │   3 / 7      │
│              │ │ ████████░ 5.0│ │              │ │              │ │              │
│ Active: 58   │ │              │ │ Avg all      │ │ 1,247 (30d)  │ │ 3 crit, 7 wrn│
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

#### Charts Layout

```
┌─────────────────────────────┐ ┌─────────────────────────────┐
│ Tier Distribution (Pie)     │ │ Top 5 Performers (Bar)      │
│                             │ │                             │
│       ╱▔▔╲                 │ │ Sarah M.  ████████ 4.9      │
│     ▕█ █ █                 │ │ John D.   ███████  4.8      │
│     ▕ █ █▏                 │ │ Emily R.  ███████  4.8      │
│       ╲__╱                 │ │ Mike P.   ██████   4.7      │
│                             │ │ Lisa K.   ██████   4.7      │
└─────────────────────────────┘ └─────────────────────────────┘

┌─────────────────────────────┐ ┌─────────────────────────────┐
│ Engagement Trend (Line)     │ │ Completion Rate (Circle)    │
│                             │ │                             │
│   90 ┐                      │ │         ╭───╮              │
│      │    ╱‾‾╲             │ │        ╱ 95.2% ╲           │
│   85 ├───╱    ╲─          │ │       │   ███   │          │
│      │           ╲        │ │       │  █████  │          │
│   80 └─────────────       │ │        ╲ █████ ╱           │
│      7d  5d  3d  1d Today  │ │         ╰───╯              │
│                             │ │                             │
│                             │ │  1,215 of 1,247 completed  │
└─────────────────────────────┘ └─────────────────────────────┘
```

---

## Component Props

### PerformanceTiers

```typescript
interface PerformanceTiersProps {
  analytics: PerformanceAnalytics | null;
  tutorMetrics: TutorMetrics[];
  onTierClick?: (tier: string | null) => void;
}
```

**Usage:**
```tsx
<PerformanceTiers
  analytics={state.analytics}
  tutorMetrics={state.tutorMetrics}
  onTierClick={(tier) => {
    console.log('Filter by tier:', tier);
  }}
/>
```

### PerformanceAnalytics (Enhanced)

```typescript
interface PerformanceAnalyticsProps {
  analytics: PerformanceAnalytics | null;
  tutorMetrics: TutorMetrics[];
}
```

**Usage:**
```tsx
<PerformanceAnalytics
  analytics={state.analytics}
  tutorMetrics={state.tutorMetrics}
/>
```

### ContributionGraph (Activity Heatmap)

```typescript
interface ContributionGraphProps {
  data: Activity[];
  blockSize?: number;
  blockMargin?: number;
  blockRadius?: number;
  maxLevel?: number;
  weekStart?: WeekDay;
}

interface Activity {
  date: string;      // ISO format: "2025-01-15"
  count: number;     // Activity count
  level: number;     // Intensity level (0-4)
}
```

**Usage:**
```tsx
<ContributionGraph data={activityData}>
  <ContributionGraphCalendar>
    {({ activity, dayIndex, weekIndex }) => (
      <ContributionGraphBlock
        activity={activity}
        dayIndex={dayIndex}
        weekIndex={weekIndex}
        className="hover:opacity-80"
      />
    )}
  </ContributionGraphCalendar>
  <ContributionGraphFooter>
    <ContributionGraphTotalCount />
    <ContributionGraphLegend />
  </ContributionGraphFooter>
</ContributionGraph>
```

---

## Color Schemes

### Performance Tiers

| Tier     | Gradient                  | Text Color | Indicator |
|----------|---------------------------|------------|-----------|
| Platinum | Purple (500→700)          | Purple-900 | Success   |
| Gold     | Yellow (400→600)          | Yellow-900 | Success   |
| Silver   | Gray (400→600)            | Gray-900   | Warning   |
| Bronze   | Orange (600→800)          | Orange-900 | Error     |

### Activity Heatmap Levels

| Level | Color                  | Opacity    |
|-------|------------------------|------------|
| 0     | Muted                  | Base       |
| 1     | Muted-foreground       | 20%        |
| 2     | Muted-foreground       | 40%        |
| 3     | Muted-foreground       | 60%        |
| 4     | Muted-foreground       | 80%        |

### Chart Colors (Chart.js)

- **Exemplary/Top Performers**: Green (34, 197, 94)
- **Strong**: Blue (59, 130, 246)
- **Developing**: Yellow (251, 191, 36)
- **Needs Support**: Red (239, 68, 68)

---

## Responsive Breakpoints

```css
/* Mobile (default) */
grid-cols-1

/* Tablet (md: 768px) */
md:grid-cols-2

/* Desktop (lg: 1024px) */
lg:grid-cols-4  /* Performance Tiers */
lg:grid-cols-5  /* Metric Cards */
```

---

## Dark Mode Support

All components automatically adapt to dark mode using Tailwind's `dark:` prefix:

```tsx
// Example from PerformanceTiers
className="text-purple-900 dark:text-purple-100"
className="bg-yellow-50 dark:bg-yellow-950"
```

---

## Accessibility Features

1. **Semantic HTML**: Proper use of `<section>`, `<header>`, `<article>`
2. **Keyboard Navigation**: All interactive elements are keyboard accessible
3. **ARIA Labels**: Screen reader support on charts and graphs
4. **Color Contrast**: WCAG AA compliant contrast ratios
5. **Focus Indicators**: Visible focus states on interactive elements

---

## Performance Optimizations

1. **useMemo**: Chart data calculations memoized to prevent recalculation
2. **Lazy Loading**: Charts loaded only when data is available
3. **Conditional Rendering**: Empty states shown while loading
4. **Optimized Re-renders**: React.memo on chart components
5. **SVG Graphics**: Lightweight vector graphics for indicators

---

## Browser Compatibility

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

---

## Code Quality

- ✅ TypeScript strict mode
- ✅ ESLint passing
- ✅ Zero console warnings
- ✅ Production build successful
- ✅ Tree-shaking optimized

---

## File Sizes (Production Build)

```
components/dashboard/PerformanceTiers.tsx    ~8.2 KB
components/dashboard/PerformanceAnalytics.tsx ~10.5 KB (enhanced)
components/kibo-ui/pill/index.tsx           ~4.8 KB
components/kibo-ui/contribution-graph/      ~15.2 KB
```

---

**Visual Design Philosophy:**
- Clean, modern interface with subtle gradients
- Data-driven visualizations with clear hierarchy
- Interactive elements with smooth transitions
- Consistent spacing and typography
- Professional color palette aligned with brand
