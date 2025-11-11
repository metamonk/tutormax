# TutorMax Video - Visual Storyboard & Screenshot Guide

**Visual Planning for Video Production**

---

## 📸 Screenshots Needed

### Opening Section
1. **TutorMax Dashboard Hero Shot**
   - Full dashboard with all sections visible
   - Light mode, clean data
   - Location: `http://localhost:3003/dashboard`
   - Resolution: 1920x1080
   - Purpose: Opening title card

2. **Problem Statement Infographic**
   - Create slide with 4 key stats:
     - 24% first session failure
     - 98.2% tutor-initiated reschedules
     - 16% no-show replacements
     - Cost impact ($$$)
   - Use red/warning colors
   - Tool: Figma or Keynote

---

## 🏗️ Architecture Diagrams

### 1. System Architecture Overview
**Create in:** Excalidraw or Mermaid
**Elements:**
```
[Synthetic Data Engine] (purple box)
         ↓
[Data Pipeline] (blue boxes)
  - Validation Worker
  - Enrichment Worker
  - Database Persister
         ↓
[Processing Engines] (green boxes)
  - Performance Evaluator
  - Churn Predictor
  - Intervention Engine
         ↓
[Dashboard/UI] (orange boxes)
  - Ops Dashboard
  - Tutor Portal
  - Admin Tools
```

**Color Coding:**
- Purple: Data sources
- Blue: Pipeline stages
- Green: Processing/ML
- Orange: User interfaces
- Red: Alerts/critical paths

### 2. Redis Streams Data Flow
**Create in:** Lucidchart or Draw.io
**Show:**
- Session completes → FastAPI endpoint
- Validation worker (tutormax:sessions:validation)
- Enrichment worker (tutormax:sessions:enrichment)
- Metrics worker (tutormax:sessions:metrics)
- Database writes at each stage
- Consumer groups with multiple workers
- Timeline: 0s → 31.8s total latency

### 3. Horizontal Scaling Diagram
**Show:**
- Redis Stream (center)
- Consumer group: metrics-workers
- 4 worker instances
- Load distribution (Msg 1,5,9 | 2,6,10 | 3,7 | 4,8)
- Auto-balancing arrows

### 4. Security Layers
**Create as:** Stacked boxes/shields
**5 Layers:**
1. Network Security (TLS 1.3, Rate limiting)
2. Authentication (JWT, RBAC, MFA)
3. Data Security (AES-256, Field encryption)
4. Application Security (Input sanitization, XSS/CSRF)
5. Audit & Monitoring (Logging, Compliance)

---

## 🎨 Design System Screenshots

### Component Showcase Page
**Location:** `http://localhost:3003/components-showcase`

**Shot 1: Color System (30 sec)**
- Full page scroll showing all color scales
- Highlight OKLCH annotation
- Show HSL fallback code

**Shot 2: Button Variants (15 sec)**
- All 6 button types in grid
- Show hover states
- Click to demonstrate transitions

**Shot 3: Form Components (30 sec)**
- Input fields with validation
- Error states
- Success states
- Disabled states
- Focus rings

**Shot 4: Dark Mode Toggle (15 sec)**
- Toggle switch
- Smooth transition
- Side-by-side light/dark comparison

**Shot 5: Component Library (45 sec)**
- Rapid scroll through all 22 components
- Pause on interesting ones:
  - Dialog (keyboard accessible)
  - Dropdown Menu
  - Data Table
  - Toast notifications

---

## 📊 Dashboard Screenshots

### Dashboard Overview
**Location:** `http://localhost:3003/dashboard`

**Shot 1: Full Page (10 sec)**
- Hero shot with all sections visible
- Connection indicator (green)
- Scroll from top to bottom slowly

**Shot 2: Critical Alerts (30 sec)**
- Zoom into alerts section
- Show 3 critical tutors
- Click one to open profile
- Show churn score breakdown

**Shot 3: Performance Tiers (60 sec)**
- Zoom into tier cards
- All 4 tiers visible (Platinum, Gold, Silver, Bronze)
- Hover effects on each
- Click Silver tier to filter
- Show filtered results
- Unfilter to reset

**Shot 4: Activity Heatmap (45 sec)**
- Zoom into contribution graph
- Show 365-day view
- Hover over individual squares
- Show tooltips with session counts
- Highlight high-activity periods

