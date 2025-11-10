"""
First Session Success Prediction Service.

Production service for predicting poor first session experiences and
triggering pre-session alerts to tutors.

Features:
- Real-time prediction for upcoming sessions
- Batch prediction for scheduled sessions
- Risk scoring and classification
- Feature calculation from live data
"""

import joblib
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class FirstSessionPredictionService:
    """
    Production service for first session success prediction.

    Loads trained model and provides prediction capabilities for
    upcoming first sessions.
    """

    # Risk level thresholds (probability of poor session)
    RISK_THRESHOLDS = {
        'LOW': 0.3,        # < 30% probability
        'MEDIUM': 0.5,     # 30-50% probability
        'HIGH': 0.7,       # 50-70% probability
        'CRITICAL': 1.0    # > 70% probability
    }

    # Alert threshold: send email if risk >= this
    ALERT_THRESHOLD = 0.5  # 50% probability

    def __init__(self, model_path: str):
        """
        Initialize prediction service.

        Args:
            model_path: Path to trained model file
        """
        self.model_path = Path(model_path)
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.model_version = None

        # Load model on initialization
        self._load_model()

    def _load_model(self) -> None:
        """Load trained model from disk."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        try:
            model_data = joblib.load(self.model_path)

            # Extract model and metadata
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.model_version = model_data.get('version', 'unknown')

            logger.info(f"Loaded first session model from {self.model_path}")
            logger.info(f"Model version: {self.model_version}")
            logger.info(f"Model expects {len(self.feature_names)} features")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def predict_session(
        self,
        session_id: str,
        tutor_id: str,
        student_id: str,
        scheduled_start: datetime,
        subject: str,
        tutors_df: pd.DataFrame,
        sessions_df: pd.DataFrame,
        feedback_df: pd.DataFrame,
        student_age: int = 12
    ) -> Dict[str, Any]:
        """
        Make prediction for a single upcoming first session.

        Args:
            session_id: Session ID
            tutor_id: Tutor ID
            student_id: Student ID
            scheduled_start: Scheduled start time
            subject: Session subject
            tutors_df: Tutor profiles dataframe
            sessions_df: Historical sessions dataframe
            feedback_df: Historical feedback dataframe
            student_age: Student age (default: 12)

        Returns:
            Dictionary with prediction results
        """
        # Get tutor info
        tutor = tutors_df[tutors_df['tutor_id'] == tutor_id].iloc[0]

        # Calculate features
        features = self._calculate_features(
            tutor_id=tutor_id,
            tutor=tutor,
            scheduled_start=scheduled_start,
            subject=subject,
            student_age=student_age,
            sessions_df=sessions_df,
            feedback_df=feedback_df
        )

        # Make prediction
        prediction_result = self._predict_from_features(features)

        # Add session context
        prediction_result.update({
            'session_id': session_id,
            'tutor_id': tutor_id,
            'tutor_name': tutor['name'],
            'student_id': student_id,
            'scheduled_start': scheduled_start.isoformat(),
            'subject': subject,
            'prediction_date': datetime.now().isoformat(),
            'should_send_alert': prediction_result['risk_probability'] >= self.ALERT_THRESHOLD
        })

        return prediction_result

    def predict_upcoming_sessions(
        self,
        upcoming_sessions_df: pd.DataFrame,
        tutors_df: pd.DataFrame,
        sessions_df: pd.DataFrame,
        feedback_df: pd.DataFrame,
        lookhead_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Make predictions for all upcoming first sessions.

        Args:
            upcoming_sessions_df: Dataframe of scheduled sessions
            tutors_df: Tutor profiles
            sessions_df: Historical sessions
            feedback_df: Historical feedback
            lookhead_hours: Only predict sessions within this many hours

        Returns:
            List of prediction results
        """
        logger.info(f"Predicting upcoming first sessions (next {lookhead_hours}h)")

        # Filter for first sessions within lookahead window
        now = datetime.now()
        cutoff = now + timedelta(hours=lookhead_hours)

        first_sessions = upcoming_sessions_df[
            (upcoming_sessions_df['session_number'] == 1) &
            (upcoming_sessions_df['scheduled_start'] >= now) &
            (upcoming_sessions_df['scheduled_start'] <= cutoff)
        ].copy()

        logger.info(f"Found {len(first_sessions)} upcoming first sessions")

        results = []
        for _, session in first_sessions.iterrows():
            try:
                prediction = self.predict_session(
                    session_id=session['session_id'],
                    tutor_id=session['tutor_id'],
                    student_id=session['student_id'],
                    scheduled_start=session['scheduled_start'],
                    subject=session['subject'],
                    tutors_df=tutors_df,
                    sessions_df=sessions_df,
                    feedback_df=feedback_df,
                    student_age=12  # Default, should come from students table
                )
                results.append(prediction)

            except Exception as e:
                logger.error(f"Failed to predict session {session['session_id']}: {e}")
                continue

        logger.info(f"Generated {len(results)} predictions")

        # Count high-risk sessions
        high_risk_count = sum(1 for r in results if r['should_send_alert'])
        logger.info(f"High-risk sessions (alert threshold): {high_risk_count}")

        return results

    def _calculate_features(
        self,
        tutor_id: str,
        tutor: pd.Series,
        scheduled_start: datetime,
        subject: str,
        student_age: int,
        sessions_df: pd.DataFrame,
        feedback_df: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Calculate features for a single session.

        Args:
            tutor_id: Tutor ID
            tutor: Tutor profile row
            scheduled_start: Session scheduled start
            subject: Session subject
            student_age: Student age
            sessions_df: Historical sessions
            feedback_df: Historical feedback

        Returns:
            Dictionary of features
        """
        # --- Tutor Profile Features ---

        # Tutor tenure (days since onboarding)
        tenure_days = (scheduled_start - tutor['onboarding_date']).days

        # --- Historical Performance Features ---

        # Get prior sessions (before scheduled_start)
        prior_sessions = sessions_df[
            (sessions_df['tutor_id'] == tutor_id) &
            (sessions_df['scheduled_start'] < scheduled_start)
        ].copy()

        # Get prior feedback
        prior_feedback = feedback_df[
            feedback_df['session_id'].isin(prior_sessions['session_id'])
        ].copy()

        # Average rating
        if len(prior_feedback) > 0:
            avg_rating = prior_feedback['overall_rating'].mean()
        else:
            avg_rating = 3.0  # Neutral default

        # First session success rate
        prior_first_sessions = prior_sessions[prior_sessions['session_number'] == 1]
        prior_first_feedback = feedback_df[
            feedback_df['session_id'].isin(prior_first_sessions['session_id'])
        ]

        if len(prior_first_feedback) > 0:
            first_session_success_rate = (prior_first_feedback['overall_rating'] >= 3).mean()
        else:
            first_session_success_rate = 0.5  # Neutral default

        # Engagement score
        if len(prior_sessions) > 0:
            engagement_score = prior_sessions['engagement_score'].mean()
            if pd.isna(engagement_score):
                engagement_score = 0.5
        else:
            engagement_score = 0.5

        # Reschedule rate
        if len(prior_sessions) > 0:
            reschedule_rate = prior_sessions['tutor_initiated_reschedule'].mean()
        else:
            reschedule_rate = 0.0

        # No-show rate
        if len(prior_sessions) > 0:
            no_show_rate = prior_sessions['no_show'].mean()
        else:
            no_show_rate = 0.0

        # Session count
        session_count = len(prior_sessions)

        # --- Session Context Features ---

        # Time of day features (cyclical encoding)
        hour_of_day = scheduled_start.hour
        hour_sin = np.sin(2 * np.pi * hour_of_day / 24)
        hour_cos = np.cos(2 * np.pi * hour_of_day / 24)

        # Day of week features (cyclical encoding)
        day_of_week = scheduled_start.weekday()
        day_sin = np.sin(2 * np.pi * day_of_week / 7)
        day_cos = np.cos(2 * np.pi * day_of_week / 7)

        # Build feature dictionary
        features = {
            'tenure_days': tenure_days,
            'avg_rating': avg_rating,
            'first_session_success_rate': first_session_success_rate,
            'engagement_score': engagement_score,
            'reschedule_rate': reschedule_rate,
            'no_show_rate': no_show_rate,
            'session_count': session_count,
            'hour_sin': hour_sin,
            'hour_cos': hour_cos,
            'day_sin': day_sin,
            'day_cos': day_cos,
            'student_age': student_age,
        }

        # Add subject one-hot encoding
        # Match training feature names (subject_<subject>)
        for feature_name in self.feature_names:
            if feature_name.startswith('subject_'):
                subject_value = feature_name.replace('subject_', '')
                features[feature_name] = 1.0 if subject == subject_value else 0.0

        return features

    def _predict_from_features(
        self,
        features: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Make prediction from calculated features.

        Args:
            features: Dictionary of features

        Returns:
            Dictionary with prediction results
        """
        # Convert to dataframe
        feature_df = pd.DataFrame([features])

        # Ensure all required features are present
        for feature_name in self.feature_names:
            if feature_name not in feature_df.columns:
                feature_df[feature_name] = 0.0

        # Reorder columns to match training
        feature_df = feature_df[self.feature_names]

        # Scale features
        features_scaled = self.scaler.transform(feature_df)

        # Make prediction
        risk_probability = self.model.predict_proba(features_scaled)[0, 1]
        risk_prediction = int(risk_probability >= 0.5)

        # Calculate risk score (0-100)
        risk_score = int(risk_probability * 100)

        # Determine risk level
        risk_level = self._calculate_risk_level(risk_probability)

        # Get feature contributions (coefficients)
        coefficients = dict(zip(self.feature_names, self.model.coef_[0]))

        # Find top contributing factors
        feature_values = feature_df.iloc[0].to_dict()
        contributions = {}

        for feature_name in self.feature_names:
            coef = coefficients[feature_name]
            value = feature_values[feature_name]
            contribution = coef * value
            contributions[feature_name] = {
                'coefficient': float(coef),
                'value': float(value),
                'contribution': float(contribution)
            }

        # Sort by absolute contribution
        top_factors = dict(
            sorted(
                contributions.items(),
                key=lambda x: abs(x[1]['contribution']),
                reverse=True
            )[:5]
        )

        return {
            'risk_probability': float(risk_probability),
            'risk_prediction': risk_prediction,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'model_version': self.model_version,
            'top_risk_factors': top_factors
        }

    def _calculate_risk_level(self, probability: float) -> str:
        """
        Calculate risk level from probability.

        Args:
            probability: Risk probability (0-1)

        Returns:
            Risk level string
        """
        if probability < self.RISK_THRESHOLDS['LOW']:
            return 'LOW'
        elif probability < self.RISK_THRESHOLDS['MEDIUM']:
            return 'MEDIUM'
        elif probability < self.RISK_THRESHOLDS['HIGH']:
            return 'HIGH'
        else:
            return 'CRITICAL'

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model metadata and configuration.

        Returns:
            Dictionary with model information
        """
        return {
            'model_path': str(self.model_path),
            'model_version': self.model_version,
            'model_type': 'LogisticRegression',
            'feature_count': len(self.feature_names),
            'risk_thresholds': self.RISK_THRESHOLDS,
            'alert_threshold': self.ALERT_THRESHOLD,
        }


def load_first_session_service(
    model_path: str = "output/models/first_session/first_session_model.pkl"
) -> FirstSessionPredictionService:
    """
    Factory function to create first session prediction service.

    Args:
        model_path: Path to trained model

    Returns:
        Initialized FirstSessionPredictionService
    """
    return FirstSessionPredictionService(model_path)
