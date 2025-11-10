"""
Intervention Framework for Tutor Performance and Churn Management

This module defines the intervention trigger rules and logic for the TutorMax
performance evaluation system. It implements automated and human-reviewed
interventions based on churn predictions and performance metrics.

Architecture:
    - Rule Engine: Evaluates tutor state against intervention criteria
    - Trigger System: Determines which interventions to activate
    - Priority System: Manages intervention scheduling and escalation
    - Integration Points: Connects to notification and task management systems
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
from pathlib import Path

# Import configuration
from .intervention_config import (
    InterventionConfig,
    ConfigManager,
    get_default_config
)

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# INTERVENTION TRIGGER CRITERIA
# ============================================================================

class InterventionType(str, Enum):
    """Types of interventions available in the system."""
    # Automated interventions
    AUTOMATED_COACHING = "automated_coaching"
    TRAINING_MODULE = "training_module"
    FIRST_SESSION_CHECKIN = "first_session_checkin"
    RESCHEDULING_ALERT = "rescheduling_alert"

    # Human-reviewed interventions
    MANAGER_COACHING = "manager_coaching"
    PEER_MENTORING = "peer_mentoring"
    PERFORMANCE_IMPROVEMENT_PLAN = "performance_improvement_plan"
    RETENTION_INTERVIEW = "retention_interview"

    # Positive interventions
    RECOGNITION = "recognition"


class InterventionPriority(str, Enum):
    """Priority levels for interventions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(str, Enum):
    """Churn risk levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class PerformanceTier(str, Enum):
    """Performance tier classifications."""
    EXEMPLARY = "Exemplary"
    STRONG = "Strong"
    DEVELOPING = "Developing"
    NEEDS_ATTENTION = "Needs Attention"
    AT_RISK = "At Risk"


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class TutorState:
    """
    Current state of a tutor used for intervention evaluation.

    This consolidates churn predictions, performance metrics, and behavioral
    indicators into a single structure for rule evaluation.
    """
    tutor_id: str
    tutor_name: str

    # Churn prediction data
    churn_probability: float  # 0-1 scale
    churn_score: int  # 0-100 scale
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL

    # Performance metrics (30-day window)
    avg_rating: Optional[float] = None
    first_session_success_rate: Optional[float] = None
    engagement_score: Optional[float] = None
    learning_objectives_met_pct: Optional[float] = None
    performance_tier: Optional[str] = None

    # Behavioral indicators (30-day window)
    no_show_rate: float = 0.0
    reschedule_rate: float = 0.0
    sessions_completed: int = 0
    sessions_per_week: float = 0.0

    # Trend indicators (comparing 7-day vs 30-day)
    engagement_decline: Optional[float] = None  # Positive = declining
    rating_decline: Optional[float] = None
    session_volume_decline: Optional[float] = None

    # Composite indicators
    behavioral_risk_score: Optional[float] = None  # Higher = more risk

    # Recent history
    recent_interventions: List[str] = field(default_factory=list)  # Last 30 days
    last_intervention_date: Optional[datetime] = None
    tenure_days: int = 0


@dataclass
class InterventionTrigger:
    """
    Definition of an intervention trigger rule.

    Each trigger defines:
    - When the intervention should activate
    - What type of intervention to create
    - Priority and timing
    - Human assignment requirements
    """
    intervention_type: InterventionType
    priority: InterventionPriority
    trigger_reason: str

    # Timing
    requires_immediate_action: bool = False
    due_days: int = 7  # Days until due after creation

    # Assignment
    requires_human: bool = False
    assigned_to: Optional[str] = None  # Role or specific person

    # Additional context
    recommended_actions: List[str] = field(default_factory=list)
    notes: Optional[str] = None


# ============================================================================
# INTERVENTION RULE ENGINE
# ============================================================================

class InterventionRuleEngine:
    """
    Evaluates tutor state against intervention rules.

    The rule engine implements a priority-based system:
    1. CRITICAL interventions (churn imminent)
    2. HIGH priority (performance/behavioral issues)
    3. MEDIUM priority (early warning signs)
    4. LOW priority (preventive/positive)

    Rules are evaluated in priority order, and multiple interventions
    can be triggered simultaneously for a single tutor.
    """

    def __init__(self, config: Optional[InterventionConfig] = None):
        """
        Initialize the rule engine.

        Args:
            config: Configuration object. If None, uses default configuration.
        """
        self.config = config or get_default_config()
        self.rules = self._initialize_rules()
        logger.info("InterventionRuleEngine initialized with configuration")

    def _initialize_rules(self) -> Dict[str, callable]:
        """
        Initialize intervention rule functions.

        Each rule function takes a TutorState and returns an optional
        InterventionTrigger if the rule is satisfied.
        """
        return {
            # CRITICAL priority rules
            'critical_churn_risk': self._rule_critical_churn_risk,
            'severe_performance_decline': self._rule_severe_performance_decline,

            # HIGH priority rules
            'high_churn_risk': self._rule_high_churn_risk,
            'poor_first_session_performance': self._rule_poor_first_session_performance,
            'excessive_rescheduling': self._rule_excessive_rescheduling,
            'low_engagement_pattern': self._rule_low_engagement_pattern,

            # MEDIUM priority rules
            'medium_churn_risk': self._rule_medium_churn_risk,
            'declining_ratings': self._rule_declining_ratings,
            'declining_session_volume': self._rule_declining_session_volume,
            'new_tutor_support': self._rule_new_tutor_support,

            # LOW priority rules (positive)
            'recognition_high_performer': self._rule_recognition_high_performer,
            'recognition_improvement': self._rule_recognition_improvement,
        }

    def evaluate_tutor(self, state: TutorState) -> List[InterventionTrigger]:
        """
        Evaluate a tutor's state and return triggered interventions.

        Args:
            state: Current tutor state with metrics and predictions

        Returns:
            List of intervention triggers, sorted by priority
        """
        logger.info(f"Evaluating tutor {state.tutor_id} for interventions")

        # Validate input
        if not self._validate_tutor_state(state):
            logger.warning(f"Invalid tutor state for {state.tutor_id}, skipping evaluation")
            return []

        # Skip evaluation if insufficient data
        min_sessions = self.config.thresholds.min_sessions_for_evaluation
        if state.sessions_completed < min_sessions:
            logger.debug(
                f"Tutor {state.tutor_id} has insufficient sessions "
                f"({state.sessions_completed} < {min_sessions}), skipping evaluation"
            )
            return []

        triggers = []
        rules_evaluated = 0
        rules_triggered = 0

        # Evaluate all rules
        for rule_name, rule_func in self.rules.items():
            # Check if rule is enabled
            if not self.config.enablement.is_enabled(rule_name):
                logger.debug(f"Rule {rule_name} is disabled, skipping")
                continue

            rules_evaluated += 1

            try:
                trigger = rule_func(state)
                if trigger:
                    # Filter by intervention type if configured
                    if not self._should_create_intervention(trigger):
                        logger.debug(
                            f"Intervention type {trigger.intervention_type} filtered out by config"
                        )
                        continue

                    # Check cooldown period
                    if self.config.require_cooldown_check and not self._check_cooldown(state, trigger):
                        logger.debug(
                            f"Intervention {trigger.intervention_type} in cooldown for tutor {state.tutor_id}"
                        )
                        continue

                    triggers.append(trigger)
                    rules_triggered += 1
                    logger.info(
                        f"Rule {rule_name} triggered {trigger.intervention_type} "
                        f"for tutor {state.tutor_id} (Priority: {trigger.priority})"
                    )
            except Exception as e:
                logger.error(
                    f"Error evaluating rule {rule_name} for tutor {state.tutor_id}: {e}",
                    exc_info=True
                )

        # Apply max interventions limit
        if len(triggers) > self.config.max_interventions_per_tutor:
            logger.warning(
                f"Tutor {state.tutor_id} triggered {len(triggers)} interventions, "
                f"limiting to {self.config.max_interventions_per_tutor}"
            )

        # Sort by priority (CRITICAL > HIGH > MEDIUM > LOW)
        priority_order = {
            InterventionPriority.CRITICAL: 0,
            InterventionPriority.HIGH: 1,
            InterventionPriority.MEDIUM: 2,
            InterventionPriority.LOW: 3
        }
        triggers.sort(key=lambda t: priority_order[t.priority])

        # Limit to max interventions
        triggers = triggers[:self.config.max_interventions_per_tutor]

        logger.info(
            f"Evaluation complete for tutor {state.tutor_id}: "
            f"{rules_evaluated} rules evaluated, {rules_triggered} triggered, "
            f"{len(triggers)} interventions returned"
        )

        return triggers

    def _validate_tutor_state(self, state: TutorState) -> bool:
        """
        Validate tutor state has required fields.

        Args:
            state: Tutor state to validate

        Returns:
            True if valid, False otherwise
        """
        if not state.tutor_id:
            logger.error("TutorState missing tutor_id")
            return False

        if state.churn_probability < 0 or state.churn_probability > 1:
            logger.error(f"Invalid churn_probability: {state.churn_probability}")
            return False

        if state.churn_score < 0 or state.churn_score > 100:
            logger.error(f"Invalid churn_score: {state.churn_score}")
            return False

        return True

    def _should_create_intervention(self, trigger: InterventionTrigger) -> bool:
        """
        Check if intervention should be created based on configuration.

        Args:
            trigger: Intervention trigger to check

        Returns:
            True if intervention should be created
        """
        # Check if automated interventions are enabled
        if not trigger.requires_human and not self.config.enable_automated_interventions:
            return False

        # Check if human interventions are enabled
        if trigger.requires_human and not self.config.enable_human_interventions:
            return False

        return True

    def _check_cooldown(self, state: TutorState, trigger: InterventionTrigger) -> bool:
        """
        Check if intervention type is in cooldown period.

        Prevents duplicate interventions from being triggered too frequently.
        """
        if not state.last_intervention_date:
            return True

        # Check if same intervention type was triggered recently
        if trigger.intervention_type.value in state.recent_interventions:
            days_since = (datetime.now() - state.last_intervention_date).days
            cooldown_days = self.config.timing.same_type_cooldown_days
            if days_since < cooldown_days:
                logger.debug(
                    f"Intervention {trigger.intervention_type} in cooldown "
                    f"({days_since} < {cooldown_days} days)"
                )
                return False

        return True

    # ========================================================================
    # CRITICAL PRIORITY RULES
    # ========================================================================

    def _rule_critical_churn_risk(self, state: TutorState) -> Optional[InterventionTrigger]:
        """
        CRITICAL: Tutor has critical churn risk (configurable threshold).

        Action: Immediate retention interview with manager.
        """
        threshold = self.config.thresholds.critical_churn_probability
        if state.churn_probability >= threshold:
            return InterventionTrigger(
                intervention_type=InterventionType.RETENTION_INTERVIEW,
                priority=InterventionPriority.CRITICAL,
                trigger_reason=f"Critical churn risk detected (probability: {state.churn_probability:.1%}, threshold: {threshold:.1%})",
                requires_immediate_action=True,
                due_days=self.config.timing.critical_due_days,
                requires_human=True,
                assigned_to="tutor_manager",
                recommended_actions=[
                    "Schedule immediate 1-on-1 with tutor",
                    "Understand root causes of dissatisfaction",
                    "Discuss retention incentives and support",
                    "Create personalized retention plan",
                    "Follow up within 48 hours"
                ],
                notes=f"Churn score: {state.churn_score}/100. Contributing factors should be reviewed."
            )
        return None

    def _rule_severe_performance_decline(self, state: TutorState) -> Optional[InterventionTrigger]:
        """
        CRITICAL: Severe performance decline across multiple metrics.

        Action: Performance improvement plan.
        """
        rating_threshold = self.config.thresholds.rating_decline_severe
        engagement_threshold = self.config.thresholds.engagement_decline_severe

        conditions = [
            state.performance_tier == PerformanceTier.AT_RISK.value,
            (state.rating_decline is not None and state.rating_decline > rating_threshold),
            (state.engagement_decline is not None and state.engagement_decline > engagement_threshold),
        ]

        if sum(1 for c in conditions if c) >= 2:  # At least 2 conditions met
            return InterventionTrigger(
                intervention_type=InterventionType.PERFORMANCE_IMPROVEMENT_PLAN,
                priority=InterventionPriority.CRITICAL,
                trigger_reason="Severe performance decline detected across multiple metrics",
                requires_immediate_action=True,
                due_days=self.config.timing.critical_due_days,
                requires_human=True,
                assigned_to="tutor_manager",
                recommended_actions=[
                    "Review performance metrics in detail",
                    "Create formal performance improvement plan",
                    "Set clear performance goals and timeline (30/60/90 days)",
                    "Schedule weekly check-ins",
                    "Provide additional training resources"
                ],
                notes=f"Performance tier: {state.performance_tier}, Rating decline: {state.rating_decline:.2f}, Engagement decline: {state.engagement_decline:.2f}"
            )
        return None

    # ========================================================================
    # HIGH PRIORITY RULES
    # ========================================================================

    def _rule_high_churn_risk(self, state: TutorState) -> Optional[InterventionTrigger]:
        """
        HIGH: Tutor has high churn risk (configurable threshold).

        Action: Manager coaching session.
        """
        threshold = self.config.thresholds.high_churn_probability
        critical_threshold = self.config.thresholds.critical_churn_probability

        if threshold <= state.churn_probability < critical_threshold:
            return InterventionTrigger(
                intervention_type=InterventionType.MANAGER_COACHING,
                priority=InterventionPriority.HIGH,
                trigger_reason=f"High churn risk detected (probability: {state.churn_probability:.1%}, threshold: {threshold:.1%})",
                requires_immediate_action=False,
                due_days=self.config.timing.high_due_days,
                requires_human=True,
                assigned_to="tutor_manager",
                recommended_actions=[
                    "Schedule coaching session with tutor",
                    "Review performance trends and challenges",
                    "Identify support needs and resources",
                    "Set goals for improvement",
                    "Plan follow-up within 2 weeks"
                ],
                notes=f"Churn score: {state.churn_score}/100"
            )
        return None

    def _rule_poor_first_session_performance(self, state: TutorState) -> Optional[InterventionTrigger]:
        """
        HIGH: Poor first session success rate (configurable threshold).

        Action: First session coaching and checkin process.
        """
        threshold = self.config.thresholds.poor_first_session_rate

        if (state.first_session_success_rate is not None and
            state.first_session_success_rate < threshold):
            return InterventionTrigger(
                intervention_type=InterventionType.FIRST_SESSION_CHECKIN,
                priority=InterventionPriority.HIGH,
                trigger_reason=f"Low first session success rate ({state.first_session_success_rate:.1%}, threshold: {threshold:.1%})",
                requires_immediate_action=False,
                due_days=self.config.timing.high_due_days,
                requires_human=True,
                assigned_to="tutor_coach",
                recommended_actions=[
                    "Review first session best practices with tutor",
                    "Provide first session checklist and tips",
                    "Schedule pre-session check-in for next first session",
                    "Monitor next 3 first sessions closely",
                    "Provide real-time feedback"
                ],
                notes=f"First session success rate: {state.first_session_success_rate:.1%}"
            )
        return None

    def _rule_excessive_rescheduling(self, state: TutorState) -> Optional[InterventionTrigger]:
        """
        HIGH: Excessive tutor-initiated rescheduling (configurable threshold).

        Action: Rescheduling alert and availability coaching.
        """
        threshold = self.config.thresholds.excessive_reschedule_rate

        if state.reschedule_rate > threshold:
            return InterventionTrigger(
                intervention_type=InterventionType.RESCHEDULING_ALERT,
                priority=InterventionPriority.HIGH,
                trigger_reason=f"High reschedule rate detected ({state.reschedule_rate:.1%}, threshold: {threshold:.1%})",
                requires_immediate_action=False,
                due_days=self.config.timing.high_due_days,
                requires_human=False,  # Can be automated initially
                assigned_to=None,
                recommended_actions=[
                    "Send automated reminder about availability commitments",
                    "Review tutor's scheduling patterns",
                    "Suggest calendar management tools",
                    "If pattern continues, escalate to manager coaching",
                ],
                notes=f"Reschedule rate: {state.reschedule_rate:.1%}, Sessions: {state.sessions_completed}"
            )
        return None

    def _rule_low_engagement_pattern(self, state: TutorState) -> Optional[InterventionTrigger]:
        """
        HIGH: Consistently low engagement scores (configurable threshold).

        Action: Training module on student engagement.
        """
        threshold = self.config.thresholds.low_engagement_score

        if (state.engagement_score is not None and
            state.engagement_score < threshold):
            return InterventionTrigger(
                intervention_type=InterventionType.TRAINING_MODULE,
                priority=InterventionPriority.HIGH,
                trigger_reason=f"Low engagement scores ({state.engagement_score:.2f}, threshold: {threshold:.2f})",
                requires_immediate_action=False,
                due_days=self.config.timing.high_due_days,
                requires_human=False,
                assigned_to=None,
                recommended_actions=[
                    "Assign 'Student Engagement Best Practices' training module",
                    "Provide interactive teaching techniques guide",
                    "Share example sessions from high-engagement tutors",
                    "Schedule follow-up to review progress in 2 weeks"
                ],
                notes=f"Engagement score: {state.engagement_score:.2f}"
            )
        return None

    # ========================================================================
    # MEDIUM PRIORITY RULES
    # ========================================================================

    def _rule_medium_churn_risk(self, state: TutorState) -> Optional[InterventionTrigger]:
        """
        MEDIUM: Tutor has medium churn risk (30-50% probability).

        Action: Peer mentoring.
        """
        if state.risk_level == RiskLevel.MEDIUM.value:
            return InterventionTrigger(
                intervention_type=InterventionType.PEER_MENTORING,
                priority=InterventionPriority.MEDIUM,
                trigger_reason=f"Medium churn risk detected (probability: {state.churn_probability:.1%})",
                requires_immediate_action=False,
                due_days=10,
                requires_human=True,
                assigned_to="peer_mentor_coordinator",
                recommended_actions=[
                    "Match tutor with experienced peer mentor",
                    "Facilitate introduction and initial meeting",
                    "Set up regular mentor check-ins",
                    "Provide mentoring conversation guides",
                    "Monitor mentorship relationship progress"
                ],
                notes=f"Churn score: {state.churn_score}/100. Preventive support to reduce risk."
            )
        return None

    def _rule_declining_ratings(self, state: TutorState) -> Optional[InterventionTrigger]:
        """
        MEDIUM: Ratings declining but not yet critical.

        Action: Automated coaching tips.
        """
        if (state.rating_decline is not None and
            0.3 <= state.rating_decline <= 0.5 and  # Moderate decline
            state.avg_rating and state.avg_rating < 4.0):
            return InterventionTrigger(
                intervention_type=InterventionType.AUTOMATED_COACHING,
                priority=InterventionPriority.MEDIUM,
                trigger_reason=f"Declining ratings detected (trend: -{state.rating_decline:.2f})",
                requires_immediate_action=False,
                due_days=5,
                requires_human=False,
                assigned_to=None,
                recommended_actions=[
                    "Send automated coaching email with tips",
                    "Highlight areas for improvement based on feedback",
                    "Provide resources for common student concerns",
                    "Suggest self-reflection exercises",
                    "Encourage seeking peer or manager support"
                ],
                notes=f"Current avg rating: {state.avg_rating:.2f}, Decline: {state.rating_decline:.2f}"
            )
        return None

    def _rule_declining_session_volume(self, state: TutorState) -> Optional[InterventionTrigger]:
        """
        MEDIUM: Session volume declining significantly.

        Action: Automated check-in and resource sharing.
        """
        if (state.session_volume_decline is not None and
            state.session_volume_decline > 0.3):  # >30% decline
            return InterventionTrigger(
                intervention_type=InterventionType.AUTOMATED_COACHING,
                priority=InterventionPriority.MEDIUM,
                trigger_reason=f"Session volume declining ({state.session_volume_decline:.1%} decrease)",
                requires_immediate_action=False,
                due_days=7,
                requires_human=False,
                assigned_to=None,
                recommended_actions=[
                    "Send check-in email about availability",
                    "Share tips for managing scheduling",
                    "Highlight benefits of consistent session volume",
                    "Offer support resources if needed",
                    "Monitor for continued decline"
                ],
                notes=f"Sessions per week: {state.sessions_per_week:.1f}, Decline: {state.session_volume_decline:.1%}"
            )
        return None

    def _rule_new_tutor_support(self, state: TutorState) -> Optional[InterventionTrigger]:
        """
        MEDIUM: New tutor (< 30 days) with suboptimal early performance.

        Action: Additional onboarding support.
        """
        if (state.tenure_days < 30 and
            state.tenure_days >= 7 and  # After first week
            state.avg_rating and state.avg_rating < 4.2):
            return InterventionTrigger(
                intervention_type=InterventionType.TRAINING_MODULE,
                priority=InterventionPriority.MEDIUM,
                trigger_reason="New tutor showing early performance challenges",
                requires_immediate_action=False,
                due_days=5,
                requires_human=False,
                assigned_to=None,
                recommended_actions=[
                    "Assign advanced onboarding modules",
                    "Provide additional new tutor resources",
                    "Schedule optional Q&A session",
                    "Connect with new tutor support group",
                    "Plan 30-day check-in"
                ],
                notes=f"Tenure: {state.tenure_days} days, Avg rating: {state.avg_rating:.2f}"
            )
        return None

    # ========================================================================
    # LOW PRIORITY RULES (POSITIVE)
    # ========================================================================

    def _rule_recognition_high_performer(self, state: TutorState) -> Optional[InterventionTrigger]:
        """
        LOW: Consistently high performance.

        Action: Recognition and appreciation.
        """
        if (state.performance_tier in [PerformanceTier.EXEMPLARY.value, PerformanceTier.STRONG.value] and
            state.avg_rating and state.avg_rating >= 4.5 and
            state.engagement_score and state.engagement_score >= 0.8):
            return InterventionTrigger(
                intervention_type=InterventionType.RECOGNITION,
                priority=InterventionPriority.LOW,
                trigger_reason="Exemplary performance merits recognition",
                requires_immediate_action=False,
                due_days=7,
                requires_human=False,
                assigned_to=None,
                recommended_actions=[
                    "Send recognition email highlighting achievements",
                    "Feature tutor in internal newsletter or spotlight",
                    "Consider for peer mentoring opportunities",
                    "Acknowledge contributions in team meetings",
                    "Explore career development opportunities"
                ],
                notes=f"Performance tier: {state.performance_tier}, Avg rating: {state.avg_rating:.2f}, Engagement: {state.engagement_score:.2f}"
            )
        return None

    def _rule_recognition_improvement(self, state: TutorState) -> Optional[InterventionTrigger]:
        """
        LOW: Significant improvement in performance.

        Action: Recognition of growth.
        """
        # Check for positive trends (negative decline = improvement)
        improved_rating = state.rating_decline is not None and state.rating_decline < -0.3
        improved_engagement = state.engagement_decline is not None and state.engagement_decline < -0.15

        if improved_rating or improved_engagement:
            return InterventionTrigger(
                intervention_type=InterventionType.RECOGNITION,
                priority=InterventionPriority.LOW,
                trigger_reason="Significant performance improvement detected",
                requires_immediate_action=False,
                due_days=7,
                requires_human=False,
                assigned_to=None,
                recommended_actions=[
                    "Send congratulations email on improvement",
                    "Acknowledge specific areas of growth",
                    "Encourage continued progress",
                    "Share success as example for others",
                    "Consider for leadership opportunities"
                ],
                notes=f"Rating trend: {state.rating_decline:.2f}, Engagement trend: {state.engagement_decline:.2f}"
            )
        return None


# ============================================================================
# INTERVENTION FRAMEWORK
# ============================================================================

class InterventionFramework:
    """
    Main interface for the intervention system.

    Coordinates rule evaluation, intervention creation, and integration
    with notification and task management systems.
    """

    def __init__(self, config: Optional[InterventionConfig] = None):
        """
        Initialize the intervention framework.

        Args:
            config: Configuration object. If None, uses default configuration.
        """
        self.config = config or get_default_config()
        self.rule_engine = InterventionRuleEngine(self.config)
        logger.info("InterventionFramework initialized")

    def evaluate_tutor_for_interventions(
        self,
        tutor_state: TutorState
    ) -> List[InterventionTrigger]:
        """
        Evaluate a tutor and return recommended interventions.

        Args:
            tutor_state: Current tutor state with metrics and predictions

        Returns:
            List of intervention triggers, sorted by priority
        """
        return self.rule_engine.evaluate_tutor(tutor_state)

    def format_intervention_summary(
        self,
        tutor_state: TutorState,
        triggers: List[InterventionTrigger]
    ) -> str:
        """
        Format intervention summary for logging/display.

        Args:
            tutor_state: Tutor state that was evaluated
            triggers: List of triggered interventions

        Returns:
            Formatted string summary
        """
        if not triggers:
            return f"No interventions triggered for tutor {tutor_state.tutor_id}"

        summary = [
            f"Intervention Summary for {tutor_state.tutor_name} ({tutor_state.tutor_id})",
            f"Churn Risk: {tutor_state.risk_level} (Score: {tutor_state.churn_score}/100)",
            f"Performance Tier: {tutor_state.performance_tier}",
            f"\nTriggered Interventions ({len(triggers)}):",
            "=" * 70
        ]

        for i, trigger in enumerate(triggers, 1):
            summary.extend([
                f"\n{i}. {trigger.intervention_type.value.upper()}",
                f"   Priority: {trigger.priority.value.upper()}",
                f"   Reason: {trigger.trigger_reason}",
                f"   Human Required: {'Yes' if trigger.requires_human else 'No'}",
                f"   Assigned To: {trigger.assigned_to or 'Automated'}",
                f"   Due: {trigger.due_days} days",
                f"   Actions:",
            ])
            for action in trigger.recommended_actions:
                summary.append(f"     - {action}")

        return "\n".join(summary)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_tutor_state_from_prediction(
    tutor_data: dict,
    churn_prediction: dict,
    performance_metrics: dict,
    recent_interventions: List[str] = None
) -> TutorState:
    """
    Create a TutorState object from prediction and metric data.

    Args:
        tutor_data: Basic tutor information (id, name, tenure)
        churn_prediction: Churn prediction data (probability, score, risk_level)
        performance_metrics: Performance metrics (ratings, engagement, etc.)
        recent_interventions: List of recent intervention types

    Returns:
        TutorState object ready for rule evaluation
    """
    return TutorState(
        tutor_id=tutor_data['tutor_id'],
        tutor_name=tutor_data.get('tutor_name', 'Unknown'),

        # Churn prediction
        churn_probability=churn_prediction['churn_probability'],
        churn_score=churn_prediction['churn_score'],
        risk_level=churn_prediction['risk_level'],

        # Performance metrics
        avg_rating=performance_metrics.get('avg_rating'),
        first_session_success_rate=performance_metrics.get('first_session_success_rate'),
        engagement_score=performance_metrics.get('engagement_score'),
        learning_objectives_met_pct=performance_metrics.get('learning_objectives_met_pct'),
        performance_tier=performance_metrics.get('performance_tier'),

        # Behavioral indicators
        no_show_rate=performance_metrics.get('no_show_rate', 0.0),
        reschedule_rate=performance_metrics.get('reschedule_rate', 0.0),
        sessions_completed=performance_metrics.get('sessions_completed', 0),
        sessions_per_week=performance_metrics.get('sessions_per_week', 0.0),

        # Trends
        engagement_decline=performance_metrics.get('engagement_decline'),
        rating_decline=performance_metrics.get('rating_decline'),
        session_volume_decline=performance_metrics.get('session_volume_decline'),

        # Composite
        behavioral_risk_score=performance_metrics.get('behavioral_risk_score'),

        # History
        recent_interventions=recent_interventions or [],
        tenure_days=tutor_data.get('tenure_days', 0)
    )


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Evaluate a high-risk tutor
    framework = InterventionFramework()

    # Create sample tutor state
    sample_state = TutorState(
        tutor_id="T001",
        tutor_name="John Doe",
        churn_probability=0.72,
        churn_score=85,
        risk_level=RiskLevel.CRITICAL.value,
        avg_rating=3.5,
        first_session_success_rate=0.45,
        engagement_score=0.55,
        performance_tier=PerformanceTier.AT_RISK.value,
        no_show_rate=0.05,
        reschedule_rate=0.25,
        sessions_completed=20,
        sessions_per_week=3.5,
        engagement_decline=0.25,
        rating_decline=0.6,
        session_volume_decline=0.35,
        behavioral_risk_score=0.68,
        recent_interventions=[],
        tenure_days=120
    )

    # Evaluate
    triggers = framework.evaluate_tutor_for_interventions(sample_state)

    # Display results
    summary = framework.format_intervention_summary(sample_state, triggers)
    print(summary)
