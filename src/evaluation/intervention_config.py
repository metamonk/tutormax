"""
Intervention Rule Engine Configuration

This module provides configuration management for the intervention rule engine,
allowing dynamic adjustment of thresholds, cooldowns, and rule enablement.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
import json
from pathlib import Path


@dataclass
class RuleThresholds:
    """Configurable thresholds for intervention rules."""

    # Churn risk thresholds
    critical_churn_probability: float = 0.70
    high_churn_probability: float = 0.50
    medium_churn_probability: float = 0.30

    # Performance thresholds
    poor_first_session_rate: float = 0.60
    low_engagement_score: float = 0.60
    low_rating: float = 4.0
    new_tutor_rating_threshold: float = 4.2

    # High performance thresholds
    high_performer_rating: float = 4.5
    high_performer_engagement: float = 0.8

    # Behavioral thresholds
    excessive_reschedule_rate: float = 0.20
    excessive_no_show_rate: float = 0.15

    # Decline thresholds
    rating_decline_moderate: float = 0.30  # Lower bound
    rating_decline_severe: float = 0.50    # Upper bound
    engagement_decline_moderate: float = 0.15
    engagement_decline_severe: float = 0.20
    session_volume_decline: float = 0.30

    # Improvement thresholds (negative decline = improvement)
    rating_improvement: float = -0.30
    engagement_improvement: float = -0.15

    # Minimum data requirements
    min_sessions_for_evaluation: int = 3
    new_tutor_days: int = 30
    new_tutor_min_days: int = 7

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RuleThresholds':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class InterventionTiming:
    """Configurable timing parameters for interventions."""

    # Cooldown periods (days)
    intervention_cooldown_days: int = 14
    same_type_cooldown_days: int = 7

    # Due dates by priority (days)
    critical_due_days: int = 2
    high_due_days: int = 5
    medium_due_days: int = 7
    low_due_days: int = 14

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InterventionTiming':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class RuleEnablement:
    """Controls which rules are enabled/disabled."""

    # Critical rules
    critical_churn_risk: bool = True
    severe_performance_decline: bool = True

    # High priority rules
    high_churn_risk: bool = True
    poor_first_session_performance: bool = True
    excessive_rescheduling: bool = True
    low_engagement_pattern: bool = True

    # Medium priority rules
    medium_churn_risk: bool = True
    declining_ratings: bool = True
    declining_session_volume: bool = True
    new_tutor_support: bool = True

    # Low priority rules (positive)
    recognition_high_performer: bool = True
    recognition_improvement: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RuleEnablement':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def is_enabled(self, rule_name: str) -> bool:
        """Check if a rule is enabled."""
        return getattr(self, rule_name, True)


@dataclass
class InterventionConfig:
    """Complete intervention system configuration."""

    thresholds: RuleThresholds = field(default_factory=RuleThresholds)
    timing: InterventionTiming = field(default_factory=InterventionTiming)
    enablement: RuleEnablement = field(default_factory=RuleEnablement)

    # System settings
    enable_automated_interventions: bool = True
    enable_human_interventions: bool = True
    max_interventions_per_tutor: int = 5
    require_cooldown_check: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'thresholds': self.thresholds.to_dict(),
            'timing': self.timing.to_dict(),
            'enablement': self.enablement.to_dict(),
            'enable_automated_interventions': self.enable_automated_interventions,
            'enable_human_interventions': self.enable_human_interventions,
            'max_interventions_per_tutor': self.max_interventions_per_tutor,
            'require_cooldown_check': self.require_cooldown_check,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InterventionConfig':
        """Create from dictionary."""
        return cls(
            thresholds=RuleThresholds.from_dict(data.get('thresholds', {})),
            timing=InterventionTiming.from_dict(data.get('timing', {})),
            enablement=RuleEnablement.from_dict(data.get('enablement', {})),
            enable_automated_interventions=data.get('enable_automated_interventions', True),
            enable_human_interventions=data.get('enable_human_interventions', True),
            max_interventions_per_tutor=data.get('max_interventions_per_tutor', 5),
            require_cooldown_check=data.get('require_cooldown_check', True),
        )

    def save_to_file(self, filepath: Path) -> None:
        """Save configuration to JSON file."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: Path) -> 'InterventionConfig':
        """Load configuration from JSON file."""
        if not filepath.exists():
            # Return default config if file doesn't exist
            return cls()

        with open(filepath, 'r') as f:
            data = json.load(f)

        return cls.from_dict(data)


class ConfigManager:
    """
    Manages intervention configuration with fallback to defaults.

    Supports loading from:
    1. Custom file path
    2. Environment-specific config (e.g., config/production.json)
    3. Default configuration
    """

    DEFAULT_CONFIG_DIR = Path(__file__).parent.parent.parent / 'config' / 'intervention'

    def __init__(self, config_path: Optional[Path] = None, environment: str = 'default'):
        """
        Initialize configuration manager.

        Args:
            config_path: Custom path to config file
            environment: Environment name (default, development, production, test)
        """
        self.environment = environment

        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = self.DEFAULT_CONFIG_DIR / f'{environment}.json'

        self.config = self._load_config()

    def _load_config(self) -> InterventionConfig:
        """Load configuration from file or use defaults."""
        try:
            return InterventionConfig.load_from_file(self.config_path)
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
            print("Using default configuration.")
            return InterventionConfig()

    def get_config(self) -> InterventionConfig:
        """Get current configuration."""
        return self.config

    def reload(self) -> None:
        """Reload configuration from file."""
        self.config = self._load_config()

    def save_config(self) -> None:
        """Save current configuration to file."""
        self.config.save_to_file(self.config_path)

    def update_thresholds(self, **kwargs) -> None:
        """Update threshold values."""
        for key, value in kwargs.items():
            if hasattr(self.config.thresholds, key):
                setattr(self.config.thresholds, key, value)

    def update_timing(self, **kwargs) -> None:
        """Update timing values."""
        for key, value in kwargs.items():
            if hasattr(self.config.timing, key):
                setattr(self.config.timing, key, value)

    def enable_rule(self, rule_name: str) -> None:
        """Enable a specific rule."""
        if hasattr(self.config.enablement, rule_name):
            setattr(self.config.enablement, rule_name, True)

    def disable_rule(self, rule_name: str) -> None:
        """Disable a specific rule."""
        if hasattr(self.config.enablement, rule_name):
            setattr(self.config.enablement, rule_name, False)


# Default configuration instance
_default_config_manager = None


def get_default_config() -> InterventionConfig:
    """Get the default configuration instance."""
    global _default_config_manager
    if _default_config_manager is None:
        _default_config_manager = ConfigManager()
    return _default_config_manager.get_config()


def set_config_manager(config_manager: ConfigManager) -> None:
    """Set the global configuration manager."""
    global _default_config_manager
    _default_config_manager = config_manager


if __name__ == "__main__":
    # Example: Create and save default configuration
    config = InterventionConfig()
    output_path = Path(__file__).parent.parent.parent / 'config' / 'intervention' / 'default.json'
    config.save_to_file(output_path)
    print(f"Default configuration saved to: {output_path}")

    # Example: Load and modify configuration
    config_mgr = ConfigManager()
    config_mgr.update_thresholds(
        critical_churn_probability=0.75,
        poor_first_session_rate=0.55
    )
    config_mgr.disable_rule('recognition_improvement')
    print("\nModified configuration:")
    print(f"Critical churn threshold: {config_mgr.config.thresholds.critical_churn_probability}")
    print(f"Recognition improvement enabled: {config_mgr.config.enablement.recognition_improvement}")
