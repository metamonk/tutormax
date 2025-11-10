"""
Celery worker for first session prediction and alerting.

Handles:
- Scheduled batch prediction for upcoming first sessions
- Real-time prediction on session creation
- Email alert delivery to high-risk tutors
- Prediction outcome tracking and model monitoring
"""

from celery import Celery, Task
from datetime import datetime, timedelta
from sqlalchemy import create_engine, select, and_
from sqlalchemy.orm import Session
import pandas as pd
import logging
import uuid
import os

from ..database.models import (
    FirstSessionPrediction,
    Session as SessionModel,
    Tutor,
    Student,
    StudentFeedback,
    ModelPerformanceLog,
    RiskLevel
)
from ..evaluation.first_session_prediction_service import FirstSessionPredictionService
from ..evaluation.first_session_email_service import FirstSessionEmailService
from ..api.config import settings

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    'first_session_worker',
    broker=settings.redis_url,
    backend=settings.redis_url
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
)

# Database engine for worker (sync)
DATABASE_URL = f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)


class DatabaseTask(Task):
    """Base task with database session management."""

    _db_session = None

    @property
    def db_session(self):
        if self._db_session is None:
            self._db_session = Session(engine)
        return self._db_session

    def after_return(self, *args, **kwargs):
        if self._db_session is not None:
            self._db_session.close()
            self._db_session = None


@celery_app.task(base=DatabaseTask, name='predict_upcoming_first_sessions')
def predict_upcoming_first_sessions(lookahead_hours: int = 24) -> dict:
    """
    Batch prediction for all upcoming first sessions.

    This task runs periodically (e.g., every hour) to identify and predict
    upcoming first sessions, sending alerts when needed.

    Args:
        lookahead_hours: Hours to look ahead (default: 24)

    Returns:
        Dictionary with prediction summary
    """
    logger.info(f"Starting batch first session prediction (lookahead: {lookahead_hours}h)")

    try:
        db = predict_upcoming_first_sessions.db_session

        # Load prediction service
        model_path = "output/models/first_session/first_session_model.pkl"
        if not os.path.exists(model_path):
            logger.error(f"Model file not found: {model_path}")
            return {"error": "Model not found", "predictions": 0}

        service = FirstSessionPredictionService(model_path)

        # Calculate time window
        now = datetime.now()
        cutoff = now + timedelta(hours=lookahead_hours)

        # Query upcoming first sessions
        upcoming_sessions = db.execute(
            select(SessionModel, Tutor, Student)
            .join(Tutor, SessionModel.tutor_id == Tutor.tutor_id)
            .join(Student, SessionModel.student_id == Student.student_id)
            .where(
                and_(
                    SessionModel.session_number == 1,
                    SessionModel.scheduled_start >= now,
                    SessionModel.scheduled_start <= cutoff
                )
            )
        ).all()

        logger.info(f"Found {len(upcoming_sessions)} upcoming first sessions")

        # Load historical data for feature calculation
        tutors_df = pd.read_sql("SELECT * FROM tutors", engine)
        sessions_df = pd.read_sql("SELECT * FROM sessions WHERE scheduled_start < NOW()", engine)
        feedback_df = pd.read_sql("SELECT * FROM student_feedback", engine)

        predictions_made = 0
        alerts_sent = 0
        high_risk_count = 0

        for session, tutor, student in upcoming_sessions:
            # Check if prediction already exists
            existing = db.execute(
                select(FirstSessionPrediction)
                .where(FirstSessionPrediction.session_id == session.session_id)
            ).scalar_one_or_none()

            if existing:
                logger.debug(f"Prediction already exists for session {session.session_id}")
                continue

            # Make prediction
            try:
                prediction = service.predict_session(
                    session_id=session.session_id,
                    tutor_id=session.tutor_id,
                    student_id=session.student_id,
                    scheduled_start=session.scheduled_start,
                    subject=session.subject,
                    tutors_df=tutors_df,
                    sessions_df=sessions_df,
                    feedback_df=feedback_df,
                    student_age=student.age or 12
                )

                # Save prediction to database
                db_prediction = FirstSessionPrediction(
                    prediction_id=f"fsp_{uuid.uuid4().hex[:12]}",
                    session_id=session.session_id,
                    tutor_id=session.tutor_id,
                    student_id=session.student_id,
                    prediction_date=datetime.now(),
                    risk_probability=prediction['risk_probability'],
                    risk_score=prediction['risk_score'],
                    risk_level=RiskLevel[prediction['risk_level']],
                    risk_prediction=prediction['risk_prediction'],
                    model_version=prediction['model_version'],
                    top_risk_factors=prediction.get('top_risk_factors'),
                    alert_sent=False
                )

                db.add(db_prediction)
                db.commit()

                predictions_made += 1

                if prediction['risk_level'] in ['HIGH', 'CRITICAL']:
                    high_risk_count += 1

                # Send alert if high risk
                if prediction['should_send_alert']:
                    # Trigger email alert task
                    send_first_session_alert.delay(
                        prediction_id=db_prediction.prediction_id,
                        tutor_email=tutor.email,
                        tutor_name=tutor.name,
                        student_name=student.name,
                        student_age=student.age or 12,
                        session_date=session.scheduled_start.isoformat(),
                        subject=session.subject,
                        risk_score=prediction['risk_score'],
                        risk_level=prediction['risk_level'],
                        top_risk_factors=prediction.get('top_risk_factors', {}),
                        session_id=session.session_id
                    )
                    alerts_sent += 1

            except Exception as e:
                logger.error(f"Failed to predict session {session.session_id}: {e}")
                continue

        logger.info(f"Batch prediction complete: {predictions_made} predictions, {alerts_sent} alerts queued, {high_risk_count} high-risk")

        return {
            "predictions_made": predictions_made,
            "alerts_sent": alerts_sent,
            "high_risk_count": high_risk_count,
            "total_sessions": len(upcoming_sessions)
        }

    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        return {"error": str(e), "predictions": 0}