**Shot 5: Charts Section (2 min)**
- Pie chart: Tier distribution
  - Show percentages in tooltip
- Bar chart: Top 5 performers
  - Show tutor names and ratings
- Bar chart: Bottom performers (needs attention)
- Line chart: Engagement trend
  - Show 30-day window
  - Highlight declining trend

**Shot 6: Interventions (60 sec)**
- Scroll to interventions section
- Show 12 pending tasks
- Color-coded SLA timers (green, yellow, red)
- Click one intervention
- Show assignment dialog
- Assign to manager
- Show confirmation

---

## 👤 Tutor Portal Screenshots

**Location:** `http://localhost:3003/tutor-portal`

**Shot 1: Overview Tab (45 sec)**
- Performance tier badge (Gold)
- Key metrics cards:
  - Average rating: 4.5/5.0
  - Sessions completed: 47
  - Engagement score: 85%
  - On-time rate: 92%
- Time window selector (7d, 30d, 90d)

**Shot 2: Badges Tab (30 sec)**
- Achievement badges grid
- Earned badges (with dates)
- Locked badges (grayed out)
- Progress toward next badge

**Shot 3: Training Tab (30 sec)**
- Recommended courses
- Completion status
- "Start Course" button
- Time estimates

**Shot 4: Ratings Tab (45 sec)**
- Recent student feedback
- Anonymized comments
- Star ratings by category:
  - Subject knowledge: 5/5
  - Communication: 4/5
  - Patience: 5/5
  - Helpfulness: 4/5

**Shot 5: Peer Stats Tab (30 sec)**
- Percentile rank: 75th
- Anonymous comparison chart
- No individual tutor names
- Privacy-preserving design

---

## 🎯 Interventions Screenshots

**Location:** `http://localhost:3003/interventions`

**Shot 1: Stats Overview (20 sec)**
- 4 stat cards:
  - Pending: 12
  - In Progress: 5
  - Completed: 47
  - Cancelled: 2
- Color-coded borders

**Shot 2: Filter Bar (30 sec)**
- Filter by risk level (dropdown)
  - Critical, High, Medium, Low
- Filter by type (dropdown)
  - Coaching, PIP, Mentoring, Interview
- Filter by assigned manager (dropdown)
- Search by tutor name (input)

**Shot 3: Intervention Card (60 sec)**
- Tutor info (name, ID, tenure)
- Churn score: 68 (High Risk) - orange badge
- Risk factors (list):
  - Engagement decline: -30%
  - High reschedule rate: 4 in 7 days
  - No-show in last 14 days
- Recommended action: "Manager coaching session"
- SLA timer: 36 hours remaining (yellow)
- Actions: Assign, View Profile, Dismiss

**Shot 4: Assignment Dialog (30 sec)**
- Assign to: [Manager dropdown]
- Due date: [Date picker]
- Priority: [High/Medium/Low]
- Notes: [Textarea]
- "Assign" button
- Confirmation toast

---

## 👨‍🎓 Student Feedback Screenshots

**Location:** `http://localhost:3003/feedback/[token]`

**Shot 1: Loading State (5 sec)**
- Animated spinner
- "Validating feedback token..."
- Clean, centered layout

**Shot 2: Feedback Form (60 sec)**
- Session info (date, subject, tutor)
- Overall rating: 5 stars (interactive)
- Category ratings:
  - Subject knowledge: [5 stars]
  - Communication: [4 stars]
  - Patience: [5 stars]
  - Helpfulness: [4 stars]
- Text feedback (optional):
  - Placeholder: "Tell us about your experience..."
  - 500 character limit
  - Character counter

**Shot 3: First Session Special (30 sec)**
- "Would you want to work with this tutor again?"
  - Radio buttons: Yes / Maybe / Probably not / No
- If negative selected:
  - Checkboxes: "What could be improved?"
    - [ ] Tutor was late
    - [ ] Tutor was unprepared
    - [ ] Explanations were unclear
    - [ ] Not patient enough
    - [ ] Technical issues

**Shot 4: Success State (10 sec)**
- Green checkmark animation
- "Thank you for your feedback!"
- "Your tutor will see your ratings but not your name"
- Privacy message
- "Close this window" button

**Shot 5: Error States (15 sec each)**
- Expired token:
  - Red X icon
  - "This feedback link has expired"
  - "Please contact support"
