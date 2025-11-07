# Product Requirements Document: Tutor Performance Evaluation & Retention System

**Version:** 1.0
**Date:** 2025-11-07
**Status:** Draft
**Owner:** Product & Engineering

---

## Executive Summary

This PRD defines an automated tutor performance evaluation system designed to process 3,000 daily tutoring sessions, predict tutor churn, identify coaching opportunities, and recommend data-driven interventions. The system will provide actionable insights within 1 hour of session completion to improve tutor retention and first-session quality.

**Key Innovation:** As a greenfield project with no existing data sources, this system includes a synthetic data generation engine to continuously simulate realistic tutor behavior, session data, and student feedback patterns.

---

## Problem Statement

### Current Challenges
- **24% of churned tutors** fail at the first session experience
- **98.2% of reschedulings** are tutor-initiated, indicating potential engagement or scheduling issues
- **16% of tutor replacements** are due to no-shows
- No systematic way to identify at-risk tutors before they churn
- Lack of data-driven coaching and intervention strategies
- No visibility into tutor performance trends or early warning signals

### Business Impact
- High tutor churn increases recruitment and training costs
- Poor first sessions damage student retention and platform reputation
- Reactive (vs. proactive) tutor management reduces operational efficiency
- Lost revenue from tutor attrition and student dissatisfaction

---

## Goals & Success Metrics

### Primary Goals
1. **Predict tutor churn** with actionable lead time across multiple time windows (1-day, 7-day, 30-day, 90-day)
2. **Reduce first-session failure rate** from 24% to <10% within 6 months
3. **Decrease tutor-initiated rescheduling** by 25% within 3 months
4. **Lower no-show-related replacements** from 16% to <8% within 6 months
5. **Process 3,000+ sessions daily** with <1 hour latency for insights

### Success Metrics
| Metric | Baseline | Target (6 months) | Measurement |
|--------|----------|-------------------|-------------|
| Tutor churn rate | TBD (synthetic baseline) | -30% reduction | Monthly retention rate |
| First session failure rate | 24% | <10% | % of first sessions with rating <3/5 |
| Tutor-initiated reschedules | 98.2% of all reschedules | <75% | % of reschedules initiated by tutors |
| No-show rate | 16% replacement cause | <8% | % of sessions resulting in no-shows |
| Insight latency | N/A | <60 minutes | Time from session end to dashboard update |
| Intervention acceptance rate | N/A | >70% | % of recommended interventions acted upon |

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                   Synthetic Data Generation Engine               │
│  (Continuous simulation of tutors, sessions, students, events)  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Processing Pipeline                    │
│          (Real-time ingestion, validation, enrichment)           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┼────────────┐
                ▼            ▼            ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │ Performance  │ │    Churn     │ │ Intervention │
    │  Evaluation  │ │  Prediction  │ │    Engine    │
    │    Engine    │ │    System    │ │              │
    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
           │                │                │
           └────────────────┼────────────────┘
                            ▼
           ┌────────────────────────────────┐
           │      Dashboard & UI Layer      │
           ├────────────────────────────────┤
           │ • Ops/People Ops Dashboard     │
           │ • Tutor Performance Portal     │
           │ • Student Feedback Flow        │
           └────────────────────────────────┘