@celery_app.task(base=DatabaseTask, name='send_first_session_alert')
def send_first_session_alert(
    prediction_id: str,
    tutor_email: str,
    tutor_name: str,
    student_name: str,
    student_age: int,
    session_date: str,
    subject: str,
    risk_score: int,
    risk_level: str,
    top_risk_factors: dict,
    session_id: str
) -> bool:
    """
    Send first session preparation alert email to tutor.

    Args:
        prediction_id: Prediction ID
        tutor_email: Tutor email
        tutor_name: Tutor name
        student_name: Student name
        student_age: Student age
        session_date: Session date (ISO format)
        subject: Session subject
        risk_score: Risk score
        risk_level: Risk level
        top_risk_factors: Top risk factors
        session_id: Session ID

    Returns:
        True if sent successfully
    """
    logger.info(f"Sending first session alert to {tutor_email} for session {session_id}")

    try:
        # Initialize email service
        if not all([settings.smtp_host, settings.smtp_user, settings.smtp_password]):
            logger.warning("SMTP not configured - skipping email")
            return False

        email_service = FirstSessionEmailService(
            smtp_host=settings.smtp_host,
            smtp_port=settings.smtp_port,
            smtp_user=settings.smtp_user,
            smtp_password=settings.smtp_password,
            smtp_use_tls=settings.smtp_use_tls,
            from_email=settings.smtp_from_email
        )

        # Parse session date
        session_datetime = datetime.fromisoformat(session_date)

        # Send email
        success = email_service.send_first_session_alert(
            tutor_email=tutor_email,
            tutor_name=tutor_name,
            student_name=student_name,
            student_age=student_age,
            session_date=session_datetime,
            subject=subject,
            risk_score=risk_score,
            risk_level=risk_level,
            top_risk_factors=top_risk_factors,
            session_id=session_id
        )

        if success:
            # Update prediction record
            db = send_first_session_alert.db_session
            prediction = db.execute(
                select(FirstSessionPrediction)
                .where(FirstSessionPrediction.prediction_id == prediction_id)
            ).scalar_one_or_none()

            if prediction:
                prediction.alert_sent = True
                prediction.alert_sent_at = datetime.now()
                db.commit()

            logger.info(f"Alert sent successfully for prediction {prediction_id}")

        return success

    except Exception as e:
        logger.error(f"Failed to send alert for prediction {prediction_id}: {e}")
        return False


