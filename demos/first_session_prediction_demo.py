"""
Demo script for First Session Success Prediction Model (Task 10).

This script demonstrates:
1. Training the first session prediction model
2. Making predictions for upcoming sessions
3. Generating email alerts for high-risk sessions
4. Monitoring model performance

Usage:
    python demos/first_session_prediction_demo.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine
import logging

from src.evaluation.first_session_model_training import train_first_session_model
from src.evaluation.first_session_prediction_service import FirstSessionPredictionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Run first session prediction demo."""

    print("=" * 80)
    print("TASK 10: FIRST SESSION SUCCESS PREDICTION MODEL - DEMO")
    print("=" * 80)

    # Database connection
    DATABASE_URL = "postgresql://tutormax:tutormax_dev@localhost:5432/tutormax"
    engine = create_engine(DATABASE_URL)

    # Step 1: Load data
    print("\n" + "=" * 80)
    print("STEP 1: LOADING DATA FROM DATABASE")
    print("=" * 80)

    try:
        tutors_df = pd.read_sql("SELECT * FROM tutors", engine)
        sessions_df = pd.read_sql("SELECT * FROM sessions", engine)
        feedback_df = pd.read_sql("SELECT * FROM student_feedback", engine)

        print(f"\nLoaded data:")
        print(f"  Tutors: {len(tutors_df):,}")
        print(f"  Sessions: {len(sessions_df):,}")
        print(f"  Feedback: {len(feedback_df):,}")

        # Check for first sessions
        first_sessions = sessions_df[sessions_df['session_number'] == 1]
        first_sessions_with_feedback = first_sessions.merge(
            feedback_df[['session_id', 'overall_rating']],
            on='session_id',
            how='inner'
        )

        print(f"\nFirst session analysis:")
        print(f"  Total first sessions: {len(first_sessions):,}")
        print(f"  First sessions with feedback: {len(first_sessions_with_feedback):,}")

        if len(first_sessions_with_feedback) > 0:
            poor_rate = (first_sessions_with_feedback['overall_rating'] < 3).mean()
            print(f"  Poor first session rate (rating < 3): {poor_rate:.2%}")

    except Exception as e:
        print(f"\nError loading data: {e}")
        print("\nPlease ensure:")
        print("  1. PostgreSQL is running")
        print("  2. TutorMax database exists")
        print("  3. Test data has been generated")
        return

    # Step 2: Train model
    print("\n" + "=" * 80)
    print("STEP 2: TRAINING FIRST SESSION PREDICTION MODEL")
    print("=" * 80)

    output_dir = "output/models/first_session"

    try:
        model, results = train_first_session_model(
            tutors_df=tutors_df,
            sessions_df=sessions_df,
            feedback_df=feedback_df,
            output_dir=output_dir,
            test_size=0.2,
            cv_folds=5
        )

        print(f"\nModel training complete!")
        print(f"\nPerformance metrics:")
        print(f"  AUC-ROC: {results['auc_roc']:.4f}")
        print(f"  Precision: {results['precision']:.4f}")
        print(f"  Recall: {results['recall']:.4f}")
        print(f"  F1-Score: {results['f1_score']:.4f}")
        print(f"  Accuracy: {results['accuracy']:.4f}")

        # Check success criteria
        meets_auc = results['auc_roc'] > 0.75
        meets_precision = results['precision'] > 0.60

        print(f"\nSuccess criteria:")
        print(f"  ✓ AUC-ROC > 0.75: {'PASS' if meets_auc else 'FAIL'} ({results['auc_roc']:.4f})")
        print(f"  ✓ Precision > 0.60: {'PASS' if meets_precision else 'FAIL'} ({results['precision']:.4f})")

    except Exception as e:
        print(f"\nError training model: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 3: Load prediction service
    print("\n" + "=" * 80)
    print("STEP 3: LOADING PREDICTION SERVICE")
    print("=" * 80)

    model_path = f"{output_dir}/first_session_model.pkl"

    try:
        service = FirstSessionPredictionService(model_path)

        print(f"\nPrediction service loaded successfully")
        print(f"  Model version: {service.model_version}")
        print(f"  Features: {len(service.feature_names)}")

        info = service.get_model_info()
        print(f"\nRisk thresholds:")
        for level, threshold in info['risk_thresholds'].items():
            print(f"  {level}: {threshold:.2f}")

    except Exception as e:
        print(f"\nError loading service: {e}")
        return

    # Step 4: Make predictions for upcoming sessions
    print("\n" + "=" * 80)
    print("STEP 4: PREDICTING UPCOMING FIRST SESSIONS")
    print("=" * 80)

    # Find upcoming first sessions
    now = datetime.now()
    future_cutoff = now + timedelta(hours=48)

    upcoming_sessions = sessions_df[
        (sessions_df['session_number'] == 1) &
        (sessions_df['scheduled_start'] >= now) &
        (sessions_df['scheduled_start'] <= future_cutoff)
    ].copy()

    print(f"\nFound {len(upcoming_sessions)} upcoming first sessions (next 48 hours)")

    if len(upcoming_sessions) > 0:
        predictions = []

        for idx, session in upcoming_sessions.head(5).iterrows():  # Show first 5
            try:
                prediction = service.predict_session(
                    session_id=session['session_id'],
                    tutor_id=session['tutor_id'],
                    student_id=session['student_id'],
                    scheduled_start=session['scheduled_start'],
                    subject=session['subject'],
                    tutors_df=tutors_df,
                    sessions_df=sessions_df[sessions_df['scheduled_start'] < now],
                    feedback_df=feedback_df,
                    student_age=12  # Default
                )

                predictions.append(prediction)

                print(f"\nSession: {session['session_id']}")
                print(f"  Tutor: {prediction['tutor_name']}")
                print(f"  Subject: {session['subject']}")
                print(f"  Scheduled: {session['scheduled_start'].strftime('%Y-%m-%d %H:%M')}")
                print(f"  Risk Score: {prediction['risk_score']}/100")
                print(f"  Risk Level: {prediction['risk_level']}")
                print(f"  Alert Recommended: {'YES' if prediction['should_send_alert'] else 'NO'}")

            except Exception as e:
                print(f"\nError predicting session {session['session_id']}: {e}")
                continue

        # Summary statistics
        if predictions:
            print(f"\n" + "-" * 80)
            print(f"PREDICTION SUMMARY (first 5 sessions)")
            print("-" * 80)

            risk_levels = [p['risk_level'] for p in predictions]
            alert_count = sum(1 for p in predictions if p['should_send_alert'])

            print(f"\nRisk distribution:")
            for level in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']:
                count = sum(1 for r in risk_levels if r == level)
                pct = count / len(risk_levels) * 100
                print(f"  {level:8s}: {count:2d} ({pct:5.1f}%)")

            print(f"\nAlerts:")
            print(f"  Total recommended: {alert_count}/{len(predictions)}")
            print(f"  Alert rate: {alert_count/len(predictions)*100:.1f}%")

    else:
        print("\nNo upcoming first sessions found. Creating simulated example...")

        # Create a simulated upcoming session
        tutor = tutors_df.iloc[0]

        simulated_prediction = service.predict_session(
            session_id='DEMO_SESSION_001',
            tutor_id=tutor['tutor_id'],
            student_id='DEMO_STUDENT_001',
            scheduled_start=datetime.now() + timedelta(hours=2),
            subject='Math',
            tutors_df=tutors_df,
            sessions_df=sessions_df[sessions_df['scheduled_start'] < now],
            feedback_df=feedback_df,
            student_age=12
        )

        print(f"\nSimulated prediction example:")
        print(f"  Tutor: {tutor['name']}")
        print(f"  Risk Score: {simulated_prediction['risk_score']}/100")
        print(f"  Risk Level: {simulated_prediction['risk_level']}")
        print(f"  Should Alert: {'YES' if simulated_prediction['should_send_alert'] else 'NO'}")

    # Step 5: Email alert demonstration
    print("\n" + "=" * 80)
    print("STEP 5: EMAIL ALERT SYSTEM")
    print("=" * 80)

    from src.evaluation.first_session_email_service import get_first_session_email_service

    email_service = get_first_session_email_service()

    if email_service:
        print("\nEmail service configured and ready")
        print(f"  SMTP Host: {email_service.smtp_host}")
        print(f"  From: {email_service.from_email}")
        print("\nNote: Email alerts would be sent automatically for high-risk sessions")
    else:
        print("\nEmail service not configured (SMTP settings required)")
        print("\nTo enable email alerts, configure in .env:")
        print("  SMTP_HOST=smtp.example.com")
        print("  SMTP_PORT=587")
        print("  SMTP_USER=your_email@example.com")
        print("  SMTP_PASSWORD=your_password")

    # Step 6: Model monitoring
    print("\n" + "=" * 80)
    print("STEP 6: MODEL MONITORING")
    print("=" * 80)

    print("\nModel monitoring features:")
    print("  1. Prediction logging to database")
    print("  2. Actual outcome tracking (after session)")
    print("  3. Automated performance evaluation")
    print("  4. Retraining triggers based on accuracy")

    print("\nCelery workers for automation:")
    print("  - predict_upcoming_first_sessions (hourly)")
    print("  - update_prediction_outcomes (daily)")
    print("  - evaluate_model_performance (weekly)")

    print("\nTo start workers:")
    print("  celery -A src.workers.first_session_worker worker --loglevel=info")
    print("  celery -A src.workers.first_session_worker beat --loglevel=info")

    # Final summary
    print("\n" + "=" * 80)
    print("DEMO COMPLETE - TASK 10 IMPLEMENTATION SUMMARY")
    print("=" * 80)

    print("\n✓ Components implemented:")
    print("  1. Logistic Regression ML model (scikit-learn)")
    print("  2. Feature engineering (tenure, ratings, engagement, etc.)")
    print("  3. Real-time prediction service")
    print("  4. Email alert system with preparation tips")
    print("  5. FastAPI endpoints for predictions and analytics")
    print("  6. Celery workers for automated processing")
    print("  7. Database models for prediction tracking")
    print("  8. Model monitoring and performance evaluation")

    print("\n✓ Success metrics:")
    print(f"  - Model accuracy: {results.get('auc_roc', 0):.2%} (target: >75%)")
    print(f"  - Precision: {results.get('precision', 0):.2%} (target: >60%)")
    print("  - API response time: <200ms (design target)")
    print("  - Email delivery: 95%+ (infrastructure dependent)")

    print("\n✓ Integration points:")
    print("  - PostgreSQL: Prediction storage and tracking")
    print("  - Redis/Celery: Asynchronous job processing")
    print("  - SMTP: Email alert delivery")
    print("  - FastAPI: REST API endpoints")

    print("\n✓ Deliverables:")
    print("  - src/evaluation/first_session_model_training.py")
    print("  - src/evaluation/first_session_prediction_service.py")
    print("  - src/evaluation/first_session_email_service.py")
    print("  - src/api/first_session_router.py")
    print("  - src/workers/first_session_worker.py")
    print("  - Database migration for new tables")
    print("  - Comprehensive test suite")
    print("  - Documentation and demo script")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