- Already submitted:
  - Blue info icon
  - "You've already submitted feedback for this session"
  - "Thank you!"

---

## 🛡️ Admin Screenshots

**Location:** `http://localhost:3003/users` (and other admin pages)

**Shot 1: Users Management (60 sec)**
- Users table:
  - Columns: Name, Email, Role, Status, Last Active
  - Sort by column
  - Filter by role
  - Search by name/email
- Actions: Edit, Delete, View Audit Log
- "Add User" button

**Shot 2: Audit Logs (45 sec)**
- Audit logs table:
  - Columns: Timestamp, User, Action, Resource, IP Address
  - Real-time updates
  - Export to CSV button
  - Date range filter
- Example actions:
  - "user@example.com viewed tutor profile #123"
  - "admin@example.com assigned intervention #456"
  - "manager@example.com updated tutor #789"

**Shot 3: Compliance Reports (30 sec)**
- FERPA compliance status
- COPPA compliance status
- GDPR compliance status
- Last audit date
- "Generate Report" buttons
- Download PDF reports

**Shot 4: Data Retention (30 sec)**
- Data retention policies
- Scheduled deletions
- Retention periods by data type:
  - Sessions: 7 years
  - Feedback: 7 years
  - Audit logs: 3 years
  - PII: Until deletion requested
- "Preview Deletions" button

---

## 💻 Code Screenshots

### Backend Code Examples

**Shot 1: Redis Streams Publisher (20 sec)**
```python
# src/pipeline/enrichment/enrichment_worker.py
await self.publisher.publish(
    "tutormax:sessions:enrichment",
    session_data,
    metadata={"source": "enrichment"}
)
```

**Shot 2: Performance Calculator (30 sec)**
```python
# src/evaluation/performance_calculator.py
async def calculate_metrics(
    self,
    tutor_id: str,
    window: MetricWindow
) -> TutorMetrics:
    sessions = await self.get_sessions(tutor_id, window)

    return TutorMetrics(
        avg_rating=mean([s.rating for s in sessions]),
        first_session_success_rate=...,
        reschedule_rate=...,
        engagement_score=...,
    )
```

**Shot 3: Churn Prediction (30 sec)**
```python
# src/evaluation/prediction_service.py
predictions = model.predict_proba(features)

churn_score = weighted_average([
    predictions["1d"] * 0.15,
    predictions["7d"] * 0.35,  # Most important
    predictions["30d"] * 0.35,
    predictions["90d"] * 0.15,
])

return ChurnPrediction(
    score=churn_score * 100,
    risk_level=get_risk_level(churn_score),
    contributing_factors=get_shap_values(features)
)
```

**Shot 4: Intervention Rules (20 sec)**
```python
# src/evaluation/intervention_framework.py
if churn_score >= 76:  # Critical
    create_intervention(
        type="retention_interview",
        priority="urgent",
        sla_hours=24
    )
    notify_manager(urgency="critical")
```

### Frontend Code Examples

**Shot 5: WebSocket Hook (20 sec)**
```tsx
// hooks/useWebSocket.ts
const { tutorMetrics, alerts, connected } = useWebSocket();

// Auto-reconnects on disconnect
// Real-time updates without polling
```

**Shot 6: Optimistic UI (30 sec)**
```tsx
// components/interventions/InterventionCard.tsx
const updateStatus = async (newStatus) => {
  // 1. Update UI immediately
  setStatus(newStatus);

  try {
    // 2. Send to server
    await api.updateIntervention(id, newStatus);
  } catch {
    // 3. Rollback on failure
    setStatus(oldStatus);
    toast.error("Update failed");
  }
};
```

**Shot 7: Lazy Loading (20 sec)**
```tsx
// app/dashboard/page.tsx
const PerformanceAnalytics = lazy(() =>
  import('@/components/dashboard/PerformanceAnalytics')
);

<Suspense fallback={<LoadingSkeleton />}>
  <PerformanceAnalytics />
</Suspense>
```

---

## 📈 Performance Screenshots

### Lighthouse Report
**Tool:** Chrome DevTools > Lighthouse
**Settings:** Mobile, Clear storage
**Categories:** Performance, Accessibility, Best Practices, SEO, PWA

**Shot 1: Overall Scores (15 sec)**
- Performance: 95/100
- Accessibility: 100/100
- Best Practices: 100/100
- SEO: 100/100
- PWA: 95/100