@celery_app.task(base=DatabaseTask, name='update_prediction_outcomes')
def update_prediction_outcomes() -> dict:
    """
    Update prediction outcomes with actual session ratings.

    This task runs periodically to match predictions with actual feedback
    and calculate prediction accuracy.

    Returns:
        Dictionary with update summary
    """
    logger.info("Updating first session prediction outcomes")

    try:
        db = update_prediction_outcomes.db_session

        # Find predictions without outcomes
        predictions = db.execute(
            select(FirstSessionPrediction)
            .where(FirstSessionPrediction.actual_rating.is_(None))
        ).scalars().all()

        logger.info(f"Found {len(predictions)} predictions to update")

        updated_count = 0

        for prediction in predictions:
            # Check if session has feedback
            feedback = db.execute(
                select(StudentFeedback)
                .where(StudentFeedback.session_id == prediction.session_id)
            ).scalar_one_or_none()

            if feedback:
                # Update outcome
                prediction.actual_rating = feedback.overall_rating
                prediction.actual_poor_session = feedback.overall_rating < 3

                # Check if prediction was correct
                predicted_poor = prediction.risk_prediction == 1
                actual_poor = prediction.actual_poor_session

                prediction.prediction_correct = (predicted_poor == actual_poor)

                updated_count += 1

        db.commit()

        logger.info(f"Updated {updated_count} prediction outcomes")

        return {
            "predictions_checked": len(predictions),
            "outcomes_updated": updated_count
        }

    except Exception as e:
        logger.error(f"Failed to update outcomes: {e}")
        return {"error": str(e)}


@celery_app.task(base=DatabaseTask, name='evaluate_model_performance')
def evaluate_model_performance(time_window_days: int = 30) -> dict:
    """
    Evaluate model performance over recent predictions.

    This task runs periodically to calculate model accuracy and
    log performance metrics for monitoring.

    Args:
        time_window_days: Number of days to evaluate (default: 30)

    Returns:
        Dictionary with performance metrics
    """
    logger.info(f"Evaluating model performance (last {time_window_days} days)")

    try:
        db = evaluate_model_performance.db_session

        # Calculate time window
        cutoff = datetime.now() - timedelta(days=time_window_days)

        # Get predictions with outcomes
        predictions = db.execute(
            select(FirstSessionPrediction)
            .where(
                and_(
                    FirstSessionPrediction.prediction_date >= cutoff,
                    FirstSessionPrediction.actual_rating.isnot(None)
                )
            )
        ).scalars().all()

        if len(predictions) < 10:
            logger.warning(f"Insufficient data for evaluation: {len(predictions)} predictions")
            return {"error": "Insufficient data", "sample_size": len(predictions)}

        # Calculate metrics
        y_true = [1 if p.actual_poor_session else 0 for p in predictions]
        y_pred = [p.risk_prediction for p in predictions]
        y_prob = [p.risk_probability for p in predictions]

        # Simple accuracy calculation
        correct = sum(1 for yt, yp in zip(y_true, y_pred) if yt == yp)
        accuracy = correct / len(predictions)

        # Precision and recall for poor sessions (class 1)
        tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
        fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
        fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        # Simple AUC approximation (would use sklearn in production)
        # For now, use average probability for positive class
        auc_roc = sum(y_prob[i] for i, yt in enumerate(y_true) if yt == 1) / sum(y_true) if sum(y_true) > 0 else 0.5

        # Log performance
        log = ModelPerformanceLog(
            log_id=f"mpl_{uuid.uuid4().hex[:12]}",
            model_type="first_session",
            model_version="1.0.0",
            evaluation_date=datetime.now(),
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            auc_roc=auc_roc,
            sample_size=len(predictions),
            time_window_days=time_window_days,
            metrics_detail={
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "total_positive": sum(y_true),
                "total_negative": len(y_true) - sum(y_true)
            }
        )

        db.add(log)
        db.commit()

        logger.info(f"Model performance logged: accuracy={accuracy:.3f}, precision={precision:.3f}, recall={recall:.3f}")

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "auc_roc": auc_roc,
            "sample_size": len(predictions)
        }

    except Exception as e:
        logger.error(f"Failed to evaluate model performance: {e}")
        return {"error": str(e)}


# Celery beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'predict-upcoming-sessions-hourly': {
        'task': 'predict_upcoming_first_sessions',
        'schedule': 3600.0,  # Every hour
        'args': (24,)  # Look ahead 24 hours
    },
    'update-outcomes-daily': {
        'task': 'update_prediction_outcomes',
        'schedule': 86400.0,  # Every day
    },
    'evaluate-performance-weekly': {
        'task': 'evaluate_model_performance',
        'schedule': 604800.0,  # Every week
        'args': (30,)  # Evaluate last 30 days
    },
}


if __name__ == "__main__":
    # Run worker
    celery_app.start()