```

---

## Component 1: Synthetic Data Generation Engine

### Purpose
Generate realistic, continuous data to seed and test the system in the absence of real data sources.

### Data Types Generated

#### 1.1 Tutor Profiles
- **Tutor ID**: Unique identifier
- **Demographics**: Age, location, education level, subject expertise
- **Tenure**: Days since onboarding
- **Baseline Activity**: Sessions per week (mean: 15, range: 5-30)
- **Behavioral Archetypes**:
  - **High Performer** (30%): Consistent, low reschedules, high ratings
  - **At-Risk** (20%): Declining engagement, increasing reschedules
  - **New Tutor** (25%): <30 days tenure, variable performance
  - **Steady** (20%): Average metrics, stable
  - **Churner** (5%): Exhibiting churn signals

#### 1.2 Session Data (3,000/day)
```json
{
  "session_id": "unique_id",
  "tutor_id": "tutor_123",
  "student_id": "student_456",
  "session_number": 1,  // 1 = first session
  "scheduled_start": "2025-11-07T10:00:00Z",
  "actual_start": "2025-11-07T10:05:00Z",
  "duration_minutes": 60,
  "subject": "Mathematics",
  "session_type": "1-on-1",
  "tutor_initiated_reschedule": false,
  "no_show": false,
  "late_start_minutes": 5,
  "engagement_score": 0.85,  // 0-1, derived from simulated interactions
  "student_rating": 4.5,      // 1-5
  "student_feedback_text": "Great session, very helpful!",
  "learning_objectives_met": true,
  "technical_issues": false
}
```

#### 1.3 Tutor Behavior Events
- **Reschedule requests**: Timing, frequency, reasons
- **Login patterns**: Last login, login frequency, session prep time
- **Communication metrics**: Response time to messages, student inquiries
- **Availability changes**: Reduced hours, schedule gaps
- **Training completion**: Professional development engagement

#### 1.4 Churn Indicators
- **Voluntary resignation**: Explicit departure signal (1-2% monthly rate)
- **Inactivity threshold**: No sessions for >14 consecutive days
- **Reduced activity**: <50% of baseline sessions per week for 3+ weeks
- **Engagement decline**: 30%+ drop in login frequency over 2 weeks

#### 1.5 Student Feedback Data
```json
{
  "feedback_id": "unique_id",
  "session_id": "session_123",
  "student_id": "student_456",
  "tutor_id": "tutor_123",
  "overall_rating": 4,        // 1-5
  "first_session": true,
  "ratings": {
    "subject_knowledge": 5,
    "communication": 4,
    "patience": 5,
    "engagement": 3,
    "helpfulness": 4
  },
  "would_recommend": true,
  "free_text_feedback": "Tutor was knowledgeable but seemed distracted",
  "timestamp": "2025-11-07T11:05:00Z"
}
```

### Data Generation Rules
1. **Volume**: 3,000 sessions/day distributed across ~200-300 active tutors
2. **Realism**: Apply temporal patterns (weekday/weekend, time-of-day variations)
3. **Correlations**:
   - First session ratings correlate with tutor tenure (newer tutors: lower avg ratings)
   - High reschedule rates (>3/week) predict churn within 30 days
   - No-shows cluster in morning slots and Mondays
4. **Signal Injection**: Embed realistic churn signals (declining engagement → reduced activity → churn)
5. **Refresh Rate**: Continuous generation, updates every 15 minutes

---

## Component 2: Performance Evaluation Engine

### Metrics Tracked

#### 2.1 Core Performance Metrics
| Metric | Calculation | Threshold |
|--------|-------------|-----------|
| **Session Rating Average** | Mean of last 30 sessions | <3.5 = underperforming |
| **First Session Success Rate** | % of first sessions with rating ≥4 | <70% = flag |
| **Reschedule Rate** | Reschedules / Total sessions (30-day window) | >15% = high |
| **No-Show Rate** | No-shows / Scheduled sessions (30-day) | >5% = concerning |
| **Engagement Score** | Composite of login frequency, session prep, communication | <60% = disengaged |
| **Learning Objectives Met %** | % of sessions where objectives achieved | <80% = needs improvement |

#### 2.2 Secondary Metrics (Retention Influencers)
- **Student satisfaction scores** (overall, by subject, by session type)
- **Response time** to student messages (avg, p95)
- **Professional development** completion rate
- **Availability consistency** (schedule changes per week)
- **Technical proficiency** (issues per session)

### Evaluation Frequency
- **Real-time**: Session completion triggers immediate evaluation
- **Daily rollup**: Aggregate metrics updated at midnight UTC
- **Weekly trends**: 7-day moving averages calculated
- **Monthly reviews**: Performance tier assignment

### Performance Tiers
| Tier | Criteria | Population % (Target) |
|------|----------|----------------------|
| **Exemplary** | Top 10%, all metrics green | 10% |
| **Strong** | Above average, no red flags | 40% |
| **Developing** | Average, some improvement areas | 35% |
| **Needs Attention** | Below average, intervention needed | 12% |
| **At Risk** | Critical issues, high churn probability | 3% |

---

## Component 3: Churn Prediction System

### 3.1 Churn Score (0-100)
A composite risk score indicating likelihood of churn across multiple time windows.

**Score Components:**
```
Churn Score = (
  0.25 × Engagement Decline Score +
  0.20 × Performance Trend Score +
  0.15 × Reschedule Pattern Score +
  0.15 × First Session Quality Score +
  0.10 × No-Show Risk Score +
  0.10 × Tenure Risk Score +
  0.05 × Availability Reduction Score
)
```

**Risk Levels:**
- **0-25**: Low risk (green)
- **26-50**: Medium risk (yellow)
- **51-75**: High risk (orange)
- **76-100**: Critical risk (red)

### 3.2 Multi-Timeframe Prediction Windows

Operators can view churn probability across different horizons:

| Window | Definition | Use Case |
|--------|------------|----------|
| **1-Day** | Immediate risk indicators (e.g., sudden availability drops) | Emergency intervention |
| **7-Day** | Short-term churn signals | Proactive coaching |
| **30-Day** | Standard prediction window | Strategic planning |
| **90-Day** | Long-term trend analysis | Capacity planning, hiring |

**UI View:**
```
Tutor: Jane Doe (#12345)
┌──────────────────────────────────────────┐
│ Churn Risk Score: 68 (High Risk)         │
├──────────────────────────────────────────┤
│ 1-Day:   45% (Medium)                    │
│ 7-Day:   72% (High)      ← Primary alert │
│ 30-Day:  68% (High)                      │
│ 90-Day:  55% (Medium)                    │
└──────────────────────────────────────────┘
```

### 3.3 Pattern Detection for Retention Issues

#### Pattern 1: Poor First Session Experience (24% of churners)
**Signals:**
- First session rating <3/5
- Student "would not recommend" = false
- Late start >10 minutes on first session
- No follow-up session scheduled

**Detection Logic:**
```python
if (is_first_session && rating < 3) || (is_first_session && late_start > 10):
    flag_as_poor_first_session_experience()
    churn_risk += 15
```

#### Pattern 2: High Rescheduling Rate (98.2% tutor-initiated)
**Signals:**
- >3 reschedules in 7-day window
- Reschedule timing: <24 hours before session
- Reschedule reasons: Personal, scheduling conflict

**Detection Logic:**
```python
if tutor_initiated_reschedules_7day > 3:
    flag_as_high_reschedule_pattern()
    churn_risk += 20
```

#### Pattern 3: No-Show Risk (16% of replacements)
**Signals:**
- No-show in last 14 days
- Declining login frequency (>30% drop)
- Missed >2 sessions without notice

**Detection Logic:**
```python
if no_shows_14day > 0 || (login_decline > 0.3 && missed_sessions > 2):
    flag_as_no_show_risk()
    churn_risk += 25
```

### 3.4 ML Model Architecture

**Model Type:** Gradient Boosted Trees (XGBoost) for interpretability and performance

**Features (30+ total):**
- Tenure (days since onboarding)
- Session count (7-day, 30-day, 90-day)
- Rating averages (7-day, 30-day moving averages)
- Reschedule rate (7-day, 30-day)
- No-show count (14-day, 30-day)
- Engagement score trend (% change over 14 days)
- First session success rate
- Response time to messages (p50, p95)
- Availability hours (current week vs. 4-week average)
- Days since last login
- Professional development completion %
- Subject diversity (# of subjects taught)

**Training:**
- Initial training on 90 days of synthetic data
- Daily retraining with new data
- Feature importance tracking for model transparency

**Validation:**
- 70/15/15 train/validation/test split
- Target metric: AUC-ROC >0.85 for 30-day churn prediction
- Calibration: Predicted probabilities should match actual churn rates

---

## Component 4: Intervention Framework

### 4.1 Intervention Types

#### Automated Interventions (No Human Review Required)

**A1. Automated Coaching Tips**
- **Trigger**: Performance metric drops below threshold
- **Action**: Email with specific resources (e.g., "Improve First Session Success: 5 Tips")
- **Frequency**: Max 1/week per tutor
- **Example**: First session rating <3.5 → Send "First Session Excellence Guide"

**A2. Training Module Suggestions**
- **Trigger**: Skill gap detected (low subject knowledge ratings)
- **Action**: Assign relevant online training module
- **Tracking**: Monitor completion within 7 days

**A3. First Session Quality Check-ins**
- **Trigger**: Every first session with a new student
- **Action**: Automated survey to tutor 2 hours post-session ("How did it go?")
- **Purpose**: Proactive engagement, signal collection

**A4. Rescheduling Pattern Alerts**
- **Trigger**: 3+ reschedules in 7 days
- **Action**: Automated message: "We noticed you've rescheduled often. Need help with scheduling?"
- **Escalation**: If continues for 14 days → flag for manager review

#### Human-Reviewed Interventions (Require Manager Action)

**H1. Manager-Assigned Coaching Sessions**
- **Trigger**: Churn score >50 (high risk) for 7+ days
- **Action**: Manager schedules 30-min 1:1 coaching call
- **SLA**: Within 48 hours of recommendation
- **Owner**: Operations Manager

**H2. Peer Mentoring Matches**
- **Trigger**: "Developing" tier + tenure <60 days
- **Action**: Match with "Exemplary" tier tutor in same subject
- **Duration**: 4-week mentorship program
- **Owner**: People Ops

**H3. Performance Improvement Plan (PIP)**
- **Trigger**: Churn score >75 (critical) OR "Needs Attention" tier for 30+ days
- **Action**: Formal PIP with specific goals, weekly check-ins
- **Duration**: 30-60 days
- **Owner**: People Ops + Direct Manager

**H4. Retention Interviews**
- **Trigger**: Churn score >60 + reduced activity detected
- **Action**: Proactive conversation to understand issues, offer support
- **Purpose**: Prevent voluntary resignation
- **Owner**: People Ops

**H5. Incentive/Recognition Programs**
- **Trigger**: Sustained high performance (Exemplary tier for 60+ days)
- **Action**: Bonus, public recognition, increased rates
- **Purpose**: Retention of top performers

### 4.2 Risk-Based Intervention Mapping

| Risk Level | Churn Score | Automated Interventions | Human-Reviewed Interventions |
|------------|-------------|------------------------|------------------------------|
| **Low** (Green) | 0-25 | A3 (First session check-ins only) | H5 (Recognition if applicable) |
| **Medium** (Yellow) | 26-50 | A1, A2, A3 | H2 (Peer mentoring for new tutors) |
| **High** (Orange) | 51-75 | A1, A2, A3, A4 | H1 (Coaching), H4 (Retention interview) |
| **Critical** (Red) | 76-100 | All automated | H1, H3 (PIP), H4 (Urgent retention interview) |

### 4.3 Intervention Workflow

```
1. System detects risk signal
   ↓
2. Churn score calculated/updated
   ↓
3. Intervention Engine evaluates rules
   ↓
4a. AUTOMATED PATH              4b. HUMAN-REVIEW PATH
    - Execute immediately           - Create intervention task
    - Log action taken              - Assign to appropriate manager
    - Track tutor response          - Set SLA timer
                                    - Send notification
                                    ↓
                                    Manager reviews & acts
                                    ↓
                                    Manager logs outcome
   ↓                                ↓
5. Monitor effectiveness
   ↓
6. Update churn score based on intervention impact
```

### 4.4 Intervention Effectiveness Tracking

**Metrics:**
- **Acceptance Rate**: % of recommended interventions acted upon (target: >70%)
- **Completion Rate**: % of interventions fully executed (target: >85%)
- **Impact Rate**: % of tutors showing improvement post-intervention (target: >60%)
- **Time to Action**: Hours from recommendation to manager action (target: <24h for critical)

**Feedback Loop:**
- A/B testing of intervention strategies
- ML model learns from successful interventions
- Quarterly review of intervention effectiveness by risk level

---

## User Personas & Workflows

### Persona 1: Operations Manager (Sarah)

**Goals:**
- Monitor overall tutor performance
- Identify and address issues before they escalate
- Allocate coaching resources efficiently

**Workflow:**
1. **Daily Morning Review** (15 min)
   - Check dashboard for new critical alerts
   - Review overnight session summaries
   - Assign high-priority intervention tasks to team

2. **Weekly Deep Dive** (1 hour)
   - Analyze churn trends by subject, tenure, region
   - Review intervention completion rates
   - Adjust coaching priorities based on data

3. **Monthly Planning** (2 hours)
   - Evaluate system effectiveness (churn reduction, retention metrics)
   - Plan capacity based on 90-day churn predictions
   - Present findings to leadership

**Key Dashboard Views:**
- High-risk tutor queue (sorted by churn score)
- Intervention task list (pending, in-progress, completed)
- System-wide KPIs (churn rate, first session success, no-show rate)

---

### Persona 2: People Ops Specialist (Marcus)

**Goals:**
- Execute retention strategies
- Conduct coaching and mentorship programs
- Improve tutor satisfaction and engagement

**Workflow:**
1. **Intervention Execution** (ongoing)
   - Review assigned tasks (PIPs, retention interviews, mentorship matching)
   - Schedule and conduct 1:1s with at-risk tutors
   - Document outcomes and recommendations in system

2. **Proactive Outreach** (weekly)
   - Reach out to tutors in "Needs Attention" tier
   - Celebrate exemplary performers
   - Gather qualitative feedback on tutor experience

3. **Program Management** (monthly)
   - Track mentorship program outcomes
   - Analyze PIP success rates
   - Recommend new intervention strategies based on patterns

**Key Dashboard Views:**
- My intervention queue (assigned tasks with SLAs)
- Tutor profiles (detailed performance, history, notes)
- Intervention outcome tracking

---

### Persona 3: Tutor (Emily)

**Goals:**
- Understand her performance
- Improve ratings and student satisfaction
- Access resources for professional growth

**What Emily CAN See:**
- Her overall performance tier (without exact churn score)
- Session ratings and student feedback (anonymized)
- Trend charts: ratings over time, sessions completed, subjects taught
- Recommended training modules
- Achievements and recognitions

**What Emily CANNOT See:**
- Churn score or risk level (to avoid anxiety/gaming the system)
- Other tutors' performance (privacy)
- Internal coaching notes or intervention details

**Workflow:**
1. **Post-Session** (5 min)
   - Review student feedback from latest session
   - Complete brief self-reflection (optional)

2. **Weekly Check-in** (15 min)
   - Review performance dashboard
   - Complete any recommended training modules
   - Set personal goals for upcoming week

3. **Monthly Growth** (30 min)
   - Review monthly performance summary
   - Explore new subjects or session types
   - Engage with peer mentorship if available

**Key Portal Views:**
- Performance overview (tier, trends, highlights)
- Recent feedback & ratings
- Training & resources library
- Session history & schedule

---

### Persona 4: Student (Alex, 16 years old)

**Goals:**
- Get effective tutoring help
- Provide feedback on session quality
- Influence tutor accountability

**Workflow:**
1. **Post-Session Feedback** (2 min) - **CRITICAL FOR FIRST SESSIONS**
   - Automated prompt appears within 5 min of session end
   - Quick ratings: Overall (1-5 stars), specific dimensions (knowledge, patience, etc.)
   - Optional: Free-text feedback
   - **Special for first sessions**: "Would you want to work with this tutor again?"

2. **First Session Experience Capture** (Extra step for session #1)
   - Additional question: "How was your first experience?" (Great/Good/OK/Poor)
   - If Poor/OK: "What could have been better?" (checkboxes + text)
   - Flagged immediately for review if Poor

**Key UI Flows:**
- Simple, mobile-friendly feedback form
- Gamification: "Your feedback helps improve tutoring quality!"
- Privacy: "Your tutor sees ratings but not your name on feedback"

---

## UI Requirements

### UI System 1: Ops/People Ops Dashboard

**Platform:** Web application (responsive, desktop-first)

**Core Views:**

#### 1.1 Home Dashboard
```
┌─────────────────────────────────────────────────────────────┐
│ Tutor Performance Overview                    [Date: Today] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  📊 System KPIs                                              │
│  ┌────────────┬────────────┬────────────┬──────────────┐   │
│  │ Total      │ At Risk    │ First Sess │ No-Show Rate │   │
│  │ Tutors     │ Tutors     │ Success    │              │   │
│  │ 287        │ 12 (4.2%)  │ 78%        │ 9.3%         │   │
│  │ ━━ +5      │ ━━ +2 🔴  │ ━━ -3% 🟡 │ ━━ +1.1% 🔴 │   │
│  └────────────┴────────────┴────────────┴──────────────┘   │
│                                                               │
│  🚨 Critical Alerts (12)                    [View All]       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 🔴 Jane Doe (#12345) - Churn Score: 82 (Critical)    │  │
│  │    ↳ 3 no-shows in 7 days, last login 4 days ago     │  │
│  │    📋 Recommended: Urgent retention interview         │  │
│  │    [Assign to Me] [Assign to Marcus] [View Profile]  │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │ 🟠 John Smith (#23456) - Churn Score: 68 (High)      │  │
│  │    ↳ 5 reschedules in 14 days, ratings declining     │  │
│  │    📋 Recommended: Coaching session                   │  │
│  │    [Assign to Me] [Assign to Sarah] [View Profile]   │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  📋 My Intervention Queue (5 pending)        [View All]      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ • PIP Check-in: Emily Chen (#34567) - Due in 2 hours │  │
│  │ • Retention Interview: Mike Johnson (#45678)         │  │
│  │ • Mentorship Match: Sarah Lee (#56789)               │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  📈 Churn Trend (30-Day)                                     │
│  [Line chart showing daily churn risk distribution]          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Real-time updates (WebSocket connections)
- Filterable alerts (by risk level, tutor tier, subject)
- One-click intervention assignment
- Exportable reports (CSV, PDF)

#### 1.2 Tutor Profile Deep Dive
```
Tutor: Jane Doe (#12345)                           [Edit] [Flag]
┌─────────────────────────────────────────────────────────────┐
│ Risk & Performance                                           │
├─────────────────────────────────────────────────────────────┤
│ 🔴 Churn Risk Score: 82 (Critical)                          │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ 1-Day: 75%  │ 7-Day: 88%  │ 30-Day: 82% │ 90-Day: 70% │  │
│ └──────────────────────────────────────────────────────┘   │
│                                                               │
│ Performance Tier: Needs Attention                            │
│ Tenure: 124 days                                             │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│ 📊 Metrics (Last 30 Days)                                    │
├─────────────────────────────────────────────────────────────┤
│ Sessions Completed:      18 (↓ 40% vs. baseline)            │
│ Avg Rating:              3.2 / 5.0 (🔴 Below threshold)     │
│ First Session Success:   50% (2/4 rated <3)                 │
│ Reschedule Rate:         27% (5/18 sessions)                │
│ No-Show Count:           3                                   │
│ Engagement Score:        42% (🔴 Disengaged)                │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│ 🚩 Active Flags                                              │
├─────────────────────────────────────────────────────────────┤
│ • High Reschedule Pattern (triggered 7 days ago)            │
│ • No-Show Risk (triggered 3 days ago)                       │
│ • Engagement Decline (40% drop in 14 days)                  │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│ 🔧 Intervention History                                      │
├─────────────────────────────────────────────────────────────┤
│ Nov 5: Automated coaching tips sent (opened: yes)           │
│ Nov 3: Rescheduling pattern alert (no response)             │
│ Oct 28: Peer mentoring offered (declined)                   │
│                                                               │
│ [+ Create New Intervention]                                  │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│ 💬 Recent Student Feedback                                   │
├─────────────────────────────────────────────────────────────┤
│ Session #142 (Nov 6): ⭐⭐⭐ "Tutor seemed tired"           │
│ Session #141 (Nov 4): ⭐⭐⭐⭐ "Helpful but rushed"         │
│ Session #138 (Oct 30): ⭐⭐ "Late to session, unprepared"  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Full performance history (drill-down charts)
- Notes field for manager annotations
- Intervention creation wizard
- Communication log (emails, messages sent)

#### 1.3 Analytics & Reporting
- **Churn heatmap**: By subject, day of week, tutor tenure cohort
- **Intervention effectiveness**: Success rates by type
- **Cohort analysis**: New tutors (<30 days) vs. tenured
- **Predictive insights**: "15 tutors predicted to churn in next 30 days"

---

### UI System 2: Tutor Performance Portal

**Platform:** Web + mobile-responsive

**Core Views:**

#### 2.1 Tutor Dashboard
```
Welcome back, Emily! 👋
┌─────────────────────────────────────────────────────────────┐
│ Your Performance                                             │
├─────────────────────────────────────────────────────────────┤
│ 🌟 Performance Tier: Strong                                 │
│ You're in the top 35% of tutors! Keep up the great work.    │
│                                                               │
│ This Week:                                                   │
│ • 12 sessions completed                                      │
│ • 4.6 / 5.0 average rating ⭐⭐⭐⭐⭐                       │
│ • 95% on-time starts                                         │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│ 📈 Trends (Last 30 Days)                                     │
├─────────────────────────────────────────────────────────────┤
│ [Line chart: Average rating over time]                       │
│ Sessions: 48 | Avg Rating: 4.5 | Students helped: 32        │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│ 💬 Recent Student Feedback                                   │
├─────────────────────────────────────────────────────────────┤
│ Session (Nov 6): ⭐⭐⭐⭐⭐                                  │
│ "Emily explained calculus concepts so clearly! Very patient."│
│                                                               │
│ Session (Nov 5): ⭐⭐⭐⭐                                    │
│ "Good session, helpful examples."                            │
│                                                               │
│ [View All Feedback]                                          │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│ 🎯 Recommended for You                                       │
├─────────────────────────────────────────────────────────────┤
│ • 📚 Training: "Advanced Engagement Techniques" (15 min)    │
│ • 💡 Tip: 90% of top tutors start sessions within 2 min     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Positive, growth-oriented framing (no churn scores shown)
- Actionable tips and encouragement
- Gamification: Badges for milestones (100 sessions, 4.8+ rating, etc.)
- Peer comparison (optional, anonymized): "Your rating is higher than 68% of tutors"

#### 2.2 Feedback & Growth
- Detailed breakdown of ratings by category (subject knowledge, patience, etc.)
- Student quotes (filtered for constructive feedback)
- Goal-setting: "Improve first session rating to 4.7"

#### 2.3 Resources Library
- Training modules organized by skill area
- Best practice guides
- Community forum (future feature)

---

### UI System 3: Student Feedback Flow

**Platform:** Web (post-session popup) + mobile app + email fallback

**Flow:**

#### Step 1: Immediate Post-Session Prompt (within 5 min)
```
┌─────────────────────────────────────────┐
│ How was your session with [Tutor Name]? │
├─────────────────────────────────────────┤
│                                          │
│     ⭐ ⭐ ⭐ ⭐ ⭐                      │
│   (Tap to rate: 1-5 stars)              │
│                                          │
│ [Skip for now]        [Submit Rating]   │
└─────────────────────────────────────────┘
```

#### Step 2: Detailed Feedback (if they rate)
```
┌─────────────────────────────────────────┐
│ Thanks! Help us improve:                │
├─────────────────────────────────────────┤
│ Rate these areas (optional):            │
│                                          │
│ Subject Knowledge:    ⭐⭐⭐⭐⭐       │
│ Communication:        ⭐⭐⭐⭐⭐       │
│ Patience:             ⭐⭐⭐⭐⭐       │
│ Helpfulness:          ⭐⭐⭐⭐⭐       │
│                                          │
│ Any additional thoughts?                │
│ [Text box: 500 char limit]              │
│                                          │
│ [Skip]                      [Submit]    │
└─────────────────────────────────────────┘
```

#### Step 3: First Session Special (ONLY for session #1)
```
┌─────────────────────────────────────────┐
│ 🎉 This was your first session!         │
├─────────────────────────────────────────┤
│ Would you want to work with             │
│ [Tutor Name] again?                     │
│                                          │
│     [Yes, definitely!]                  │
│     [Maybe]                              │
│     [Probably not]                       │
│     [No]                                 │
│                                          │
└─────────────────────────────────────────┘
```

**If "Probably not" or "No" selected:**
```
┌─────────────────────────────────────────┐
│ We're sorry to hear that.               │
│ What could have been better?            │
├─────────────────────────────────────────┤
│ ☐ Tutor was late                        │
│ ☐ Tutor seemed unprepared               │
│ ☐ Didn't explain things clearly         │
│ ☐ Wasn't patient or encouraging         │
│ ☐ Technical issues                      │
│ ☐ Other: [text field]                   │
│                                          │
│ [Submit Feedback]                       │
└─────────────────────────────────────────┘
```
**→ This triggers immediate "Poor First Session Experience" flag**

**Features:**
- Mobile-optimized (most students on mobile)
- Low friction (2-click minimum path)
- Privacy-conscious messaging
- Email reminder if no feedback after 24 hours

---

## Data Model

### Core Entities

#### Tutors
```sql
tutors
├── tutor_id (PK)
├── name
├── email
├── onboarding_date
├── status (active, inactive, churned)
├── subjects (array)
├── education_level
├── location
├── baseline_sessions_per_week
├── behavioral_archetype (for synthetic data)
├── created_at
└── updated_at
```

#### Students
```sql
students
├── student_id (PK)
├── name
├── age
├── grade_level
├── subjects_interested (array)
├── created_at
└── updated_at
```

#### Sessions
```sql
sessions
├── session_id (PK)
├── tutor_id (FK)
├── student_id (FK)
├── session_number (per student-tutor pairing)
├── scheduled_start
├── actual_start
├── duration_minutes
├── subject
├── session_type (1-on-1, group)
├── tutor_initiated_reschedule (boolean)
├── no_show (boolean)
├── late_start_minutes
├── engagement_score (0-1)
├── learning_objectives_met (boolean)
├── technical_issues (boolean)
├── created_at
└── updated_at
```

#### Feedback
```sql
student_feedback
├── feedback_id (PK)
├── session_id (FK)
├── student_id (FK)
├── tutor_id (FK)
├── overall_rating (1-5)
├── is_first_session (boolean)
├── subject_knowledge_rating
├── communication_rating
├── patience_rating
├── engagement_rating
├── helpfulness_rating
├── would_recommend (boolean, for first sessions)
├── improvement_areas (array, for poor first sessions)
├── free_text_feedback
├── submitted_at
└── created_at
```

#### Performance Metrics (Calculated/Aggregated)
```sql
tutor_performance_metrics
├── metric_id (PK)
├── tutor_id (FK)
├── calculation_date
├── window (7day, 30day, 90day)
├── sessions_completed
├── avg_rating
├── first_session_success_rate
├── reschedule_rate
├── no_show_count
├── engagement_score
├── learning_objectives_met_pct
├── response_time_avg_minutes
├── performance_tier (Exemplary, Strong, Developing, Needs Attention, At Risk)
├── created_at
└── updated_at
```

#### Churn Predictions
```sql
churn_predictions
├── prediction_id (PK)
├── tutor_id (FK)
├── prediction_date
├── churn_score (0-100)
├── risk_level (Low, Medium, High, Critical)
├── window_1day_probability
├── window_7day_probability
├── window_30day_probability
├── window_90day_probability
├── contributing_factors (JSON: {engagement_decline: 0.3, reschedule_pattern: 0.25, ...})
├── model_version
├── created_at
└── updated_at
```

#### Interventions
```sql
interventions
├── intervention_id (PK)
├── tutor_id (FK)
├── intervention_type (automated_coaching, peer_mentoring, PIP, etc.)
├── trigger_reason
├── recommended_date
├── assigned_to (user_id, nullable for automated)
├── status (pending, in_progress, completed, cancelled)
├── due_date
├── completed_date
├── outcome (improved, no_change, declined, churned)
├── notes
├── created_at
└── updated_at
```

#### Tutor Events (for behavior tracking)
```sql
tutor_events
├── event_id (PK)
├── tutor_id (FK)
├── event_type (login, reschedule_request, availability_change, training_completed, etc.)
├── event_timestamp
├── metadata (JSON: event-specific details)
└── created_at
```

---

## Technical Architecture

### System Components

```
┌──────────────────────────────────────────────────────────────┐
│                     Application Layer                         │
├──────────────────────────────────────────────────────────────┤
│ • Ops Dashboard (React + TypeScript)                         │
│ • Tutor Portal (React + TypeScript)                          │
│ • Student Feedback UI (React + TypeScript)                   │
│ • REST API (Node.js/Express OR Python/FastAPI)               │
│ • WebSocket Server (for real-time updates)                   │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────┴─────────────────────────────────────┐
│                     Business Logic Layer                      │
├──────────────────────────────────────────────────────────────┤
│ • Performance Evaluation Engine (Python)                     │
│ • Churn Prediction Service (Python + ML libraries)           │
│ • Intervention Engine (Rules engine + workflow orchestrator) │
│ • Synthetic Data Generator (Python + Faker)                  │
└────────────────────────┬─────────────────────────────────────┘
                         │
┌────────────────────────┴─────────────────────────────────────┐
│                       Data Layer                              │
├──────────────────────────────────────────────────────────────┤
│ • Primary Database: PostgreSQL (relational data)             │
│ • Cache: Redis (real-time metrics, session state)            │
│ • Time-Series DB: TimescaleDB/InfluxDB (metrics over time)   │
│ • Message Queue: RabbitMQ/Kafka (event streaming)            │
│ • ML Model Store: MLflow (model versioning, tracking)        │
└──────────────────────────────────────────────────────────────┘
```

### Data Processing Pipeline

```
Session Completion Event
        ↓
[Message Queue] ← Synthetic Data Generator (continuous feed)
        ↓
[Ingestion Service]
   ├─ Validate data
   ├─ Enrich (add derived fields)
   └─ Persist to DB
        ↓
[Performance Evaluation Engine] (triggered every 15 min)
   ├─ Calculate metrics (7-day, 30-day, 90-day windows)
   ├─ Assign performance tier
   └─ Persist to tutor_performance_metrics
        ↓
[Churn Prediction Service] (triggered on metric updates)
   ├─ Load ML model
   ├─ Generate predictions (1d, 7d, 30d, 90d)
   ├─ Calculate churn score
   └─ Persist to churn_predictions
        ↓
[Intervention Engine] (triggered on churn score updates)
   ├─ Evaluate intervention rules
   ├─ Create intervention tasks
   ├─ Send automated interventions (email, in-app)
   ├─ Notify managers (high/critical risk)
   └─ Persist to interventions table
        ↓
[Dashboard Updates] (via WebSocket)
   └─ Push real-time updates to connected clients
```

**Latency Target:** <60 minutes from session end to dashboard update

### Technology Stack Recommendations

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Frontend** | React + TypeScript + Tailwind CSS | Modern, type-safe, component-based, fast development |
| **API** | Python FastAPI | Fast, async, auto-documentation, ML-friendly |
| **Database** | PostgreSQL 14+ | ACID compliance, JSON support, mature ecosystem |
| **Cache** | Redis | In-memory speed for real-time metrics |
| **Message Queue** | RabbitMQ | Reliable, straightforward for MVP |
| **ML Framework** | Scikit-learn, XGBoost, SHAP (explainability) | Proven, interpretable, production-ready |
| **Synthetic Data** | Faker, NumPy, Pandas | Flexible, realistic data generation |
| **Monitoring** | Prometheus + Grafana | Observability, alerting |
| **Hosting** | AWS/GCP (serverless options for scaling) | Scalable, managed services available |

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Load Balancer                        │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ API Server 1 │ │ API Server 2 │ │ API Server N │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        ▼
              ┌──────────────────┐
              │   PostgreSQL     │
              │   (Primary +     │
              │   Read Replicas) │
              └──────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              Background Workers (Auto-scaling)               │
├─────────────────────────────────────────────────────────────┤
│ • Synthetic Data Generator (continuous)                     │
│ • Performance Evaluator (every 15 min)                      │
│ • Churn Predictor (on-demand + batch)                       │
│ • Intervention Engine (event-driven)                        │
│ • ML Model Trainer (daily)                                  │
└─────────────────────────────────────────────────────────────┘
```

### Scalability Considerations

**For 3,000 sessions/day:**
- **Current load**: ~125 sessions/hour, ~2 sessions/minute
- **Database**: Single PostgreSQL instance sufficient for MVP
- **API**: 2-3 instances for redundancy
- **Workers**: 1-2 instances per job type

**For 10x growth (30,000 sessions/day):**
- **Database**: Read replicas, connection pooling
- **API**: Horizontal auto-scaling (5-10 instances)
- **Workers**: Message queue-based job distribution
- **ML**: Batch predictions instead of per-session

---

## ML Model Details

### Model 1: Churn Prediction (Primary)

**Algorithm:** Gradient Boosted Trees (XGBoost)

**Input Features (35 total):**

| Category | Features |
|----------|----------|
| **Tenure** | Days since onboarding, is_new_tutor (<30 days) |
| **Activity** | Sessions 7d/30d/90d, sessions_trend (% change), days_since_last_session |
| **Performance** | Avg rating 7d/30d, rating_trend, first_session_success_rate |
| **Engagement** | Login frequency 7d/30d, engagement_score, response_time_p50/p95 |
| **Behavioral** | Reschedule_rate_7d/30d, no_show_count_14d/30d, late_start_count |
| **Schedule** | Availability_hours_current_week, availability_change_pct |
| **Development** | Training_completion_rate, subjects_taught_count |
| **Temporal** | Day_of_week, month, is_holiday_season |

**Target Variable:**
- Binary: `churned_within_30_days` (1 if tutor churned within 30 days, 0 otherwise)
- For other windows (1d, 7d, 90d): Separate models OR multi-output model

**Training Process:**
1. **Data Collection**: 90 days of synthetic data (28,500 tutor-days)
2. **Feature Engineering**: Calculate rolling windows, trends, flags
3. **Train/Validation/Test Split**: 70/15/15 (temporal split to avoid leakage)
4. **Hyperparameter Tuning**: Grid search on validation set
5. **Model Evaluation**:
   - AUC-ROC target: >0.85
   - Precision at top 10% (high-risk group): >0.70
   - Calibration: Brier score <0.15
6. **Explainability**: SHAP values for feature importance
7. **Retraining**: Daily with new data, A/B test before deployment

**Output:**
- Probability scores (0-1) for each time window
- Churn score (0-100): Weighted combination of probabilities
- Feature contributions (top 3 factors driving risk)

### Model 2: First Session Success Prediction (Secondary)

**Purpose:** Predict likelihood of poor first session BEFORE it happens

**Algorithm:** Logistic Regression (for interpretability)

**Input Features:**
- Tutor tenure, avg rating (if >5 sessions), engagement score
- Time of day scheduled, subject, student age
- Tutor's historical first session success rate

**Target:**
- Binary: First session rating <3

**Use Case:**
- Pre-session alerts: "This first session has 60% risk of poor rating. Consider sending prep reminder."

---

## Compliance & Security

### Data Privacy (FERPA, COPPA)

**FERPA (Family Educational Rights and Privacy Act):**
- **Applies to:** Student educational records (feedback, session notes)
- **Requirements:**
  - No PII in analytics without consent
  - Anonymize student names in tutor-visible feedback
  - Access controls: Only authorized staff view student-tutor mappings
  - Data retention: 7-year max for educational records

**COPPA (Children's Online Privacy Protection Act):**
- **Applies to:** Students <13 years old
- **Requirements:**
  - Parental consent for data collection (handled at signup, outside this system's scope)
  - Minimal data collection: Only what's necessary for service
  - No third-party sharing of student data
  - Secure data storage and encryption

### Security Measures

1. **Authentication & Authorization:**
   - SSO/OAuth for all users
   - Role-based access control (RBAC):
     - Ops managers: Full dashboard access
     - People Ops: Intervention management, tutor profiles
     - Tutors: Own data only
     - Students: Own feedback only

2. **Data Encryption:**
   - At rest: AES-256 for database
   - In transit: TLS 1.3 for all API calls
   - PII fields: Additional encryption layer

3. **Audit Logging:**
   - All data access logged (who, what, when)
   - Quarterly compliance audits
   - Retention: 3 years

4. **Anonymization:**
   - Student names hashed in tutor-visible feedback
   - Aggregated analytics only (no individual student tracking in reports)

---

## Implementation Phases

### Phase 1: MVP Core (Weeks 1-8)

**Goals:**
- Synthetic data generation operational
- Basic performance evaluation
- Simple churn prediction (rule-based)
- Ops dashboard with core views
- Student feedback flow

**Deliverables:**
- [ ] Synthetic data generator producing 3,000 sessions/day
- [ ] Database schema implemented
- [ ] Performance metrics calculated (7-day, 30-day windows)
- [ ] Rule-based churn flagging (e.g., no-shows >2 in 14 days → high risk)
- [ ] Ops dashboard: Home view, tutor profiles, alert list
- [ ] Student feedback UI (web only)
- [ ] Basic automated interventions (coaching tips emails)

**Success Criteria:**
- System processes 3,000 sessions/day with <1 hour latency
- Dashboard loads in <2 seconds
- 90% synthetic data realism (passes manual review)

---

### Phase 2: ML & Advanced Interventions (Weeks 9-16)

**Goals:**
- ML-based churn prediction deployed
- Multi-timeframe predictions (1d, 7d, 30d, 90d)
- Full intervention framework
- Tutor portal launched

**Deliverables:**
- [ ] XGBoost churn model trained and deployed
- [ ] Churn score (0-100) calculation
- [ ] Multi-window predictions in dashboard
- [ ] Human-reviewed intervention workflows (task assignment, SLAs)
- [ ] Tutor performance portal (all core views)
- [ ] Email notifications for managers (critical alerts)
- [ ] A/B testing framework for interventions

**Success Criteria:**
- Churn prediction AUC-ROC >0.85
- Intervention acceptance rate >60%
- Tutor portal: 80% active tutor engagement within 2 weeks

---

### Phase 3: Optimization & Scale (Weeks 17-24)

**Goals:**
- System optimization for performance
- Advanced analytics and reporting
- Intervention effectiveness tracking
- Scalability testing

**Deliverables:**
- [ ] Performance optimizations (caching, query tuning)
- [ ] Advanced analytics dashboard (cohort analysis, churn heatmaps)
- [ ] Intervention outcome tracking & ML feedback loop
- [ ] Mobile-responsive student feedback (iOS/Android webview)
- [ ] API documentation & external integrations (if needed)
- [ ] Load testing for 10x scale (30,000 sessions/day)

**Success Criteria:**
- Dashboard load time <1 second
- System handles 10,000 sessions/day in load test
- Intervention impact rate >50% (tutors improve post-intervention)

---

### Phase 4: Real Data Transition (Weeks 25+)

**Goals:**
- Gradual replacement of synthetic data with real data
- Model retraining on real patterns
- System hardening

**Deliverables:**
- [ ] Real session data ingestion pipeline
- [ ] Hybrid mode: Real + synthetic data blending
- [ ] Model retraining on real churn events
- [ ] Production monitoring & alerting
- [ ] User training & documentation

**Success Criteria:**
- Smooth transition with no downtime
- Real data churn predictions maintain >0.80 AUC
- System uptime >99.5%

---

## Open Questions & Decisions Needed

1. **Synthetic Data Realism:**
   - Should we model specific subjects differently? (e.g., Math tutors vs. English tutors churn patterns)
   - What % of synthetic tutors should exhibit churn signals?

2. **Intervention Authority:**
   - Can automated interventions send emails directly, or require manager approval?
   - Who has authority to override churn predictions?

3. **Tutor Visibility Trade-offs:**
   - Should tutors see a "health score" instead of performance tier?
   - Risk of tutors gaming the system if too much visibility?

4. **Prediction Calibration:**
   - What's acceptable false positive rate for critical churn alerts?
   - Balance between over-alerting managers vs. missing at-risk tutors?

5. **Integration Future:**
   - Will this eventually integrate with payment/compensation systems?
   - Link to student outcomes (test scores, grades)?

---

## Success Metrics & KPIs (Recap)

| Metric | Target | Measurement Frequency |
|--------|--------|----------------------|
| **System uptime** | >99.5% | Continuous |
| **Insight latency** | <60 minutes | Per session |
| **Churn prediction accuracy** | AUC >0.85 | Weekly |
| **Tutor churn rate reduction** | -30% in 6 months | Monthly |
| **First session failure rate** | <10% (from 24%) | Weekly |
| **Tutor reschedule rate** | <75% tutor-initiated (from 98.2%) | Weekly |
| **No-show rate** | <8% (from 16%) | Weekly |
| **Intervention acceptance** | >70% | Monthly |
| **Intervention impact** | >60% show improvement | Quarterly |
| **Ops dashboard usage** | 90% of managers use daily | Monthly |
| **Tutor portal engagement** | 80% active users weekly | Weekly |

---

## Appendix

### A. Glossary

- **Churn**: Tutor departure via voluntary resignation, inactivity (>14 days no sessions), or reduced activity (<50% baseline for 3+ weeks)
- **First Session Experience**: The initial session between a tutor and a new student (session_number = 1)
- **Engagement Score**: Composite metric (0-100%) combining login frequency, session prep time, response time
- **Performance Tier**: Categorical ranking (Exemplary, Strong, Developing, Needs Attention, At Risk)
- **Intervention**: Proactive action (automated or human) to improve tutor retention or performance

### B. References

- [FERPA Compliance Guidelines](https://www2.ed.gov/policy/gen/guid/fpco/ferpa/index.html)
- [COPPA Requirements](https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions)
- XGBoost Documentation: https://xgboost.readthedocs.io/
- SHAP for Model Explainability: https://shap.readthedocs.io/

### C. Synthetic Data Sample

**Sample Tutor Journey (At-Risk → Churned):**
```
Day 1: Onboarded, 3 sessions, 4.8 avg rating
Day 15: 12 sessions, 4.6 avg, Tier: Strong
Day 30: 18 sessions, 4.5 avg, Tier: Strong
Day 45: 14 sessions (-22% vs Day 30), 4.2 avg, 2 reschedules → Tier: Developing
Day 50: 1st no-show, engagement_score drops to 65%
Day 55: System flags: High reschedule pattern, No-show risk
Day 56: Automated intervention: Coaching tips sent (opened)
Day 60: 8 sessions in last 15 days (-47% decline), avg 3.8 → Tier: Needs Attention
Day 62: Manager assigned retention interview (pending)
Day 68: Last login 6 days ago → Churn score: 78 (Critical)
Day 70: Manager attempts contact (no response)
Day 75: No sessions for 14 days → Status: Churned (Inactivity)
```

---

## Document Control

**Revision History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-07 | Product Team | Initial draft |

**Approval:**

- [ ] Product Lead
- [ ] Engineering Lead
- [ ] Operations Manager
- [ ] People Ops Lead

---

**Questions or Feedback?** Contact: [Product Team]