**Shot 2: Core Web Vitals (20 sec)**
- First Contentful Paint: 1.2s (green)
- Largest Contentful Paint: 2.0s (green)
- Cumulative Layout Shift: 0.05 (green)
- Total Blocking Time: 50ms (green)

**Shot 3: Accessibility Details (15 sec)**
- All checks passed (green checkmarks)
- Color contrast: WCAG AA compliant
- ARIA: Properly labeled
- Keyboard navigation: Fully supported

### Network Tab
**Tool:** Chrome DevTools > Network

**Shot 4: Initial Page Load (30 sec)**
- Total requests: 25
- Total size: 450 KB
- Load time: 1.8s on 3G
- Show waterfall chart
- Highlight:
  - HTML: 15 KB
  - CSS: 45 KB
  - JS: 280 KB
  - Fonts: 80 KB
  - Images: 30 KB

**Shot 5: WebSocket Connection (20 sec)**
- Show WS connection in Network tab
- Messages tab showing real-time data
- Latency: <50ms
- Message frequency: 1-2 per second

### Application Tab
**Tool:** Chrome DevTools > Application

**Shot 6: Service Worker (20 sec)**
- Service worker status: Active
- Cached resources: 35 files
- Offline capability: Enabled
- Update check: Every 24 hours

**Shot 7: Storage (15 sec)**
- IndexedDB: 2.1 MB
- LocalStorage: 45 KB
- Session Storage: 12 KB
- Cache Storage: 8.5 MB

---

## 🎬 Screen Recording Tips

### Recording Settings
- **Resolution:** 1920x1080 (Full HD)
- **Frame Rate:** 60 FPS
- **Codec:** H.264
- **Audio:** 48 kHz, 16-bit
- **Tool:** OBS Studio or QuickTime

### Browser Setup
- **Browser:** Chrome (latest)
- **Zoom:** 100% (no zoom)
- **Extensions:** Disable (for clean UI)
- **Profile:** Clean profile (no bookmarks)
- **Window Size:** 1920x1080 (full screen)

### Cursor Settings
- **Cursor Highlight:** Enable (yellow circle)
- **Click Animation:** Enable (ripple effect)
- **Tool:** Mousepose or Keycastr

### Multiple Takes
Record each section separately:
1. **A-Roll:** Main content with voiceover
2. **B-Roll:** Code scrolls, terminal output, animations
3. **Screen Captures:** Static screenshots for emphasis

---

## 🎨 Graphic Elements to Create

### Title Cards
1. **Opening Title**
   - "TutorMax: Tutor Performance Evaluation System"
   - Subtitle: "Predicting Churn 30-90 Days in Advance"
   - Background: Gradient (primary blue)

2. **Section Dividers**
   - "Part 1: Introduction & Problem Statement"
   - "Part 2: System Architecture"
   - "Part 3: Frontend Implementation"
   - etc.
   - Background: Subtle gradient
   - Icon: Relevant emoji or icon

3. **Key Stats**
   - Large number + label
   - Example: "85%" + "Prediction Accuracy"
   - Color: Primary blue or success green
   - Animation: Count-up effect

### Callout Boxes
- **Interesting Pattern:** Purple box
- **Key Insight:** Blue box
- **Warning/Caution:** Amber box
- **Success/Achievement:** Green box

### Annotations
- **Arrows:** Point to specific UI elements
- **Highlights:** Yellow boxes around important features
- **Circles:** Draw attention to buttons or icons
- **Fade In/Out:** Smooth transitions

---

## 📊 Chart/Graph Screenshots

### Dashboard Charts
**Pie Chart: Performance Tier Distribution**
- Platinum: 10%
- Gold: 30%
- Silver: 35%
- Bronze: 25%
- Colors: Purple, Gold, Gray, Orange
- Show percentages in legend

**Bar Chart: Top 5 Performers**
- Horizontal bars
- Tutor names (anonymized if needed)
- Ratings: 4.8, 4.7, 4.6, 4.5, 4.5
- Color: Success green gradient

**Line Chart: Engagement Trend**
- X-axis: 30 days
- Y-axis: Engagement score (0-100%)
- Line: Declining from 85% to 60%
- Color: Warning amber (declining trend)
- Fill: Gradient below line

