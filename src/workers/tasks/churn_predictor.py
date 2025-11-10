"""
Celery tasks for churn prediction.

Implements both batch and event-driven churn prediction tasks:
- batch_predict_churn: Daily batch prediction for all active tutors (scheduled at midnight)
- predict_churn_for_tutor: Event-driven prediction for individual tutor (triggered by events)
"""

import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import uuid

import pandas as pd
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session
from celery import Task

from ..celery_app import celery_app
from ...database.models import (
    Tutor,
    Session as SessionModel,
    StudentFeedback,
    ChurnPrediction,
    TutorStatus,
    RiskLevel,
)
from ...api.config import settings
from ...evaluation.prediction_service import ChurnPredictionService
from ...evaluation.feature_engineering import ChurnFeatureEngineer

# Configure logging
logger = logging.getLogger(__name__)

# Construct synchronous database URL for Celery
# Celery tasks run synchronously, so we need psycopg2 driver instead of asyncpg
SYNC_DATABASE_URL = f"postgresql+psycopg2://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"

# Create synchronous engine and session factory for worker tasks
sync_engine = create_engine(
    SYNC_DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    echo=False,
)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)


# Model loading and caching
class ChurnPredictorTask(Task):
    """
    Base task class with model caching.

    Loads the churn prediction model once and caches it for reuse across task invocations.
    This improves performance by avoiding repeated model loading from disk.
    """
    _model_service: Optional[ChurnPredictionService] = None
    _model_version: Optional[str] = None
    _model_path: Path = Path("output/models/churn_model.pkl")

    @property
    def model_service(self) -> ChurnPredictionService:
        """
        Lazy-load and cache the churn prediction model.

        Returns:
            ChurnPredictionService instance with loaded model
        """
        if self._model_service is None:
            logger.info("Loading churn prediction model...")
            try:
                if not self._model_path.exists():
                    raise FileNotFoundError(
                        f"Churn model not found at {self._model_path}. "
                        "Please train the model first using src/evaluation/model_training.py"
                    )

                self._model_service = ChurnPredictionService(
                    model_path=str(self._model_path)
                )
                self._model_version = self._model_service.model_version
                logger.info(f"Model loaded successfully (version: {self._model_version})")
            except Exception as e:
                logger.error(f"Failed to load churn prediction model: {e}")
                raise

        return self._model_service


