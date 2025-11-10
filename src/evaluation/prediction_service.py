"""
Churn prediction service for production deployment.

Provides real-time and batch prediction capabilities for tutor churn.
Includes model loading, feature calculation, prediction, and SHAP explanations.
"""

import pickle
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np

from .feature_engineering import ChurnFeatureEngineer

logger = logging.getLogger(__name__)


class ChurnPredictionService:
    """
    Production service for churn prediction.

    Loads trained model and provides prediction capabilities with
    feature calculation, risk scoring, and interpretability.
    """

    # Risk level thresholds (churn probability)
    RISK_THRESHOLDS = {
        'LOW': 0.3,        # < 30% probability
        'MEDIUM': 0.5,     # 30-50% probability
        'HIGH': 0.7,       # 50-70% probability
        'CRITICAL': 1.0    # > 70% probability
    }

    # Composite churn score thresholds (0-100 scale)
    SCORE_THRESHOLDS = {
        'LOW': 40,
        'MEDIUM': 60,
        'HIGH': 80,
        'CRITICAL': 100
    }

    def __init__(
        self,
        model_path: str,
        feature_engineer: Optional[ChurnFeatureEngineer] = None
    ):
        """
        Initialize prediction service.

        Args:
            model_path: Path to trained model pickle file
            feature_engineer: Optional feature engineer (creates new one if None)
        """
        self.model_path = Path(model_path)
        self.model = None
        self.feature_names = None
        self.model_version = None
        self.feature_engineer = feature_engineer or ChurnFeatureEngineer()

        # Load model on initialization
        self._load_model()

    def _load_model(self) -> None:
        """Load trained model from disk."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        try:
            with open(self.model_path, 'rb') as f:
                model_data = pickle.load(f)

            # Extract model and metadata
            if isinstance(model_data, dict):
                self.model = model_data.get('model')
                self.feature_names = model_data.get('feature_names')
                self.model_version = model_data.get('version', 'unknown')
            else:
                # Legacy format: just the model
                self.model = model_data
                self.feature_names = None
                self.model_version = 'legacy'

            logger.info(f"Loaded model from {self.model_path}")
            logger.info(f"Model version: {self.model_version}")
            if self.feature_names:
                logger.info(f"Model expects {len(self.feature_names)} features")

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise

    def predict_tutor(
        self,
        tutor_id: str,
        tutors_df: pd.DataFrame,
        sessions_df: pd.DataFrame,
        feedback_df: pd.DataFrame,
        include_explanation: bool = False
    ) -> Dict[str, Any]:
        """
        Make churn prediction for a single tutor.

        Args:
            tutor_id: Tutor ID to predict
            tutors_df: Tutor profiles dataframe
            sessions_df: Sessions dataframe
            feedback_df: Feedback dataframe
            include_explanation: Whether to include SHAP explanation

        Returns:
            Dictionary with prediction results
        """
        # Filter data for this tutor
        tutor_df = tutors_df[tutors_df['tutor_id'] == tutor_id].copy()
        if tutor_df.empty:
            raise ValueError(f"Tutor {tutor_id} not found")

        tutor_sessions = sessions_df[sessions_df['tutor_id'] == tutor_id].copy()
        tutor_feedback = feedback_df[feedback_df['tutor_id'] == tutor_id].copy()

        # Calculate features
        features_df = self.feature_engineer.create_features(
            tutor_df,
            tutor_sessions,
            tutor_feedback
        )

        # Make prediction
        prediction_result = self._predict_from_features(
            features_df,
            include_explanation=include_explanation
        )

        # Add tutor context
        prediction_result['tutor_id'] = tutor_id
        prediction_result['tutor_name'] = tutor_df.iloc[0]['name']
        prediction_result['tutor_status'] = tutor_df.iloc[0]['status']
        prediction_result['prediction_date'] = datetime.now().isoformat()

        return prediction_result

    def predict_batch(
        self,
        tutors_df: pd.DataFrame,
        sessions_df: pd.DataFrame,
        feedback_df: pd.DataFrame,
        include_explanation: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Make churn predictions for multiple tutors.

        Args:
            tutors_df: Tutor profiles dataframe
            sessions_df: Sessions dataframe
            feedback_df: Feedback dataframe
            include_explanation: Whether to include SHAP explanations

        Returns:
            List of prediction results for each tutor
        """
        logger.info(f"Starting batch prediction for {len(tutors_df)} tutors")

        # Calculate features for all tutors
        features_df = self.feature_engineer.create_features(
            tutors_df,
            sessions_df,
            feedback_df
        )

        # Make predictions
        results = []
        for idx, row in features_df.iterrows():
            tutor_id = row['tutor_id']
            tutor_features = features_df[features_df['tutor_id'] == tutor_id]

            # Get prediction
            prediction = self._predict_from_features(
                tutor_features,
                include_explanation=include_explanation
            )

            # Add tutor context
            tutor_info = tutors_df[tutors_df['tutor_id'] == tutor_id].iloc[0]
            prediction['tutor_id'] = tutor_id
            prediction['tutor_name'] = tutor_info['name']
            prediction['tutor_status'] = tutor_info['status']
            prediction['prediction_date'] = datetime.now().isoformat()

            results.append(prediction)

        logger.info(f"Completed batch prediction: {len(results)} results")
        return results

    def _predict_from_features(
        self,
        features_df: pd.DataFrame,
        include_explanation: bool = False
    ) -> Dict[str, Any]:
        """
        Make prediction from calculated features.

        Args:
            features_df: Features dataframe (single row)
            include_explanation: Whether to include SHAP explanation

        Returns:
            Dictionary with prediction results
        """
        if len(features_df) != 1:
            raise ValueError("Expected single row of features")

        # Prepare feature matrix
        X = features_df.drop(columns=['tutor_id'], errors='ignore')

        # Align with training features if available
        if self.feature_names:
            # Ensure columns match training
            missing_cols = set(self.feature_names) - set(X.columns)
            if missing_cols:
                logger.warning(f"Missing features: {missing_cols}")
                # Add missing columns with zeros
                for col in missing_cols:
                    X[col] = 0

            # Select and order columns
            X = X[self.feature_names]

        # Make prediction
        churn_probability = self.model.predict_proba(X)[0, 1]
        churn_prediction = int(churn_probability >= 0.5)

        # Calculate composite churn score (0-100 scale)
        churn_score = int(churn_probability * 100)

        # Determine risk level
        risk_level = self._calculate_risk_level(churn_probability)

        # Build result
        result = {
            'churn_probability': float(churn_probability),
            'churn_prediction': churn_prediction,
            'churn_score': churn_score,
            'risk_level': risk_level,
            'model_version': self.model_version,
        }

        # Add feature importance if requested
        if include_explanation:
            explanation = self._generate_explanation(X)
            result['contributing_factors'] = explanation

        return result

    def _calculate_risk_level(self, probability: float) -> str:
        """
        Calculate risk level from churn probability.

        Args:
            probability: Churn probability (0-1)

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

    def _generate_explanation(self, X: pd.DataFrame) -> Dict[str, float]:
        """
        Generate simple feature importance explanation.

        For production SHAP explanations, use TreeExplainer from interpretability module.
        This provides a lightweight alternative using feature importances.

        Args:
            X: Feature dataframe (single row)

        Returns:
            Dictionary of top contributing factors
        """
        try:
            # Get feature importances from model
            if hasattr(self.model, 'feature_importances_'):
                importances = self.model.feature_importances_
                feature_names = X.columns

                # Create importance dictionary
                feature_importance = dict(zip(feature_names, importances))

                # Get top 5 factors
                top_factors = dict(
                    sorted(
                        feature_importance.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:5]
                )

                # Add feature values
                result = {}
                for feature, importance in top_factors.items():
                    result[feature] = {
                        'importance': float(importance),
                        'value': float(X[feature].iloc[0])
                    }

                return result
            else:
                return {}

        except Exception as e:
            logger.warning(f"Failed to generate explanation: {e}")
            return {}

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model metadata and configuration.

        Returns:
            Dictionary with model information
        """
        return {
            'model_path': str(self.model_path),
            'model_version': self.model_version,
            'model_type': type(self.model).__name__,
            'feature_count': len(self.feature_names) if self.feature_names else 'unknown',
            'risk_thresholds': self.RISK_THRESHOLDS,
            'score_thresholds': self.SCORE_THRESHOLDS,
        }


def load_prediction_service(
    model_path: str = "output/models/churn_model.pkl"
) -> ChurnPredictionService:
    """
    Factory function to create prediction service.

    Args:
        model_path: Path to trained model

    Returns:
        Initialized ChurnPredictionService
    """
    return ChurnPredictionService(model_path)
