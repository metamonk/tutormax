"""
Configuration for background workers.

This module provides worker-specific configuration settings that extend
the main application configuration.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class WorkerSettings(BaseSettings):
    """
    Worker-specific configuration settings.
    """

    # Data generation settings
    data_gen_enabled: bool = True
    data_gen_interval_seconds: int = 60  # Generate data every minute
    data_gen_batch_size: int = 10  # Generate 10 sessions at a time

    # Performance evaluation settings
    perf_eval_lookback_minutes: int = 15  # Evaluate last 15 minutes
    perf_eval_batch_size: int = 100  # Process 100 tutors at a time

    # Churn prediction settings
    churn_prediction_threshold: float = 0.5  # Probability threshold
    churn_prediction_lookback_days: int = 30  # Look back 30 days
    churn_batch_size: int = 100  # Process 100 tutors at a time

    # Model training settings
    model_training_min_samples: int = 100  # Minimum samples for training
    model_training_test_split: float = 0.2  # 20% test set
    model_save_path: str = "output/models"

    # Retry settings
    max_task_retries: int = 3
    retry_backoff: int = 60  # seconds
    retry_backoff_max: int = 600  # 10 minutes

    # Monitoring settings
    enable_task_monitoring: bool = True
    log_task_execution: bool = True

    class Config:
        env_prefix = "WORKER_"
        env_file = ".env"
        case_sensitive = False


# Global worker settings instance
worker_settings = WorkerSettings()
