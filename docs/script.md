[🎬 SCREEN: /dashboard - Show main dashboard with Critical Alerts section visible]

Churn is one of the most robust problems in tech businesses, and it's also inherent in the nature of platforms, especially ones that are driven by market forces.

Identifying why there is churn is one thing, but being able to do something about it is a completely different thing. Whether it's having a first experience that doesn't meet expectations or not fulfilling some internal personal standard, first identifying the patterns that indicate churn risk is the first step in mitigating it.

[🎬 SCREEN: Stay on /dashboard - Slowly pan to show full dashboard overview including Performance Tiers and Activity Heatmap]

Introducing TutorMax for Nerdy - an early warning and intervention system for tutor churn.

[🎬 SCREEN: Focus on Critical Alerts section at top of dashboard - show live alerts with risk badges (CRITICAL/HIGH/MEDIUM), tutor names, and "Create Intervention" action buttons]

The system operates in real-time, continuously analyzing tutor behavior and triggering immediate alerts when risk patterns emerge. You can see the Critical Alerts section here - these appear the moment a tutor crosses into high-risk territory, creating actionable tasks with SLA timers to ensure managers respond quickly.

[🎬 SCREEN: Pan down to highlight the Performance Tiers section showing Platinum/Gold/Silver/Bronze distribution with tutor counts in each tier]

We've also gamified performance through tier rankings - Platinum, Gold, Silver, and Bronze - giving tutors visible recognition and motivation to maintain high standards. 

[🎬 SCREEN: /dashboard - Click on Analytics tab, show the Churn Heatmap component]

At it's core, we are using two ML models - one is the Churn Prediction Model and the other is a First Session Prediction Model.

The Churn Prediction Model, which uses XGBoost (gradient boosting), predicts which tutors are likely to quit in the next 7, 14, 30, and 90 days.

And the First Session Prediction Model, which uses Logistic Regression, predicts which upcoming first tutoring sessions are likely to go poorly, and therefore get bad ratings, which could contribute to the 24% first-session churn rate.

[🎬 SCREEN: Navigate to /tutor/[id] - Individual tutor profile page. Navigate through Performance tab slowly to highlight each metric being discussed]

Churn Model - Needs Historical Behavior Data

  For each tutor, it looks at 50+ engineered features or factors, including:
  - Session history
    - How many sessions they completed
    - Session frequency (sessions per week)
    - Recent changes in volume
  - Performance data
    - Average student ratings
    - Engagement scores (login frequency, responsiveness)
    - Learning objectives met percentage
  - Behavioral patterns
    - Reschedule frequency
    - No-show incidents
    - First session success rates
  - Background info
    - How long they've been tutoring (tenure)
    - Their typical weekly workload

[🎬 SCREEN: Still on /tutor/[id] - Focus on TutorProfileHeaderV2 at the top showing the churn prediction score. Optional: Toggle to Flags tab to show active risk indicators]

  And the Model's Output is that every tutor gets a moving binary prediction, a yes will churn or no will not churn, across 7, 14, 30, and 90 day windows

[🎬 SCREEN: /tutor/[high-risk-id] - Switch to a HIGH-RISK tutor profile. Point out: churn score at top, declining metrics, critical flags, intervention history]

  Example input for one tutor:
  Tutor: Sarah Chen
  - 15 sessions in last 30 days (down from 25 previous month)
  - Average rating: 4.1 (down from 4.5)
  - 3 reschedules in last week
  - Engagement score: 0.32 (down from 0.75)
  - Tenure: 120 days

  Output: "72% probability of quitting in next 30 days" (CRITICAL RISK)

[🎬 SCREEN: /tutor-portal - Show the tutor self-view. Navigate to Performance tab or Sessions tab to show first session success tracking]

Now, here's where it gets interesting - tutors aren't just data points. They have access to their own portal where they can see their performance metrics, track their tier ranking, and understand exactly where they stand.

[🎬 SCREEN: Still on /tutor-portal - Highlight the tier badge (Gold/Silver/etc), performance metrics dashboard, and any improvement suggestions or goals visible to the tutor]

This self-service approach empowers tutors to take ownership of their improvement before they even need intervention.