def load_tutor_data(
    db: Session,
    tutor_id: Optional[str] = None,
    lookback_days: int = 90
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load tutor, session, and feedback data from database.

    Args:
        db: Database session
        tutor_id: Optional tutor ID to filter for single tutor
        lookback_days: Number of days of historical data to include

    Returns:
        Tuple of (tutors_df, sessions_df, feedback_df)
    """
    cutoff_date = datetime.now() - timedelta(days=lookback_days)

    # Load tutors
    if tutor_id:
        tutors_query = select(Tutor).where(
            Tutor.tutor_id == tutor_id,
            Tutor.status == TutorStatus.ACTIVE
        )
    else:
        tutors_query = select(Tutor).where(Tutor.status == TutorStatus.ACTIVE)

    tutors = db.execute(tutors_query).scalars().all()

    if not tutors:
        logger.warning(f"No active tutors found{' for ' + tutor_id if tutor_id else ''}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    # Convert to DataFrame
    tutors_data = []
    for tutor in tutors:
        tenure_days = (datetime.now() - tutor.onboarding_date).days
        tutors_data.append({
            'tutor_id': tutor.tutor_id,
            'name': tutor.name,
            'email': tutor.email,
            'onboarding_date': tutor.onboarding_date,
            'status': tutor.status.value,
            'subjects': tutor.subjects,
            'baseline_sessions_per_week': tutor.baseline_sessions_per_week or 0.0,
            'behavioral_archetype': tutor.behavioral_archetype.value if tutor.behavioral_archetype else None,
            'tenure_days': tenure_days,
        })

    tutors_df = pd.DataFrame(tutors_data)

    # Get tutor IDs for querying sessions and feedback
    tutor_ids = [t.tutor_id for t in tutors]

    # Load sessions
    sessions_query = select(SessionModel).where(
        SessionModel.tutor_id.in_(tutor_ids),
        SessionModel.scheduled_start >= cutoff_date
    )
    sessions = db.execute(sessions_query).scalars().all()

    sessions_data = []
    for session in sessions:
        sessions_data.append({
            'session_id': session.session_id,
            'tutor_id': session.tutor_id,
            'student_id': session.student_id,
            'scheduled_start': session.scheduled_start,
            'actual_start': session.actual_start,
            'duration_minutes': session.duration_minutes,
            'subject': session.subject,
            'tutor_initiated_reschedule': session.tutor_initiated_reschedule,
            'no_show': session.no_show,
            'late_start_minutes': session.late_start_minutes,
            'engagement_score': session.engagement_score,
            'learning_objectives_met': session.learning_objectives_met,
            'technical_issues': session.technical_issues,
            'is_first_session': session.session_number == 1,
        })

    sessions_df = pd.DataFrame(sessions_data)

    # Load feedback
    feedback_query = select(StudentFeedback).where(
        StudentFeedback.tutor_id.in_(tutor_ids),
        StudentFeedback.submitted_at >= cutoff_date
    )
    feedbacks = db.execute(feedback_query).scalars().all()

    feedback_data = []
    for feedback in feedbacks:
        feedback_data.append({
            'feedback_id': feedback.feedback_id,
            'session_id': feedback.session_id,
            'tutor_id': feedback.tutor_id,
            'student_id': feedback.student_id,
            'overall_rating': feedback.overall_rating,
            'subject_knowledge_rating': feedback.subject_knowledge_rating,
            'communication_rating': feedback.communication_rating,
            'patience_rating': feedback.patience_rating,
            'engagement_rating': feedback.engagement_rating,
            'submitted_at': feedback.submitted_at,
        })

    feedback_df = pd.DataFrame(feedback_data)

    logger.info(
        f"Loaded data: {len(tutors_df)} tutors, "
        f"{len(sessions_df)} sessions, "
        f"{len(feedback_df)} feedback records"
    )

    return tutors_df, sessions_df, feedback_df


def save_prediction(
    db: Session,
    tutor_id: str,
    prediction_result: Dict[str, Any],
    model_version: str
) -> str:
    """
    Save churn prediction to database.

    Args:
        db: Database session
        tutor_id: Tutor ID
        prediction_result: Prediction result dictionary from ChurnPredictionService
        model_version: Model version string

    Returns:
        prediction_id: ID of saved prediction
    """
    # Map risk level string to enum
    risk_level_map = {
        'LOW': RiskLevel.LOW,
        'MEDIUM': RiskLevel.MEDIUM,
        'HIGH': RiskLevel.HIGH,
        'CRITICAL': RiskLevel.CRITICAL,
    }

    risk_level = risk_level_map.get(
        prediction_result['risk_level'],
        RiskLevel.MEDIUM
    )

    # Create prediction record
    prediction_id = f"pred_{uuid.uuid4().hex[:12]}"

    # Extract contributing factors if available
    contributing_factors = prediction_result.get('contributing_factors')

    prediction = ChurnPrediction(
        prediction_id=prediction_id,
        tutor_id=tutor_id,
        prediction_date=datetime.now(),
        churn_score=prediction_result['churn_score'],
        risk_level=risk_level,
        window_1day_probability=None,  # Not implemented in current model
        window_7day_probability=None,
        window_30day_probability=prediction_result['churn_probability'],
        window_90day_probability=None,
        contributing_factors=contributing_factors,
        model_version=model_version,
    )

    db.add(prediction)
    db.commit()

    logger.info(
        f"Saved prediction for tutor {tutor_id}: "
        f"score={prediction_result['churn_score']}, "
        f"risk={risk_level.value}"
    )

    return prediction_id


@celery_app.task(
    bind=True,
    base=ChurnPredictorTask,
    name="src.workers.tasks.churn_predictor.batch_predict_churn",
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,  # 10 minutes
    retry_jitter=True,
)
def batch_predict_churn(self, lookback_days: int = 90) -> Dict[str, Any]:
    """
    Daily batch churn prediction for all active tutors.

    Scheduled to run daily at midnight via Celery Beat.
    Processes all active tutors and stores predictions in database.

    Args:
        lookback_days: Number of days of historical data to use for features

    Returns:
        Dictionary with prediction summary statistics
    """
    logger.info("Starting batch churn prediction...")
    start_time = datetime.now()

    db = SyncSessionLocal()
    try:
        # Load data for all active tutors
        tutors_df, sessions_df, feedback_df = load_tutor_data(
            db=db,
            tutor_id=None,
            lookback_days=lookback_days
        )

        if tutors_df.empty:
            logger.warning("No active tutors found for batch prediction")
            return {
                'status': 'completed',
                'tutors_processed': 0,
                'predictions_created': 0,
                'errors': 0,
                'duration_seconds': 0,
            }

        # Make predictions using cached model
        logger.info(f"Making predictions for {len(tutors_df)} tutors...")
        predictions = self.model_service.predict_batch(
            tutors_df=tutors_df,
            sessions_df=sessions_df,
            feedback_df=feedback_df,
            include_explanation=True  # Include SHAP explanations
        )

        # Save predictions to database
        logger.info("Saving predictions to database...")
        predictions_created = 0
        errors = 0
        risk_distribution = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0}

        for prediction in predictions:
            try:
                save_prediction(
                    db=db,
                    tutor_id=prediction['tutor_id'],
                    prediction_result=prediction,
                    model_version=self.model_service.model_version
                )
                predictions_created += 1
                risk_distribution[prediction['risk_level']] += 1
            except Exception as e:
                logger.error(f"Failed to save prediction for {prediction['tutor_id']}: {e}")
                errors += 1

        duration = (datetime.now() - start_time).total_seconds()

        summary = {
            'status': 'completed',
            'tutors_processed': len(tutors_df),
            'predictions_created': predictions_created,
            'errors': errors,
            'risk_distribution': risk_distribution,
            'duration_seconds': duration,
            'model_version': self.model_service.model_version,
            'timestamp': datetime.now().isoformat(),
        }

        logger.info(
            f"Batch prediction completed: {predictions_created} predictions created "
            f"in {duration:.1f}s (errors: {errors})"
        )
        logger.info(f"Risk distribution: {risk_distribution}")

        return summary

    except Exception as e:
        logger.error(f"Batch prediction failed: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(
    bind=True,
    base=ChurnPredictorTask,
    name="src.workers.tasks.churn_predictor.predict_churn_for_tutor",
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
)
def predict_churn_for_tutor(
    self,
    tutor_id: str,
    lookback_days: int = 90,
    include_explanation: bool = True
) -> Dict[str, Any]:
    """
    Event-driven churn prediction for individual tutor.

    Triggered by specific events such as:
    - Low performance evaluation scores
    - Completion of sessions with concerning patterns
    - Manual request from operations manager

    Args:
        tutor_id: Tutor ID to predict churn for
        lookback_days: Number of days of historical data to use
        include_explanation: Whether to include SHAP explanation

    Returns:
        Dictionary with prediction result
    """
    logger.info(f"Starting churn prediction for tutor: {tutor_id}")
    start_time = datetime.now()

    db = SyncSessionLocal()
    try:
        # Load data for specific tutor
        tutors_df, sessions_df, feedback_df = load_tutor_data(
            db=db,
            tutor_id=tutor_id,
            lookback_days=lookback_days
        )

        if tutors_df.empty:
            logger.warning(f"Tutor {tutor_id} not found or not active")
            return {
                'status': 'error',
                'error': f"Tutor {tutor_id} not found or not active",
                'tutor_id': tutor_id,
            }

        # Make prediction using cached model
        logger.info(f"Making prediction for tutor {tutor_id}...")
        prediction = self.model_service.predict_tutor(
            tutor_id=tutor_id,
            tutors_df=tutors_df,
            sessions_df=sessions_df,
            feedback_df=feedback_df,
            include_explanation=include_explanation
        )

        # Save prediction to database
        prediction_id = save_prediction(
            db=db,
            tutor_id=tutor_id,
            prediction_result=prediction,
            model_version=self.model_service.model_version
        )

        duration = (datetime.now() - start_time).total_seconds()

        result = {
            'status': 'completed',
            'prediction_id': prediction_id,
            'tutor_id': tutor_id,
            'churn_score': prediction['churn_score'],
            'risk_level': prediction['risk_level'],
            'churn_probability': prediction['churn_probability'],
            'model_version': self.model_service.model_version,
            'duration_seconds': duration,
            'timestamp': datetime.now().isoformat(),
        }

        if include_explanation and 'contributing_factors' in prediction:
            result['contributing_factors'] = prediction['contributing_factors']

        logger.info(
            f"Prediction completed for {tutor_id}: "
            f"score={prediction['churn_score']}, "
            f"risk={prediction['risk_level']} "
            f"({duration:.2f}s)"
        )

        return result

    except Exception as e:
        logger.error(f"Prediction failed for tutor {tutor_id}: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()
