"""
First Session Success Prediction Model Training.

Implements logistic regression model to predict poor first session experiences
(rating < 3) and trigger pre-session alerts.

Features:
- Logistic regression (scikit-learn) for interpretability
- Comprehensive feature engineering
- Cross-validation for robustness
- Model evaluation and persistence
"""

from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    roc_auc_score,
    precision_recall_curve,
    average_precision_score,
    classification_report,
    confusion_matrix,
    roc_curve,
    f1_score,
    precision_score,
    recall_score,
)
import joblib
import json
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FirstSessionModelTrainer:
    """
    Train and evaluate logistic regression model for first session success prediction.

    Predicts likelihood of first session rating < 3 to enable proactive interventions.
    """

    # Classification threshold optimized for high-risk detection
    DEFAULT_THRESHOLD = 0.5  # Can be adjusted based on precision/recall tradeoff

    def __init__(
        self,
        test_size: float = 0.2,
        random_state: int = 42,
        cv_folds: int = 5
    ):
        """
        Initialize model trainer.

        Args:
            test_size: Proportion of data for testing
            random_state: Random seed for reproducibility
            cv_folds: Number of cross-validation folds
        """
        self.test_size = test_size
        self.random_state = random_state
        self.cv_folds = cv_folds
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.evaluation_results = {}

    def create_features(
        self,
        tutors_df: pd.DataFrame,
        sessions_df: pd.DataFrame,
        feedback_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Create features for first session prediction.

        Features include:
        - Tutor tenure (days since onboarding)
        - Average rating (excluding first sessions)
        - Historical first session success rate
        - Engagement score
        - Time of day (hour of day)
        - Subject (one-hot encoded)
        - Student age
        - Reschedule rate
        - Session count

        Args:
            tutors_df: Tutor profiles
            sessions_df: All sessions
            feedback_df: All feedback

        Returns:
            Feature dataframe with target variable
        """
        print("=" * 70)
        print("FEATURE ENGINEERING - FIRST SESSION PREDICTION")
        print("=" * 70)

        # Filter for first sessions only
        first_sessions = sessions_df[sessions_df['session_number'] == 1].copy()

        # Join with feedback
        first_sessions = first_sessions.merge(
            feedback_df[['session_id', 'overall_rating', 'is_first_session']],
            on='session_id',
            how='left'
        )

        # Filter to sessions with feedback
        first_sessions = first_sessions[first_sessions['overall_rating'].notna()].copy()

        print(f"\nFound {len(first_sessions):,} first sessions with feedback")

        # Create target variable: poor_first_session = 1 if rating < 3
        first_sessions['poor_first_session'] = (first_sessions['overall_rating'] < 3).astype(int)

        # Calculate poor session rate
        poor_rate = first_sessions['poor_first_session'].mean()
        print(f"Poor first session rate (rating < 3): {poor_rate:.2%}")

        features_list = []

        for _, session in first_sessions.iterrows():
            tutor_id = session['tutor_id']
            session_date = session['scheduled_start']

            # Get tutor info
            tutor = tutors_df[tutors_df['tutor_id'] == tutor_id].iloc[0]

            # --- Tutor Profile Features ---

            # Tutor tenure (days since onboarding)
            tenure_days = (session_date - tutor['onboarding_date']).days

            # --- Historical Performance Features ---

            # Get prior sessions (before this one)
            prior_sessions = sessions_df[
                (sessions_df['tutor_id'] == tutor_id) &
                (sessions_df['scheduled_start'] < session_date)
            ].copy()

            # Get prior feedback
            prior_feedback = feedback_df[
                feedback_df['session_id'].isin(prior_sessions['session_id'])
            ].copy()

            # Average rating (from prior sessions)
            if len(prior_feedback) > 0:
                avg_rating = prior_feedback['overall_rating'].mean()
            else:
                avg_rating = 3.0  # Default/neutral

            # First session success rate (from prior first sessions)
            prior_first_sessions = prior_sessions[prior_sessions['session_number'] == 1]
            prior_first_feedback = feedback_df[
                feedback_df['session_id'].isin(prior_first_sessions['session_id'])
            ]

            if len(prior_first_feedback) > 0:
                first_session_success_rate = (prior_first_feedback['overall_rating'] >= 3).mean()
            else:
                first_session_success_rate = 0.5  # Default/neutral

            # Engagement score (from prior sessions)
            if len(prior_sessions) > 0:
                engagement_score = prior_sessions['engagement_score'].mean()
                if pd.isna(engagement_score):
                    engagement_score = 0.5  # Default
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

            # Time of day (hour)
            hour_of_day = session_date.hour

            # Day of week (0=Monday, 6=Sunday)
            day_of_week = session_date.weekday()

            # Subject
            subject = session['subject']

            # Student age (from session)
            student_id = session['student_id']
            student = sessions_df[sessions_df['student_id'] == student_id].iloc[0]
            # We need to merge with students table, but for now use a default
            student_age = 12  # Default age

            # Build feature row
            feature_row = {
                'session_id': session['session_id'],
                'tutor_id': tutor_id,
                'tenure_days': tenure_days,
                'avg_rating': avg_rating,
                'first_session_success_rate': first_session_success_rate,
                'engagement_score': engagement_score,
                'reschedule_rate': reschedule_rate,
                'no_show_rate': no_show_rate,
                'session_count': session_count,
                'hour_of_day': hour_of_day,
                'day_of_week': day_of_week,
                'student_age': student_age,
                'subject': subject,
                'poor_first_session': session['poor_first_session']
            }

            features_list.append(feature_row)

        # Convert to dataframe
        features_df = pd.DataFrame(features_list)

        # Check if we have any data
        if len(features_df) == 0:
            raise ValueError("No first sessions with feedback found. Cannot create features.")

        # One-hot encode subject
        subject_dummies = pd.get_dummies(features_df['subject'], prefix='subject')
        features_df = pd.concat([features_df, subject_dummies], axis=1)
        features_df = features_df.drop(columns=['subject'])

        # Cyclical encoding for time features
        features_df['hour_sin'] = np.sin(2 * np.pi * features_df['hour_of_day'] / 24)
        features_df['hour_cos'] = np.cos(2 * np.pi * features_df['hour_of_day'] / 24)
        features_df['day_sin'] = np.sin(2 * np.pi * features_df['day_of_week'] / 7)
        features_df['day_cos'] = np.cos(2 * np.pi * features_df['day_of_week'] / 7)

        features_df = features_df.drop(columns=['hour_of_day', 'day_of_week'])

        print(f"\nCreated {len(features_df)} feature rows with {len(features_df.columns)-3} features")
        print(f"Features: {[c for c in features_df.columns if c not in ['session_id', 'tutor_id', 'poor_first_session']]}")

        return features_df

    def prepare_data(
        self,
        features_df: pd.DataFrame,
        target_col: str = 'poor_first_session'
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Prepare data for training and testing.

        Args:
            features_df: Feature matrix with target column
            target_col: Name of target column

        Returns:
            X_train, X_test, y_train, y_test
        """
        print("\n" + "=" * 70)
        print("DATA PREPARATION")
        print("=" * 70)

        # Separate features and target
        X = features_df.drop(columns=[target_col, 'session_id', 'tutor_id'], errors='ignore')
        y = features_df[target_col].astype(int)

        # Store feature names
        self.feature_names = X.columns.tolist()

        print(f"\nDataset info:")
        print(f"  Total samples: {len(X):,}")
        print(f"  Features: {len(X.columns)}")
        print(f"  Poor session rate: {y.mean():.2%}")
        print(f"  Class balance: {y.value_counts().to_dict()}")

        # Stratified train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=y
        )

        print(f"\nTrain/test split:")
        print(f"  Train samples: {len(X_train):,} (poor rate: {y_train.mean():.2%})")
        print(f"  Test samples: {len(X_test):,} (poor rate: {y_test.mean():.2%})")

        return X_train, X_test, y_train, y_test

    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        C: float = 1.0,
        max_iter: int = 1000
    ) -> LogisticRegression:
        """
        Train logistic regression model with cross-validation.

        Args:
            X_train: Training features
            y_train: Training labels
            C: Inverse regularization strength
            max_iter: Maximum iterations

        Returns:
            Trained logistic regression model
        """
        print("\n" + "=" * 70)
        print("MODEL TRAINING - LOGISTIC REGRESSION")
        print("=" * 70)

        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)

        # Calculate class weights for imbalanced data
        class_weight = {
            0: 1.0,
            1: len(y_train) / (2 * (y_train == 1).sum())  # Balance classes
        }

        print(f"\nConfiguration:")
        print(f"  Regularization (C): {C}")
        print(f"  Class weights: {class_weight}")
        print(f"  Max iterations: {max_iter}")

        # Cross-validation
        print(f"\nPerforming {self.cv_folds}-fold cross-validation...")

        cv = StratifiedKFold(
            n_splits=self.cv_folds,
            shuffle=True,
            random_state=self.random_state
        )

        model = LogisticRegression(
            C=C,
            class_weight=class_weight,
            max_iter=max_iter,
            random_state=self.random_state,
            solver='lbfgs'
        )

        # CV scores
        cv_scores = cross_val_score(
            model, X_train_scaled, y_train,
            cv=cv,
            scoring='roc_auc',
            n_jobs=-1
        )

        print(f"\nCross-validation results:")
        print(f"  Mean AUC-ROC: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        print(f"  Fold scores: {cv_scores}")

        # Train final model
        print(f"\nTraining final model on full training set...")
        model.fit(X_train_scaled, y_train)

        self.model = model
        self.evaluation_results['cv_auc_roc'] = cv_scores.mean()
        self.evaluation_results['cv_auc_std'] = cv_scores.std()

        print(f"\n✓ Model trained successfully")

        return model

    def evaluate(
        self,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Evaluate trained model on test set.

        Args:
            X_test: Test features
            y_test: Test labels
            threshold: Classification threshold

        Returns:
            Dictionary of evaluation metrics
        """
        print("\n" + "=" * 70)
        print("MODEL EVALUATION")
        print("=" * 70)

        if self.model is None or self.scaler is None:
            raise ValueError("Model must be trained before evaluation")

        # Scale test features
        X_test_scaled = self.scaler.transform(X_test)

        # Get predictions
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        y_pred = (y_pred_proba >= threshold).astype(int)

        # Calculate metrics
        auc_roc = roc_auc_score(y_test, y_pred_proba)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)

        # Precision-Recall curve
        avg_precision = average_precision_score(y_test, y_pred_proba)

        # Classification report
        class_report = classification_report(y_test, y_pred, output_dict=True)

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()

        # Store results
        results = {
            'auc_roc': float(auc_roc),
            'avg_precision': float(avg_precision),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'accuracy': float(class_report['accuracy']),
            'confusion_matrix': {
                'tn': int(tn), 'fp': int(fp),
                'fn': int(fn), 'tp': int(tp)
            },
            'classification_report': class_report,
            'threshold': threshold
        }

        self.evaluation_results.update(results)

        # Print results
        print(f"\nTest Set Performance:")
        print(f"  AUC-ROC: {auc_roc:.4f} (target: > 0.75)")
        print(f"  Precision (high-risk): {precision:.4f} (target: > 0.60)")
        print(f"  Recall (high-risk): {recall:.4f}")
        print(f"  F1-Score: {f1:.4f}")
        print(f"  Accuracy: {class_report['accuracy']:.4f}")

        print(f"\nConfusion Matrix:")
        print(f"  True Negatives:  {tn:4d}  |  False Positives: {fp:4d}")
        print(f"  False Negatives: {fn:4d}  |  True Positives:  {tp:4d}")

        # Check if meets success criteria
        meets_auc = auc_roc > 0.75
        meets_precision = precision > 0.60

        print(f"\nSuccess Criteria:")
        print(f"  ✓ AUC-ROC > 0.75: {meets_auc} ({auc_roc:.4f})")
        print(f"  ✓ Precision > 0.60: {meets_precision} ({precision:.4f})")

        return results

    def get_feature_importance(self, top_n: int = 15) -> pd.DataFrame:
        """
        Get feature importance (coefficients) from trained model.

        Args:
            top_n: Number of top features to return

        Returns:
            DataFrame with feature importances
        """
        if self.model is None:
            raise ValueError("Model must be trained before getting feature importance")

        # Get coefficients
        coefficients = self.model.coef_[0]

        # Create dataframe
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'coefficient': coefficients,
            'abs_coefficient': np.abs(coefficients)
        }).sort_values('abs_coefficient', ascending=False)

        print(f"\nTop {top_n} Most Important Features:")
        print("=" * 70)
        for i, row in importance_df.head(top_n).iterrows():
            direction = "increases" if row['coefficient'] > 0 else "decreases"
            print(f"  {row['feature']:35s} {row['coefficient']:+.4f} ({direction} risk)")

        self.evaluation_results['feature_importance'] = importance_df.to_dict('records')

        return importance_df

    def save_model(
        self,
        model_path: str,
        results_path: Optional[str] = None
    ):
        """
        Save trained model and evaluation results.

        Args:
            model_path: Path to save model
            results_path: Optional path to save evaluation results JSON
        """
        print("\n" + "=" * 70)
        print("SAVING MODEL")
        print("=" * 70)

        if self.model is None or self.scaler is None:
            raise ValueError("Model must be trained before saving")

        # Create directory if needed
        model_path = Path(model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)

        # Save model and scaler
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat(),
            'model_type': 'first_session_prediction'
        }

        joblib.dump(model_data, model_path)

        print(f"\n✓ Model saved to: {model_path}")

        # Save results if path provided
        if results_path:
            results_path = Path(results_path)
            results_path.parent.mkdir(parents=True, exist_ok=True)

            with open(results_path, 'w') as f:
                json.dump(self.evaluation_results, f, indent=2)

            print(f"✓ Evaluation results saved to: {results_path}")

    @staticmethod
    def load_model(model_path: str) -> Tuple[LogisticRegression, StandardScaler, List[str]]:
        """
        Load saved model.

        Args:
            model_path: Path to saved model

        Returns:
            Tuple of (model, scaler, feature_names)
        """
        model_data = joblib.load(model_path)

        return (
            model_data['model'],
            model_data['scaler'],
            model_data['feature_names']
        )


def train_first_session_model(
    tutors_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    feedback_df: pd.DataFrame,
    output_dir: str = "output/models/first_session",
    test_size: float = 0.2,
    cv_folds: int = 5
) -> Tuple[LogisticRegression, Dict[str, Any]]:
    """
    Convenience function to train first session prediction model.

    Args:
        tutors_df: Tutor profiles
        sessions_df: Sessions dataframe
        feedback_df: Feedback dataframe
        output_dir: Directory to save model and results
        test_size: Proportion for test set
        cv_folds: Number of CV folds

    Returns:
        Tuple of (trained_model, evaluation_results)
    """
    # Initialize trainer
    trainer = FirstSessionModelTrainer(
        test_size=test_size,
        random_state=42,
        cv_folds=cv_folds
    )

    # Create features
    features_df = trainer.create_features(tutors_df, sessions_df, feedback_df)

    # Prepare data
    X_train, X_test, y_train, y_test = trainer.prepare_data(features_df)

    # Train model
    model = trainer.train(X_train, y_train)

    # Evaluate
    results = trainer.evaluate(X_test, y_test)

    # Get feature importance
    trainer.get_feature_importance(top_n=15)

    # Save model and results
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    trainer.save_model(
        model_path=output_path / "first_session_model.pkl",
        results_path=output_path / "evaluation_results.json"
    )

    print("\n" + "=" * 70)
    print("TRAINING COMPLETE!")
    print("=" * 70)
    print(f"\nModel ready for deployment")
    print(f"Test AUC-ROC: {results['auc_roc']:.4f}")
    print(f"Test Precision: {results['precision']:.4f}")

    return model, trainer.evaluation_results


if __name__ == "__main__":
    # Demo execution
    from sqlalchemy import create_engine

    # Database connection
    DATABASE_URL = "postgresql://tutormax:tutormax_dev@localhost:5432/tutormax"
    engine = create_engine(DATABASE_URL)

    print("Loading data from database...")
    tutors_df = pd.read_sql("SELECT * FROM tutors", engine)
    sessions_df = pd.read_sql("SELECT * FROM sessions", engine)
    feedback_df = pd.read_sql("SELECT * FROM student_feedback", engine)

    print(f"Loaded {len(tutors_df):,} tutors, {len(sessions_df):,} sessions, {len(feedback_df):,} feedback")

    # Train model
    model, results = train_first_session_model(
        tutors_df,
        sessions_df,
        feedback_df,
        output_dir="output/models/first_session",
        test_size=0.2,
        cv_folds=5
    )