First Session Model - Needs Tutor & Session Context

  For each upcoming first session, it looks at:
  - Tutor's track record
    - Overall rating average
    - Past first session success rate (% rated 4+ stars)
    - Total sessions completed
    - Engagement score
    - Reschedule and no-show rates
  - Session context
    - Subject being taught
    - Time of day scheduled
    - Day of week
    - Student age

[🎬 SCREEN: /tutor/[new-tutor-id] - Switch to a NEWER tutor with lower stats (5 sessions, 3.8 rating). Focus on: low session count, lower rating, first session success rate]

  Example input for one session:
  Upcoming Session:
  - Tutor: Mike Ross (new, only 5 sessions completed)
  - Subject: Spanish
  - Time: Saturday 8am
  - Student: 14 years old
  - Mike's stats:
    - Average rating: 3.8
    - First session success rate: 40% (only 2 of 5 went well)
    - Engagement score: 0.55

  Output: "65% probability of poor rating" (HIGH RISK) → Send prep email to Mike

[🎬 SCREEN: /interventions - Show intervention queue demonstrating how "Send prep email to Mike" would appear. Show SLA timers, intervention types, and task assignments]

	As far as the data is concerned, we synthesized blah blah blah data and then this was fed into the models to train them. The result of which was that, when tested on our initial training data, the first session model achieved 91% accuracy at predicting which sessions would go poorly, and the churn model showed similarly strong performance in identifying at-risk tutors.

	But here's what makes this valuable - predictions alone don't save tutors. The system automatically creates intervention tasks when risk is detected.

[🎬 SCREEN: Stay on /interventions - Scroll through the queue to show variety of intervention types. Point out: intervention type badges (Automated Coaching, Training Module, Manager Coaching, Peer Mentoring, PIP, Retention Interview, Recognition), SLA countdown timers (especially any in red/overdue), and manager assignments]

	The platform supports seven intervention types, ranging from automated coaching emails for low-risk cases, all the way up to manager-led retention interviews for critical situations. Each intervention has an SLA timer, so overdue tasks surface immediately. For someone like Sarah Chen with her 72% churn risk, the system would create a "Manager Coaching" intervention assigned to her supervisor with a 48-hour SLA.

	This transforms predictions into workflow - managers get actionable next steps, not just dashboards. And we can track intervention effectiveness over time to see which approaches actually reduce churn.

[🎬 SCREEN: /monitoring - Show System Health dashboard with Celery Tasks section. Point out "Last Model Training" timestamp or background job success metrics]

	Furthermore, the system is set up so that there will be ongoing training daily (at 2am), gathering thousands of sessions, and retraining the model to improve over time.

	This will help us be flexible as tutor's behavior evolves or as patterns change over time.

[🎬 SCREEN: /dashboard - Analytics tab → Cohort Analysis or Predictive Insights. Show trend analysis demonstrating how the system tracks patterns over time. Alternative: Show Activity Heatmap to visualize behavior patterns]

	And once real data is introduced, the model will learn to recognize the patterns automatically from thousands of real examples, finding the optimal thresholds and combinations that best predict the outcomes.

[🎬 SCREEN: /dashboard - Performance Tiers section showing tutor distribution. Alternative: /users page showing full tutor list with various performance levels]

	The biggest takeaway is that when we synthesized the data to just have a starting place to train the models, the strategy I settled on was creating five different types of tutors, high performers, steady performers, new tutors, at-risk tutors, and churners, and having the LLM generate what it believed to be realistic patterns.

[🎬 SCREEN: /dashboard Analytics tab → Intervention Effectiveness chart. Point to success rates by intervention type, showing which approaches work best]

	So what's the business impact? If we can reduce tutor churn by even 10-15%, that translates to massive cost savings in recruitment and training, better student experiences through continuity with experienced tutors, and reduced manager workload through automated early intervention.

[🎬 SCREEN: Zoom out to show full dashboard overview - Critical Alerts, Performance Tiers, Activity Heatmap, and Analytics together]

	The system pays for itself by keeping just a handful of high-performing tutors from leaving each quarter.

[🎬 SCREEN: Return to /dashboard - Full overview tab for closing shot. Show the complete system view to reinforce the comprehensive solution]

	This one took a little over 48 hours to complete, and it was really interesting to try and solve the problem and ultimately predict whether or not tutors would churn. Thanks for checking out TutorMax. Hope to see you soon!