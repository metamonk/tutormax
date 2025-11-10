"""
Unit tests for the Intervention Rule Engine

Tests the rule engine logic, configuration system, and intervention triggers.
"""

import pytest
from datetime import datetime, timedelta
from src.evaluation.intervention_framework import (
    InterventionRuleEngine,
    InterventionFramework,
    TutorState,
    InterventionTrigger,
    InterventionType,
    InterventionPriority,
    RiskLevel,
    PerformanceTier,
)
from src.evaluation.intervention_config import (
    InterventionConfig,
    RuleThresholds,
    InterventionTiming,
    RuleEnablement,
    ConfigManager,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def default_config():
    """Provide default configuration."""
    return InterventionConfig()


@pytest.fixture
def custom_config():
    """Provide custom configuration with modified thresholds."""
    config = InterventionConfig()
    config.thresholds.critical_churn_probability = 0.80
    config.thresholds.high_churn_probability = 0.60
    config.thresholds.poor_first_session_rate = 0.50
    return config


@pytest.fixture
def rule_engine(default_config):
    """Provide a rule engine instance with default configuration."""
    return InterventionRuleEngine(default_config)


@pytest.fixture
def custom_rule_engine(custom_config):
    """Provide a rule engine instance with custom configuration."""
    return InterventionRuleEngine(custom_config)


@pytest.fixture
def baseline_tutor_state():
    """Provide a baseline tutor state with normal metrics."""
    return TutorState(
        tutor_id="T001",
        tutor_name="Test Tutor",
        churn_probability=0.25,
        churn_score=25,
        risk_level=RiskLevel.LOW.value,
        avg_rating=4.3,
        first_session_success_rate=0.75,
        engagement_score=0.72,
        learning_objectives_met_pct=0.68,
        performance_tier=PerformanceTier.STRONG.value,
        no_show_rate=0.03,
        reschedule_rate=0.08,
        sessions_completed=25,
        sessions_per_week=5.0,
        engagement_decline=0.0,
        rating_decline=0.0,
        session_volume_decline=0.0,
        behavioral_risk_score=0.15,
        recent_interventions=[],
        last_intervention_date=None,
        tenure_days=90,
    )


@pytest.fixture
def critical_risk_tutor_state():
    """Provide a tutor state with critical churn risk."""
    return TutorState(
        tutor_id="T002",
        tutor_name="Critical Risk Tutor",
        churn_probability=0.75,
        churn_score=85,
        risk_level=RiskLevel.CRITICAL.value,
        avg_rating=3.2,
        first_session_success_rate=0.45,
        engagement_score=0.50,
        learning_objectives_met_pct=0.48,
        performance_tier=PerformanceTier.AT_RISK.value,
        no_show_rate=0.08,
        reschedule_rate=0.25,
        sessions_completed=20,
        sessions_per_week=3.0,
        engagement_decline=0.30,
        rating_decline=0.65,
        session_volume_decline=0.40,
        behavioral_risk_score=0.72,
        recent_interventions=[],
        last_intervention_date=None,
        tenure_days=120,
    )


# =============================================================================
# CONFIGURATION TESTS
# =============================================================================

class TestInterventionConfig:
    """Test configuration system."""

    def test_default_config_creation(self):
        """Test that default configuration is created properly."""
        config = InterventionConfig()
        assert config.thresholds.critical_churn_probability == 0.70
        assert config.thresholds.high_churn_probability == 0.50
        assert config.timing.intervention_cooldown_days == 14
        assert config.enable_automated_interventions is True

    def test_config_to_dict(self):
        """Test configuration serialization to dictionary."""
        config = InterventionConfig()
        config_dict = config.to_dict()

        assert 'thresholds' in config_dict
        assert 'timing' in config_dict
        assert 'enablement' in config_dict
        assert config_dict['enable_automated_interventions'] is True

    def test_config_from_dict(self):
        """Test configuration deserialization from dictionary."""
        data = {
            'thresholds': {'critical_churn_probability': 0.80},
            'timing': {'intervention_cooldown_days': 21},
            'enablement': {'critical_churn_risk': False},
            'enable_automated_interventions': False,
        }
        config = InterventionConfig.from_dict(data)

        assert config.thresholds.critical_churn_probability == 0.80
        assert config.timing.intervention_cooldown_days == 21
        assert config.enablement.critical_churn_risk is False
        assert config.enable_automated_interventions is False

    def test_rule_enablement(self):
        """Test rule enablement checking."""
        enablement = RuleEnablement()
        assert enablement.is_enabled('critical_churn_risk') is True

        enablement.critical_churn_risk = False
        assert enablement.is_enabled('critical_churn_risk') is False

    def test_config_manager(self, tmp_path):
        """Test configuration manager."""
        config_file = tmp_path / "test_config.json"

        # Create and save config
        manager = ConfigManager(config_path=config_file)
        manager.update_thresholds(critical_churn_probability=0.85)
        manager.save_config()

        # Load config
        manager2 = ConfigManager(config_path=config_file)
        assert manager2.config.thresholds.critical_churn_probability == 0.85


# =============================================================================
# RULE ENGINE INITIALIZATION TESTS
# =============================================================================

class TestRuleEngineInitialization:
    """Test rule engine initialization and configuration."""

    def test_rule_engine_creation(self, rule_engine):
        """Test that rule engine is created properly."""
        assert rule_engine is not None
        assert rule_engine.config is not None
        assert len(rule_engine.rules) > 0

    def test_rule_engine_with_custom_config(self, custom_rule_engine):
        """Test rule engine with custom configuration."""
        assert custom_rule_engine.config.thresholds.critical_churn_probability == 0.80
        assert custom_rule_engine.config.thresholds.high_churn_probability == 0.60

    def test_all_rules_initialized(self, rule_engine):
        """Test that all expected rules are initialized."""
        expected_rules = [
            'critical_churn_risk',
            'severe_performance_decline',
            'high_churn_risk',
            'poor_first_session_performance',
            'excessive_rescheduling',
            'low_engagement_pattern',
            'medium_churn_risk',
            'declining_ratings',
            'declining_session_volume',
            'new_tutor_support',
            'recognition_high_performer',
            'recognition_improvement',
        ]

        for rule_name in expected_rules:
            assert rule_name in rule_engine.rules


# =============================================================================
# INPUT VALIDATION TESTS
# =============================================================================

class TestInputValidation:
    """Test input validation logic."""

    def test_valid_tutor_state(self, rule_engine, baseline_tutor_state):
        """Test validation of valid tutor state."""
        assert rule_engine._validate_tutor_state(baseline_tutor_state) is True

    def test_missing_tutor_id(self, rule_engine):
        """Test validation fails with missing tutor_id."""
        state = TutorState(
            tutor_id="",
            tutor_name="Test",
            churn_probability=0.5,
            churn_score=50,
            risk_level=RiskLevel.MEDIUM.value,
        )
        assert rule_engine._validate_tutor_state(state) is False

    def test_invalid_churn_probability(self, rule_engine):
        """Test validation fails with invalid churn probability."""
        state = TutorState(
            tutor_id="T001",
            tutor_name="Test",
            churn_probability=1.5,  # Invalid: > 1.0
            churn_score=50,
            risk_level=RiskLevel.MEDIUM.value,
        )
        assert rule_engine._validate_tutor_state(state) is False

    def test_invalid_churn_score(self, rule_engine):
        """Test validation fails with invalid churn score."""
        state = TutorState(
            tutor_id="T001",
            tutor_name="Test",
            churn_probability=0.5,
            churn_score=150,  # Invalid: > 100
            risk_level=RiskLevel.MEDIUM.value,
        )
        assert rule_engine._validate_tutor_state(state) is False


# =============================================================================
# INDIVIDUAL RULE TESTS
# =============================================================================

class TestCriticalPriorityRules:
    """Test critical priority rules."""

    def test_critical_churn_risk_trigger(self, rule_engine, critical_risk_tutor_state):
        """Test that critical churn risk triggers retention interview."""
        trigger = rule_engine._rule_critical_churn_risk(critical_risk_tutor_state)

        assert trigger is not None
        assert trigger.intervention_type == InterventionType.RETENTION_INTERVIEW
        assert trigger.priority == InterventionPriority.CRITICAL
        assert trigger.requires_human is True
        assert trigger.requires_immediate_action is True

    def test_critical_churn_risk_no_trigger(self, rule_engine, baseline_tutor_state):
        """Test that normal risk doesn't trigger critical intervention."""
        trigger = rule_engine._rule_critical_churn_risk(baseline_tutor_state)
        assert trigger is None

    def test_critical_churn_custom_threshold(self, custom_rule_engine):
        """Test critical churn risk with custom threshold."""
        # Custom threshold is 0.80, so 0.75 should not trigger
        state = TutorState(
            tutor_id="T001",
            tutor_name="Test",
            churn_probability=0.75,
            churn_score=75,
            risk_level=RiskLevel.HIGH.value,
            sessions_completed=10,
        )

        trigger = custom_rule_engine._rule_critical_churn_risk(state)
        assert trigger is None

        # But 0.85 should trigger
        state.churn_probability = 0.85
        trigger = custom_rule_engine._rule_critical_churn_risk(state)
        assert trigger is not None

    def test_severe_performance_decline_trigger(self, rule_engine):
        """Test severe performance decline trigger."""
        state = TutorState(
            tutor_id="T001",
            tutor_name="Test",
            churn_probability=0.5,
            churn_score=50,
            risk_level=RiskLevel.MEDIUM.value,
            performance_tier=PerformanceTier.AT_RISK.value,
            rating_decline=0.6,  # Severe
            engagement_decline=0.25,  # Severe
            sessions_completed=15,
        )

        trigger = rule_engine._rule_severe_performance_decline(state)

        assert trigger is not None
        assert trigger.intervention_type == InterventionType.PERFORMANCE_IMPROVEMENT_PLAN
        assert trigger.priority == InterventionPriority.CRITICAL


class TestHighPriorityRules:
    """Test high priority rules."""

    def test_high_churn_risk_trigger(self, rule_engine):
        """Test high churn risk triggers manager coaching."""
        state = TutorState(
            tutor_id="T001",
            tutor_name="Test",
            churn_probability=0.55,  # Between high (0.5) and critical (0.7)
            churn_score=60,
            risk_level=RiskLevel.HIGH.value,
            sessions_completed=10,
        )

        trigger = rule_engine._rule_high_churn_risk(state)

        assert trigger is not None
        assert trigger.intervention_type == InterventionType.MANAGER_COACHING
        assert trigger.priority == InterventionPriority.HIGH
        assert trigger.requires_human is True

    def test_poor_first_session_performance_trigger(self, rule_engine):
        """Test poor first session performance triggers intervention."""
        state = TutorState(
            tutor_id="T001",
            tutor_name="Test",
            churn_probability=0.3,
            churn_score=30,
            risk_level=RiskLevel.MEDIUM.value,
            first_session_success_rate=0.45,  # Below 0.60 threshold
            sessions_completed=10,
        )

        trigger = rule_engine._rule_poor_first_session_performance(state)

        assert trigger is not None
        assert trigger.intervention_type == InterventionType.FIRST_SESSION_CHECKIN
        assert trigger.priority == InterventionPriority.HIGH

    def test_excessive_rescheduling_trigger(self, rule_engine):
        """Test excessive rescheduling triggers alert."""
        state = TutorState(
            tutor_id="T001",
            tutor_name="Test",
            churn_probability=0.3,
            churn_score=30,
            risk_level=RiskLevel.MEDIUM.value,
            reschedule_rate=0.25,  # Above 0.20 threshold
            sessions_completed=10,
        )

        trigger = rule_engine._rule_excessive_rescheduling(state)

        assert trigger is not None
        assert trigger.intervention_type == InterventionType.RESCHEDULING_ALERT
        assert trigger.priority == InterventionPriority.HIGH
        assert trigger.requires_human is False  # Can be automated

    def test_low_engagement_pattern_trigger(self, rule_engine):
        """Test low engagement triggers training module."""
        state = TutorState(
            tutor_id="T001",
            tutor_name="Test",
            churn_probability=0.3,
            churn_score=30,
            risk_level=RiskLevel.MEDIUM.value,
            engagement_score=0.45,  # Below 0.60 threshold
            sessions_completed=10,
        )

        trigger = rule_engine._rule_low_engagement_pattern(state)

        assert trigger is not None
        assert trigger.intervention_type == InterventionType.TRAINING_MODULE
        assert trigger.priority == InterventionPriority.HIGH


class TestPositiveRecognitionRules:
    """Test positive recognition rules."""

    def test_recognition_high_performer(self, rule_engine):
        """Test recognition for high performers."""
        state = TutorState(
            tutor_id="T001",
            tutor_name="Test",
            churn_probability=0.1,
            churn_score=10,
            risk_level=RiskLevel.LOW.value,
            performance_tier=PerformanceTier.EXEMPLARY.value,
            avg_rating=4.8,
            engagement_score=0.85,
            sessions_completed=50,
        )

        trigger = rule_engine._rule_recognition_high_performer(state)

        assert trigger is not None
        assert trigger.intervention_type == InterventionType.RECOGNITION
        assert trigger.priority == InterventionPriority.LOW
        assert trigger.requires_human is False

    def test_recognition_improvement(self, rule_engine):
        """Test recognition for significant improvement."""
        state = TutorState(
            tutor_id="T001",
            tutor_name="Test",
            churn_probability=0.3,
            churn_score=30,
            risk_level=RiskLevel.MEDIUM.value,
            rating_decline=-0.35,  # Negative = improvement
            engagement_decline=-0.20,  # Negative = improvement
            sessions_completed=20,
        )

        trigger = rule_engine._rule_recognition_improvement(state)

        assert trigger is not None
        assert trigger.intervention_type == InterventionType.RECOGNITION


# =============================================================================
# COOLDOWN TESTS
# =============================================================================

class TestCooldownLogic:
    """Test intervention cooldown logic."""

    def test_no_cooldown_first_intervention(self, rule_engine, baseline_tutor_state):
        """Test that first intervention has no cooldown."""
        trigger = InterventionTrigger(
            intervention_type=InterventionType.AUTOMATED_COACHING,
            priority=InterventionPriority.MEDIUM,
            trigger_reason="Test",
        )

        assert rule_engine._check_cooldown(baseline_tutor_state, trigger) is True

    def test_cooldown_same_intervention_type(self, rule_engine):
        """Test cooldown for same intervention type."""
        state = TutorState(
            tutor_id="T001",
            tutor_name="Test",
            churn_probability=0.3,
            churn_score=30,
            risk_level=RiskLevel.MEDIUM.value,
            sessions_completed=10,
            recent_interventions=[InterventionType.AUTOMATED_COACHING.value],
            last_intervention_date=datetime.now() - timedelta(days=5),  # 5 days ago
        )

        trigger = InterventionTrigger(
            intervention_type=InterventionType.AUTOMATED_COACHING,
            priority=InterventionPriority.MEDIUM,
            trigger_reason="Test",
        )

        # Should be in cooldown (default: 7 days)
        assert rule_engine._check_cooldown(state, trigger) is False

    def test_cooldown_expired(self, rule_engine):
        """Test cooldown expires after configured period."""
        state = TutorState(
            tutor_id="T001",
            tutor_name="Test",
            churn_probability=0.3,
            churn_score=30,
            risk_level=RiskLevel.MEDIUM.value,
            sessions_completed=10,
            recent_interventions=[InterventionType.AUTOMATED_COACHING.value],
            last_intervention_date=datetime.now() - timedelta(days=10),  # 10 days ago
        )

        trigger = InterventionTrigger(
            intervention_type=InterventionType.AUTOMATED_COACHING,
            priority=InterventionPriority.MEDIUM,
            trigger_reason="Test",
        )

        # Should not be in cooldown (> 7 days)
        assert rule_engine._check_cooldown(state, trigger) is True


# =============================================================================
# FULL EVALUATION TESTS
# =============================================================================

class TestFullEvaluation:
    """Test full tutor evaluation process."""

    def test_evaluate_baseline_tutor(self, rule_engine, baseline_tutor_state):
        """Test evaluation of baseline tutor with normal metrics."""
        triggers = rule_engine.evaluate_tutor(baseline_tutor_state)

        # Baseline tutor should trigger no or few interventions
        assert isinstance(triggers, list)
        assert len(triggers) <= 2  # Might get recognition

    def test_evaluate_critical_risk_tutor(self, rule_engine, critical_risk_tutor_state):
        """Test evaluation of critical risk tutor."""
        triggers = rule_engine.evaluate_tutor(critical_risk_tutor_state)

        assert len(triggers) > 0
        # Should have critical priority intervention
        assert any(t.priority == InterventionPriority.CRITICAL for t in triggers)
        # Should have retention interview
        assert any(t.intervention_type == InterventionType.RETENTION_INTERVIEW for t in triggers)

    def test_evaluate_insufficient_sessions(self, rule_engine):
        """Test evaluation skips tutors with insufficient sessions."""
        state = TutorState(
            tutor_id="T001",
            tutor_name="Test",
            churn_probability=0.8,  # High risk
            churn_score=80,
            risk_level=RiskLevel.CRITICAL.value,
            sessions_completed=2,  # Below minimum
        )

        triggers = rule_engine.evaluate_tutor(state)
        assert len(triggers) == 0

    def test_evaluate_triggers_sorted_by_priority(self, rule_engine, critical_risk_tutor_state):
        """Test that triggers are sorted by priority."""
        triggers = rule_engine.evaluate_tutor(critical_risk_tutor_state)

        if len(triggers) > 1:
            # Check that critical/high are before medium/low
            priority_values = [t.priority for t in triggers]
            assert priority_values == sorted(
                priority_values,
                key=lambda p: {
                    InterventionPriority.CRITICAL: 0,
                    InterventionPriority.HIGH: 1,
                    InterventionPriority.MEDIUM: 2,
                    InterventionPriority.LOW: 3,
                }[p]
            )

    def test_evaluate_max_interventions_limit(self, rule_engine):
        """Test that evaluation respects max interventions limit."""
        # Create state that would trigger many interventions
        state = TutorState(
            tutor_id="T001",
            tutor_name="Test",
            churn_probability=0.75,
            churn_score=85,
            risk_level=RiskLevel.CRITICAL.value,
            avg_rating=3.0,
            first_session_success_rate=0.40,
            engagement_score=0.45,
            performance_tier=PerformanceTier.AT_RISK.value,
            reschedule_rate=0.30,
            no_show_rate=0.15,
            sessions_completed=20,
            rating_decline=0.70,
            engagement_decline=0.30,
            session_volume_decline=0.40,
        )

        triggers = rule_engine.evaluate_tutor(state)

        # Should not exceed max_interventions_per_tutor (default: 5)
        assert len(triggers) <= rule_engine.config.max_interventions_per_tutor


# =============================================================================
# RULE ENABLEMENT TESTS
# =============================================================================

class TestRuleEnablement:
    """Test rule enablement configuration."""

    def test_disabled_rule_not_evaluated(self, default_config):
        """Test that disabled rules are not evaluated."""
        # Disable critical churn risk rule
        default_config.enablement.critical_churn_risk = False

        engine = InterventionRuleEngine(default_config)

        state = TutorState(
            tutor_id="T001",
            tutor_name="Test",
            churn_probability=0.80,  # Would trigger if enabled
            churn_score=85,
            risk_level=RiskLevel.CRITICAL.value,
            sessions_completed=10,
        )

        triggers = engine.evaluate_tutor(state)

        # Should not have retention interview trigger
        assert not any(t.intervention_type == InterventionType.RETENTION_INTERVIEW for t in triggers)

    def test_disable_automated_interventions(self, default_config):
        """Test disabling all automated interventions."""
        default_config.enable_automated_interventions = False

        engine = InterventionRuleEngine(default_config)

        state = TutorState(
            tutor_id="T001",
            tutor_name="Test",
            churn_probability=0.3,
            churn_score=30,
            risk_level=RiskLevel.MEDIUM.value,
            engagement_score=0.50,  # Would trigger automated training
            sessions_completed=10,
        )

        triggers = engine.evaluate_tutor(state)

        # Should not have any automated interventions
        assert all(t.requires_human for t in triggers)


# =============================================================================
# FRAMEWORK INTEGRATION TESTS
# =============================================================================

class TestInterventionFramework:
    """Test the full intervention framework."""

    def test_framework_initialization(self):
        """Test framework initialization."""
        framework = InterventionFramework()
        assert framework is not None
        assert framework.rule_engine is not None

    def test_framework_evaluation(self, baseline_tutor_state):
        """Test framework evaluation."""
        framework = InterventionFramework()
        triggers = framework.evaluate_tutor_for_interventions(baseline_tutor_state)

        assert isinstance(triggers, list)

    def test_framework_summary_formatting(self, critical_risk_tutor_state):
        """Test intervention summary formatting."""
        framework = InterventionFramework()
        triggers = framework.evaluate_tutor_for_interventions(critical_risk_tutor_state)

        summary = framework.format_intervention_summary(critical_risk_tutor_state, triggers)

        assert isinstance(summary, str)
        assert critical_risk_tutor_state.tutor_name in summary
        assert "Intervention Summary" in summary

    def test_framework_with_custom_config(self, custom_config):
        """Test framework with custom configuration."""
        framework = InterventionFramework(custom_config)
        assert framework.config == custom_config
        assert framework.rule_engine.config == custom_config
