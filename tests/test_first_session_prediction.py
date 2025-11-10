"""
Tests for first session success prediction system.

Tests:
- Model training and evaluation
- Prediction service functionality
- Email alert generation
- Database operations
- API endpoints
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import joblib

from src.evaluation.first_session_model_training import (
    FirstSessionModelTrainer,
    train_first_session_model
)
from src.evaluation.first_session_prediction_service import FirstSessionPredictionService
from src.evaluation.first_session_email_service import FirstSessionEmailService


@pytest.fixture
def sample_tutors_df():
    """Create sample tutor data."""
    return pd.DataFrame({
        'tutor_id': ['T001', 'T002', 'T003'],
        'name': ['Alice', 'Bob', 'Carol'],
        'email': ['alice@example.com', 'bob@example.com', 'carol@example.com'],
        'onboarding_date': [
            datetime.now() - timedelta(days=365),
            datetime.now() - timedelta(days=30),
            datetime.now() - timedelta(days=180)
        ],
        'status': ['active', 'active', 'active'],
        'subjects': [['Math'], ['Science'], ['Math', 'Science']],
        'education_level': ['Bachelor', 'Master', 'PhD'],
        'location': ['NYC', 'LA', 'Chicago'],
        'baseline_sessions_per_week': [5.0, 3.0, 4.0],
        'behavioral_archetype': ['high_performer', 'new_tutor', 'steady']
    })


@pytest.fixture
def sample_sessions_df():
    """Create sample session data."""
    sessions = []

    # Create sessions for each tutor
    for tutor_id in ['T001', 'T002', 'T003']:
        for i in range(1, 6):  # 5 sessions each
            session_date = datetime.now() - timedelta(days=30-i*2)
            sessions.append({
                'session_id': f'S_{tutor_id}_{i}',
                'tutor_id': tutor_id,
                'student_id': f'ST_{tutor_id}_{i}',
                'session_number': i,
                'scheduled_start': session_date,
                'actual_start': session_date,
                'duration_minutes': 60,
                'subject': 'Math' if i % 2 == 0 else 'Science',
                'session_type': '1-on-1',
                'tutor_initiated_reschedule': False,
                'no_show': False,
                'late_start_minutes': 0,
                'engagement_score': 0.8 + (i * 0.02),
                'learning_objectives_met': True,
                'technical_issues': False
            })

    return pd.DataFrame(sessions)


@pytest.fixture
def sample_feedback_df(sample_sessions_df):
    """Create sample feedback data."""
    feedback = []

    for _, session in sample_sessions_df.iterrows():
        # First sessions have varied ratings
        if session['session_number'] == 1:
            rating = np.random.choice([2, 3, 4, 5], p=[0.1, 0.2, 0.4, 0.3])
        else:
            rating = np.random.choice([3, 4, 5], p=[0.2, 0.5, 0.3])

        feedback.append({
            'feedback_id': f"F_{session['session_id']}",
            'session_id': session['session_id'],
            'student_id': session['student_id'],
            'tutor_id': session['tutor_id'],
            'overall_rating': rating,
            'is_first_session': session['session_number'] == 1,
            'subject_knowledge_rating': rating,
            'communication_rating': rating,
            'patience_rating': rating,
            'engagement_rating': rating,
            'helpfulness_rating': rating,
            'would_recommend': rating >= 3,
            'improvement_areas': [],
            'free_text_feedback': 'Good session',
            'submitted_at': session['scheduled_start'] + timedelta(hours=1)
        })

    return pd.DataFrame(feedback)


class TestFirstSessionModelTrainer:
    """Tests for model training."""

    def test_feature_creation(self, sample_tutors_df, sample_sessions_df, sample_feedback_df):
        """Test feature engineering."""
        trainer = FirstSessionModelTrainer()

        features_df = trainer.create_features(
            sample_tutors_df,
            sample_sessions_df,
            sample_feedback_df
        )

        # Check features created
        assert len(features_df) > 0
        assert 'poor_first_session' in features_df.columns
        assert 'tenure_days' in features_df.columns
        assert 'avg_rating' in features_df.columns
        assert 'first_session_success_rate' in features_df.columns

        # Check target distribution
        assert features_df['poor_first_session'].isin([0, 1]).all()

    def test_data_preparation(self, sample_tutors_df, sample_sessions_df, sample_feedback_df):
        """Test train/test split."""
        trainer = FirstSessionModelTrainer(test_size=0.3, random_state=42)

        features_df = trainer.create_features(
            sample_tutors_df,
            sample_sessions_df,
            sample_feedback_df
        )

        X_train, X_test, y_train, y_test = trainer.prepare_data(features_df)

        # Check split proportions
        total = len(X_train) + len(X_test)
        assert len(X_test) / total == pytest.approx(0.3, abs=0.1)

        # Check feature names stored
        assert trainer.feature_names is not None
        assert len(trainer.feature_names) > 0

    def test_model_training(self, sample_tutors_df, sample_sessions_df, sample_feedback_df):
        """Test model training."""
        trainer = FirstSessionModelTrainer(random_state=42)

        features_df = trainer.create_features(
            sample_tutors_df,
            sample_sessions_df,
            sample_feedback_df
        )

        X_train, X_test, y_train, y_test = trainer.prepare_data(features_df)

        # Train model
        model = trainer.train(X_train, y_train, C=1.0)

        # Check model trained
        assert model is not None
        assert trainer.model is not None
        assert trainer.scaler is not None

        # Check coefficients
        assert len(model.coef_[0]) == len(trainer.feature_names)

    def test_model_evaluation(self, sample_tutors_df, sample_sessions_df, sample_feedback_df):
        """Test model evaluation."""
        trainer = FirstSessionModelTrainer(random_state=42)

        features_df = trainer.create_features(
            sample_tutors_df,
            sample_sessions_df,
            sample_feedback_df
        )

        X_train, X_test, y_train, y_test = trainer.prepare_data(features_df)
        trainer.train(X_train, y_train)

        # Evaluate
        results = trainer.evaluate(X_test, y_test)

        # Check metrics present
        assert 'accuracy' in results
        assert 'precision' in results
        assert 'recall' in results
        assert 'f1_score' in results
        assert 'auc_roc' in results

        # Check metrics in valid range
        assert 0 <= results['accuracy'] <= 1
        assert 0 <= results['precision'] <= 1
        assert 0 <= results['recall'] <= 1

    def test_feature_importance(self, sample_tutors_df, sample_sessions_df, sample_feedback_df):
        """Test feature importance extraction."""
        trainer = FirstSessionModelTrainer(random_state=42)

        features_df = trainer.create_features(
            sample_tutors_df,
            sample_sessions_df,
            sample_feedback_df
        )

        X_train, X_test, y_train, y_test = trainer.prepare_data(features_df)
        trainer.train(X_train, y_train)

        # Get importance
        importance_df = trainer.get_feature_importance(top_n=10)

        # Check output
        assert len(importance_df) > 0
        assert 'feature' in importance_df.columns
        assert 'coefficient' in importance_df.columns

    def test_model_save_load(self, sample_tutors_df, sample_sessions_df, sample_feedback_df):
        """Test model persistence."""
        trainer = FirstSessionModelTrainer(random_state=42)

        features_df = trainer.create_features(
            sample_tutors_df,
            sample_sessions_df,
            sample_feedback_df
        )

        X_train, X_test, y_train, y_test = trainer.prepare_data(features_df)
        trainer.train(X_train, y_train)

        # Save model
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "test_model.pkl"

            trainer.save_model(str(model_path))

            # Check file created
            assert model_path.exists()

            # Load model
            loaded_model, loaded_scaler, loaded_features = FirstSessionModelTrainer.load_model(str(model_path))

            # Check loaded correctly
            assert loaded_model is not None
            assert loaded_scaler is not None
            assert loaded_features == trainer.feature_names


class TestFirstSessionPredictionService:
    """Tests for prediction service."""

    @pytest.fixture
    def trained_model_path(self, sample_tutors_df, sample_sessions_df, sample_feedback_df):
        """Create and save a trained model for testing."""
        trainer = FirstSessionModelTrainer(random_state=42)

        features_df = trainer.create_features(
            sample_tutors_df,
            sample_sessions_df,
            sample_feedback_df
        )

        X_train, X_test, y_train, y_test = trainer.prepare_data(features_df)
        trainer.train(X_train, y_train)

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as f:
            trainer.save_model(f.name)
            return f.name

    def test_service_initialization(self, trained_model_path):
        """Test service initialization."""
        service = FirstSessionPredictionService(trained_model_path)

        # Check model loaded
        assert service.model is not None
        assert service.scaler is not None
        assert service.feature_names is not None

    def test_single_session_prediction(
        self,
        trained_model_path,
        sample_tutors_df,
        sample_sessions_df,
        sample_feedback_df
    ):
        """Test single session prediction."""
        service = FirstSessionPredictionService(trained_model_path)

        # Predict for upcoming session
        prediction = service.predict_session(
            session_id='S_TEST_001',
            tutor_id='T001',
            student_id='ST_TEST_001',
            scheduled_start=datetime.now() + timedelta(hours=2),
            subject='Math',
            tutors_df=sample_tutors_df,
            sessions_df=sample_sessions_df,
            feedback_df=sample_feedback_df,
            student_age=12
        )

        # Check prediction structure
        assert 'risk_probability' in prediction
        assert 'risk_score' in prediction
        assert 'risk_level' in prediction
        assert 'should_send_alert' in prediction

        # Check values in valid range
        assert 0 <= prediction['risk_probability'] <= 1
        assert 0 <= prediction['risk_score'] <= 100
        assert prediction['risk_level'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

    def test_risk_level_calculation(self, trained_model_path):
        """Test risk level classification."""
        service = FirstSessionPredictionService(trained_model_path)

        # Test thresholds
        assert service._calculate_risk_level(0.1) == 'LOW'
        assert service._calculate_risk_level(0.4) == 'MEDIUM'
        assert service._calculate_risk_level(0.6) == 'HIGH'
        assert service._calculate_risk_level(0.8) == 'CRITICAL'

    def test_model_info(self, trained_model_path):
        """Test model info retrieval."""
        service = FirstSessionPredictionService(trained_model_path)

        info = service.get_model_info()

        # Check info structure
        assert 'model_version' in info
        assert 'model_type' in info
        assert 'feature_count' in info
        assert 'risk_thresholds' in info


class TestFirstSessionEmailService:
    """Tests for email service."""

    @pytest.fixture
    def email_service(self):
        """Create email service for testing."""
        # Mock SMTP settings
        return FirstSessionEmailService(
            smtp_host='smtp.example.com',
            smtp_port=587,
            smtp_user='test@example.com',
            smtp_password='password',
            smtp_use_tls=True
        )

    def test_prep_tips_generation(self, email_service):
        """Test preparation tips generation."""
        risk_factors = {
            'first_session_success_rate': {'value': 0.5, 'coefficient': 0.3},
            'avg_rating': {'value': 3.5, 'coefficient': 0.2},
            'tenure_days': {'value': 50, 'coefficient': 0.1}
        }

        tips_html = email_service._generate_prep_tips(
            risk_factors,
            student_age=10,
            subject='Math'
        )

        # Check tips generated
        assert isinstance(tips_html, str)
        assert len(tips_html) > 0
        assert '<ul>' in tips_html
        assert '<li>' in tips_html

    def test_alert_email_structure(self, email_service, monkeypatch):
        """Test alert email structure."""
        # Mock the _send_email method to capture email content
        sent_emails = []

        def mock_send(to_email, subject, html_body, text_body):
            sent_emails.append({
                'to': to_email,
                'subject': subject,
                'html': html_body,
                'text': text_body
            })
            return True

        monkeypatch.setattr(email_service, '_send_email', mock_send)

        # Send alert
        result = email_service.send_first_session_alert(
            tutor_email='tutor@example.com',
            tutor_name='John Doe',
            student_name='Jane Student',
            student_age=12,
            session_date=datetime.now() + timedelta(hours=3),
            subject='Math',
            risk_score=70,
            risk_level='HIGH',
            top_risk_factors={
                'avg_rating': {'value': 3.5, 'coefficient': 0.3}
            },
            session_id='S_TEST_001'
        )

        # Check email sent
        assert result is True
        assert len(sent_emails) == 1

        email = sent_emails[0]
        assert email['to'] == 'tutor@example.com'
        assert 'First Session' in email['subject']
        assert 'Jane Student' in email['html']
        assert 'Math' in email['html']
        assert 'HIGH' in email['html']


class TestIntegration:
    """Integration tests."""

    def test_end_to_end_prediction_flow(
        self,
        sample_tutors_df,
        sample_sessions_df,
        sample_feedback_df
    ):
        """Test complete prediction workflow."""
        # 1. Train model
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "model.pkl"

            trainer = FirstSessionModelTrainer(random_state=42)
            features_df = trainer.create_features(
                sample_tutors_df,
                sample_sessions_df,
                sample_feedback_df
            )

            X_train, X_test, y_train, y_test = trainer.prepare_data(features_df)
            trainer.train(X_train, y_train)
            trainer.save_model(str(model_path))

            # 2. Load prediction service
            service = FirstSessionPredictionService(str(model_path))

            # 3. Make prediction
            prediction = service.predict_session(
                session_id='S_TEST_001',
                tutor_id='T001',
                student_id='ST_TEST_001',
                scheduled_start=datetime.now() + timedelta(hours=2),
                subject='Math',
                tutors_df=sample_tutors_df,
                sessions_df=sample_sessions_df,
                feedback_df=sample_feedback_df,
                student_age=12
            )

            # 4. Verify prediction
            assert prediction is not None
            assert 'risk_probability' in prediction
            assert 'risk_level' in prediction

            # 5. Check alert decision
            should_alert = prediction['should_send_alert']
            assert isinstance(should_alert, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