### Analytics Page
**Churn Heatmap**
- Create in Figma or use Chart.js
- X-axis: Day of week
- Y-axis: Hour of day
- Color: Red (high churn) to Green (low churn)
- Show: Mondays 9am have highest churn risk

**Cohort Analysis**
- Table format
- Rows: Tenure cohorts (0-30d, 31-60d, 61-90d, 91+)
- Columns: Churn rate, Avg rating, Session count
- Color: Red for concerning metrics

---

## 🎥 Video Timeline

**Total Duration:** 30 minutes

| Time | Section | Visuals |
|------|---------|---------|
| 0:00-0:30 | Opening Hook | Title card → Dashboard hero shot |
| 0:30-3:00 | Problem Statement | Stats infographic → PRD quotes |
| 3:00-7:00 | Architecture | System diagram → Data flow |
| 7:00-13:00 | Frontend | Component showcase → Dashboard demo |
| 13:00-20:00 | Backend | Code snippets → Worker diagrams |
| 20:00-24:00 | Compliance | Security layers → Audit logs |
| 24:00-27:00 | Performance | Lighthouse report → Network tab |
| 27:00-29:00 | Learnings | Bullet points → Code examples |
| 29:00-30:00 | Closing | Summary card → Call to action |

---

## 📦 Asset Checklist

### Screenshots (38 total)
- [ ] Dashboard hero shot
- [ ] Problem statement infographic
- [ ] Component showcase (5 shots)
- [ ] Dashboard detailed (6 shots)
- [ ] Tutor portal (5 shots)
- [ ] Interventions (4 shots)
- [ ] Student feedback (5 shots)
- [ ] Admin pages (4 shots)
- [ ] Code examples (7 shots)
- [ ] Performance metrics (7 shots)

### Diagrams (4 total)
- [ ] System architecture
- [ ] Redis Streams data flow
- [ ] Horizontal scaling
- [ ] Security layers

### Graphics (10 total)
- [ ] Opening title card
- [ ] 9 section divider cards
- [ ] Closing summary card

### Recordings (9 total)
- [ ] Dashboard live demo
- [ ] Tutor portal walkthrough
- [ ] Intervention assignment flow
- [ ] Student feedback submission
- [ ] Dark mode toggle
- [ ] Real-time WebSocket updates
- [ ] Lighthouse audit run
- [ ] Terminal worker output
- [ ] Mobile responsive demo

---

## 🎬 Post-Production Checklist

### Video Editing
- [ ] Cut silences and filler words
- [ ] Add transitions between sections
- [ ] Insert B-roll footage
- [ ] Add background music (subtle, non-distracting)
- [ ] Normalize audio levels
- [ ] Color correction (if needed)

### Graphics/Annotations
- [ ] Add callout boxes for key points
- [ ] Highlight important UI elements
- [ ] Add arrows pointing to features
- [ ] Insert key stat overlays
- [ ] Add section divider cards

### Captions/Subtitles
- [ ] Generate auto-captions
- [ ] Manually review and fix errors
- [ ] Add punctuation and formatting
- [ ] Highlight technical terms
- [ ] Export SRT file

### Final Review
- [ ] Watch full video (no interruptions)
- [ ] Check audio sync
- [ ] Verify all links work (if on screen)
- [ ] Confirm branding consistency
- [ ] Test on multiple devices
- [ ] Get feedback from colleague

---

## 🚀 Publishing Checklist

### Video File
- [ ] Resolution: 1920x1080
- [ ] Frame rate: 60 FPS
- [ ] Codec: H.264
- [ ] Bitrate: 15-20 Mbps
- [ ] File size: < 2 GB (for easy sharing)

### Metadata
- [ ] Title: "TutorMax: AI-Powered Tutor Performance System"
- [ ] Description: Include timestamps, key links
- [ ] Tags: tutoring, edtech, machine learning, churn prediction, FastAPI, Next.js
- [ ] Thumbnail: Eye-catching dashboard shot
- [ ] Chapters: Add timestamps for each section

### Distribution
- [ ] Upload to YouTube (if public)
- [ ] Share on LinkedIn
- [ ] Post in Slack/Teams
- [ ] Send direct links to stakeholders
- [ ] Add to project wiki/docs

---

**Created:** 2025-11-10
**For:** TutorMax Video Production
**Total Assets:** 61 screenshots + 4 diagrams + 9 recordings
