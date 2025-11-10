"""
ML Model Trainer Worker - Celery Task for Daily Model Training.

This worker runs daily at 2am (configured in celery_app.py) to:
1. Fetch latest data from PostgreSQL database
2. Prepare data for model training
3. Engineer features for churn prediction
4. Train XGBoost churn prediction model
5. Save trained models with versioning
6. Generate model evaluation reports
7. Track training metrics in Redis

Integrates with:
- src/evaluation/data_preparation.py (data generation logic)
- src/evaluation/feature_engineering.py (feature engineering)
- src/evaluation/model_training.py (model training and evaluation)
- PostgreSQL database for training data
- Redis for caching and status tracking
"""

import logging
import os
import pickle
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pandas as pd
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

# Import Celery app
from ..celery_app import celery_app

# Import database dependencies
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from src.database.database import async_session_maker
from src.database.models import (
    Tutor, Session, StudentFeedback, TutorStatus
)

# Import evaluation modules
from src.evaluation.feature_engineering import ChurnFeatureEngineer
from src.evaluation.model_training import ChurnModelTrainer

# Configure logging
logger = logging.getLogger(__name__)


class ModelTrainerTask(Task):
    """
    Custom Celery task class for model training with retry logic.
    """

    # Retry settings
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 2, "countdown": 300}  # Retry after 5 minutes
    retry_backoff = True
    retry_backoff_max = 600  # Max 10 minutes between retries
    retry_jitter = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log failure details."""
        logger.error(
            f"Model training task {task_id} failed: {exc}",
            exc_info=True,
            extra={
                "task_id": task_id,
                "args": args,
                "kwargs": kwargs,
                "exception": str(exc),
            }
        )

    def on_success(self, retval, task_id, args, kwargs):
        """Log success details."""
        logger.info(
            f"Model training task {task_id} completed successfully",
            extra={
                "task_id": task_id,
                "result": retval,
            }
        )


@celery_app.task(
    bind=True,
    base=ModelTrainerTask,
    name="src.workers.tasks.model_trainer.train_models",
    time_limit=3000,  # 50 minutes hard limit (must match soft limit in config)
    soft_time_limit=2700,  # 45 minutes soft limit
)
def train_models(self, lookback_days: int = 90, output_dir: str = "output/models") -> Dict[str, Any]:
    """
    Train ML models using latest data from database.

    This is the main Celery task that runs daily at 2am.

    Args:
        lookback_days: Number of days of historical data to use for training
        output_dir: Directory to save trained models and reports

    Returns:
        Dictionary containing:
        - success: bool
        - models_trained: list of model names
        - model_version: str (timestamp-based version)
        - metrics: dict of evaluation metrics
        - output_paths: dict of saved file paths
        - error: str (if any error occurred)

    Raises:
        SoftTimeLimitExceeded: If task exceeds time limit
    """
    logger.info("=" * 80)
    logger.info("Starting Daily ML Model Training Task")
    logger.info("=" * 80)
    logger.info(f"Task ID: {self.request.id}")
    logger.info(f"Lookback days: {lookback_days}")
    logger.info(f"Output directory: {output_dir}")

    start_time = datetime.now()
    model_version = start_time.strftime("%Y%m%d_%H%M%S")

    result = {
        "success": False,
        "models_trained": [],
        "model_version": model_version,
        "metrics": {},
        "output_paths": {},
        "start_time": start_time.isoformat(),
        "error": None,
    }

    try:
        # Step 1: Fetch training data from database
        logger.info("\n[Step 1/5] Fetching training data from database...")
        tutors_df, sessions_df, feedback_df = _fetch_training_data(lookback_days)

        if len(tutors_df) == 0:
            error_msg = "No tutor data found in database"
            logger.error(error_msg)
            result["error"] = error_msg
            return result

        logger.info(f"  Tutors: {len(tutors_df):,}")
        logger.info(f"  Sessions: {len(sessions_df):,}")
        logger.info(f"  Feedback: {len(feedback_df):,}")

        # Step 2: Engineer features
        logger.info("\n[Step 2/5] Engineering features...")
        features_df = _engineer_features(tutors_df, sessions_df, feedback_df)

        if len(features_df) == 0:
            error_msg = "Feature engineering produced no features"
            logger.error(error_msg)
            result["error"] = error_msg
            return result

        logger.info(f"  Features created: {len(features_df.columns) - 2}")  # Exclude tutor_id, will_churn
        logger.info(f"  Tutors with features: {len(features_df):,}")

        # Step 3: Train churn prediction model
        logger.info("\n[Step 3/5] Training churn prediction model...")
        model, metrics = _train_churn_model(features_df)

        logger.info(f"  Training complete")
        logger.info(f"  AUC-ROC: {metrics.get('auc_roc', 0):.4f}")
        logger.info(f"  Precision: {metrics.get('precision', 0):.4f}")
        logger.info(f"  Recall: {metrics.get('recall', 0):.4f}")

        # Step 4: Save models and results
        logger.info("\n[Step 4/5] Saving models and evaluation results...")
        output_paths = _save_models_and_results(
            model=model,
            features_df=features_df,
            metrics=metrics,
            model_version=model_version,
            output_dir=output_dir,
        )

        logger.info(f"  Model saved: {output_paths['model']}")
        logger.info(f"  Metrics saved: {output_paths['metrics']}")
        logger.info(f"  Features saved: {output_paths['features']}")

        # Step 5: Update result tracking
        logger.info("\n[Step 5/5] Updating training metadata...")
        _save_training_metadata(
            model_version=model_version,
            metrics=metrics,
            output_paths=output_paths,
            tutors_count=len(tutors_df),
            sessions_count=len(sessions_df),
            features_count=len(features_df.columns) - 2,
        )

        # Update result
        result.update({
            "success": True,
            "models_trained": ["churn_prediction"],
            "metrics": {
                "auc_roc": metrics.get("auc_roc", 0),
                "precision": metrics.get("precision", 0),
                "recall": metrics.get("recall", 0),
                "f1_score": metrics.get("f1_score", 0),
                "accuracy": metrics.get("accuracy", 0),
            },
            "output_paths": output_paths,
            "data_stats": {
                "tutors": len(tutors_df),
                "sessions": len(sessions_df),
                "feedback": len(feedback_df),
                "features": len(features_df.columns) - 2,
            },
        })

        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        result["end_time"] = end_time.isoformat()
        result["elapsed_seconds"] = elapsed

        logger.info("\n" + "=" * 80)
        logger.info("MODEL TRAINING COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"Model version: {model_version}")
        logger.info(f"Total time: {elapsed:.1f} seconds")
        logger.info(f"Models trained: {result['models_trained']}")
        logger.info("=" * 80)

        return result

    except SoftTimeLimitExceeded:
        error_msg = "Model training exceeded time limit"
        logger.error(error_msg)
        result["error"] = error_msg
        result["end_time"] = datetime.now().isoformat()
        raise  # Re-raise to trigger Celery retry

    except Exception as e:
        error_msg = f"Model training failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        result["error"] = error_msg
        result["end_time"] = datetime.now().isoformat()
        raise  # Re-raise to trigger Celery retry


def _fetch_training_data(lookback_days: int) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Fetch training data from PostgreSQL database.

    Args:
        lookback_days: Number of days of historical data to fetch

    Returns:
        Tuple of (tutors_df, sessions_df, feedback_df)
    """
    import asyncio

    async def fetch_data():
        async with async_session_maker() as session:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=lookback_days)

            logger.info(f"  Fetching data from {start_date.date()} to {end_date.date()}")

            # Fetch tutors (active and churned)
            tutors_stmt = select(Tutor).where(
                Tutor.created_at >= start_date
            )
            tutors_result = await session.execute(tutors_stmt)
            tutors = tutors_result.scalars().all()

            # Convert to DataFrame
            tutors_data = []
            for tutor in tutors:
                # Calculate tenure
                tenure_days = (end_date - tutor.onboarding_date).days

                # Determine churn label (tutors with status "churned" in last 30 days)
                will_churn = tutor.status == TutorStatus.CHURNED

                tutors_data.append({
                    "tutor_id": tutor.tutor_id,
                    "name": tutor.name,
                    "email": tutor.email,
                    "onboarding_date": tutor.onboarding_date,
                    "status": tutor.status.value,
                    "subjects": tutor.subjects,
                    "baseline_sessions_per_week": tutor.baseline_sessions_per_week or 5.0,
                    "behavioral_archetype": tutor.behavioral_archetype.value if tutor.behavioral_archetype else None,
                    "tenure_days": tenure_days,
                    "will_churn": will_churn,
                })

            tutors_df = pd.DataFrame(tutors_data)

            # Fetch sessions in date range
            sessions_stmt = select(Session).where(
                and_(
                    Session.scheduled_start >= start_date,
                    Session.scheduled_start <= end_date,
                )
            )
            sessions_result = await session.execute(sessions_stmt)
            sessions = sessions_result.scalars().all()

            # Convert to DataFrame
            sessions_data = []
            for sess in sessions:
                # Determine if this is a first session (session_number == 1)
                is_first = sess.session_number == 1

                sessions_data.append({
                    "session_id": sess.session_id,
                    "tutor_id": sess.tutor_id,
                    "student_id": sess.student_id,
                    "session_number": sess.session_number,
                    "scheduled_start": sess.scheduled_start,
                    "actual_start": sess.actual_start,
                    "duration_minutes": sess.duration_minutes,
                    "subject": sess.subject,
                    "session_type": sess.session_type.value,
                    "tutor_initiated_reschedule": sess.tutor_initiated_reschedule,
                    "no_show": sess.no_show,
                    "late_start_minutes": sess.late_start_minutes,
                    "engagement_score": sess.engagement_score or 0.0,
                    "learning_objectives_met": sess.learning_objectives_met,
                    "technical_issues": sess.technical_issues,
                    "is_first_session": is_first,
                })

            sessions_df = pd.DataFrame(sessions_data)

            # Fetch feedback
            feedback_stmt = select(StudentFeedback).where(
                StudentFeedback.submitted_at >= start_date
            )
            feedback_result = await session.execute(feedback_stmt)
            feedbacks = feedback_result.scalars().all()

            # Convert to DataFrame
            feedback_data = []
            for fb in feedbacks:
                feedback_data.append({
                    "feedback_id": fb.feedback_id,
                    "session_id": fb.session_id,
                    "student_id": fb.student_id,
                    "tutor_id": fb.tutor_id,
                    "overall_rating": fb.overall_rating,
                    "is_first_session": fb.is_first_session,
                    "subject_knowledge_rating": fb.subject_knowledge_rating,
                    "communication_rating": fb.communication_rating,
                    "patience_rating": fb.patience_rating,
                    "engagement_rating": fb.engagement_rating,
                    "helpfulness_rating": fb.helpfulness_rating,
                    "would_recommend": fb.would_recommend,
                    "submitted_at": fb.submitted_at,
                })

            feedback_df = pd.DataFrame(feedback_data)

            return tutors_df, sessions_df, feedback_df

    # Run async function
    return asyncio.run(fetch_data())


def _engineer_features(
    tutors_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    feedback_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Engineer features for churn prediction using existing feature engineering module.

    Args:
        tutors_df: Tutor data
        sessions_df: Session data
        feedback_df: Feedback data

    Returns:
        DataFrame with engineered features
    """
    engineer = ChurnFeatureEngineer()
    features_df = engineer.create_features(tutors_df, sessions_df, feedback_df)
    return features_df


def _train_churn_model(features_df: pd.DataFrame) -> Tuple[Any, Dict[str, Any]]:
    """
    Train churn prediction model using existing model training module.

    Args:
        features_df: Feature matrix with 'will_churn' target

    Returns:
        Tuple of (trained_model, evaluation_metrics)
    """
    # Check if we have the target column
    if "will_churn" not in features_df.columns:
        raise ValueError("Features DataFrame missing 'will_churn' target column")

    # Initialize trainer
    trainer = ChurnModelTrainer(
        test_size=0.2,
        random_state=42,
        cv_folds=5,
    )

    # Prepare data
    X_train, X_test, y_train, y_test = trainer.prepare_data(features_df)

    # Train with hyperparameter tuning
    model = trainer.train_with_hyperparameter_tuning(X_train, y_train)

    # Evaluate
    metrics = trainer.evaluate(X_test, y_test)

    # Get feature importance
    trainer.get_feature_importance(top_n=20)

    return model, trainer.evaluation_results


def _save_models_and_results(
    model: Any,
    features_df: pd.DataFrame,
    metrics: Dict[str, Any],
    model_version: str,
    output_dir: str,
) -> Dict[str, str]:
    """
    Save trained models, features, and evaluation results with versioning.

    Args:
        model: Trained model instance
        features_df: Feature matrix used for training
        metrics: Evaluation metrics
        model_version: Version string (timestamp-based)
        output_dir: Base output directory

    Returns:
        Dictionary of output file paths
    """
    # Create output directory structure
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Versioned subdirectory
    version_dir = output_path / model_version
    version_dir.mkdir(parents=True, exist_ok=True)

    output_paths = {}

    # Save model
    model_file = version_dir / "churn_model.pkl"
    with open(model_file, "wb") as f:
        pickle.dump({
            "model": model,
            "version": model_version,
            "timestamp": datetime.now().isoformat(),
            "feature_names": [c for c in features_df.columns if c not in ["tutor_id", "will_churn"]],
        }, f)
    output_paths["model"] = str(model_file)

    # Also save to "latest" for easy access
    latest_model_file = output_path / "churn_model_latest.pkl"
    with open(latest_model_file, "wb") as f:
        pickle.dump({
            "model": model,
            "version": model_version,
            "timestamp": datetime.now().isoformat(),
            "feature_names": [c for c in features_df.columns if c not in ["tutor_id", "will_churn"]],
        }, f)
    output_paths["model_latest"] = str(latest_model_file)

    # Save evaluation metrics
    metrics_file = version_dir / "evaluation_metrics.json"
    with open(metrics_file, "w") as f:
        # Convert non-serializable objects
        serializable_metrics = _make_json_serializable(metrics)
        json.dump(serializable_metrics, f, indent=2)
    output_paths["metrics"] = str(metrics_file)

    # Save features (sample for inspection)
    features_file = version_dir / "features_sample.csv"
    features_df.head(100).to_csv(features_file, index=False)
    output_paths["features"] = str(features_file)

    return output_paths


def _make_json_serializable(obj: Any) -> Any:
    """Convert objects to JSON-serializable format."""
    import numpy as np

    if isinstance(obj, dict):
        return {k: _make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_json_serializable(v) for v in obj]
    elif isinstance(obj, (np.integer, np.floating)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.DataFrame):
        return obj.to_dict("records")
    elif hasattr(obj, "__dict__"):
        return str(obj)
    else:
        return obj


def _save_training_metadata(
    model_version: str,
    metrics: Dict[str, Any],
    output_paths: Dict[str, str],
    tutors_count: int,
    sessions_count: int,
    features_count: int,
) -> None:
    """
    Save training metadata to output directory for tracking.

    Args:
        model_version: Model version string
        metrics: Evaluation metrics
        output_paths: Dictionary of output file paths
        tutors_count: Number of tutors in training data
        sessions_count: Number of sessions in training data
        features_count: Number of features engineered
    """
    metadata = {
        "model_version": model_version,
        "training_timestamp": datetime.now().isoformat(),
        "data_stats": {
            "tutors": tutors_count,
            "sessions": sessions_count,
            "features": features_count,
        },
        "metrics": {
            "auc_roc": metrics.get("auc_roc", 0),
            "precision": metrics.get("precision", 0),
            "recall": metrics.get("recall", 0),
            "f1_score": metrics.get("f1_score", 0),
            "accuracy": metrics.get("accuracy", 0),
        },
        "output_paths": output_paths,
    }

    # Save to output directory
    output_dir = Path(output_paths.get("model", "output/models")).parent.parent
    metadata_file = output_dir / "training_history.jsonl"

    # Append to training history (JSONL format)
    with open(metadata_file, "a") as f:
        f.write(json.dumps(metadata) + "\n")

    logger.info(f"  Training metadata saved to {metadata_file}")


# Additional helper task for manual/on-demand training
@celery_app.task(
    name="src.workers.tasks.model_trainer.train_models_on_demand",
    time_limit=3000,
    soft_time_limit=2700,
)
def train_models_on_demand(
    lookback_days: int = 90,
    output_dir: str = "output/models",
) -> Dict[str, Any]:
    """
    On-demand model training task (can be triggered manually).

    Same as train_models but without scheduled execution.

    Args:
        lookback_days: Number of days of historical data to use
        output_dir: Directory to save models

    Returns:
        Training result dictionary
    """
    logger.info("On-demand model training triggered")
    return train_models.apply(kwargs={
        "lookback_days": lookback_days,
        "output_dir": output_dir,
    }).get()
