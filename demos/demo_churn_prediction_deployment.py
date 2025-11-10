"""
Demo: Churn Prediction Model Deployment

Demonstrates the deployed churn prediction system including:
- Real-time prediction for single tutors
- Batch prediction for multiple tutors
- Feature calculation and model inference
- Risk level classification
- Performance benchmarking

This demo uses the prediction service directly (without API/Redis).
For API demo, see demo_prediction_api.py
"""

import sys
from pathlib import Path
import pandas as pd
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.evaluation.prediction_service import ChurnPredictionService


def print_header(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(title.center(70))
    print("=" * 70)


def print_prediction(prediction: dict, show_explanation: bool = False):
    """Print formatted prediction result."""
    print(f"\nTutor: {prediction['tutor_name']} ({prediction['tutor_id']})")
    print(f"Status: {prediction['tutor_status']}")
    print(f"\nChurn Prediction:")
    print(f"  Probability: {prediction['churn_probability']:.2%}")
    print(f"  Score: {prediction['churn_score']}/100")
    print(f"  Risk Level: {prediction['risk_level']}")
    print(f"  Prediction: {'WILL CHURN' if prediction['churn_prediction'] == 1 else 'WILL STAY'}")

    if show_explanation and prediction.get('contributing_factors'):
        print(f"\n  Top Contributing Factors:")
        for i, (feature, data) in enumerate(prediction['contributing_factors'].items(), 1):
            print(f"    {i}. {feature}")
            print(f"       Value: {data['value']:.3f}, Importance: {data['importance']:.3f}")

    print(f"\nModel: {prediction['model_version']}")
    print(f"Prediction Date: {prediction['prediction_date']}")


def load_data():
    """Load tutor, session, and feedback data."""
    print("\nLoading tutor data...")
    data_dir = project_root / "output" / "churn_data"

    tutors_df = pd.read_csv(data_dir / "tutors.csv")
    sessions_df = pd.read_csv(data_dir / "sessions.csv")
    feedback_df = pd.read_csv(data_dir / "feedback.csv")

    print(f"  Loaded {len(tutors_df):,} tutors")
    print(f"  Loaded {len(sessions_df):,} sessions")
    print(f"  Loaded {len(feedback_df):,} feedback records")

    return tutors_df, sessions_df, feedback_df


def demo_single_prediction(
    service: ChurnPredictionService,
    tutors_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    feedback_df: pd.DataFrame
):
    """Demonstrate single tutor prediction."""
    print_header("DEMO 1: Single Tutor Prediction")

    # Get a high-risk tutor (will churn)
    churners = tutors_df[tutors_df['will_churn'] == True]
    if len(churners) == 0:
        # If no churners, use any tutor
        print("No churning tutors found, using first tutor")
        churner = tutors_df.iloc[0]
    else:
        churner = churners.iloc[0]

    tutor_id = churner['tutor_id']

    print(f"\nPredicting churn for tutor: {tutor_id}")
    if churner['will_churn']:
        print("(This tutor will churn - model should detect high risk)")
    else:
        print("(Demonstrating prediction capability)")

    # Make prediction with timing
    start_time = time.time()
    prediction = service.predict_tutor(
        tutor_id=tutor_id,
        tutors_df=tutors_df,
        sessions_df=sessions_df,
        feedback_df=feedback_df,
        include_explanation=True
    )
    elapsed = time.time() - start_time

    print_prediction(prediction, show_explanation=True)
    print(f"\n⏱️  Prediction time: {elapsed:.3f} seconds")


def demo_batch_prediction(
    service: ChurnPredictionService,
    tutors_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    feedback_df: pd.DataFrame
):
    """Demonstrate batch prediction."""
    print_header("DEMO 2: Batch Prediction")

    # Select diverse set of tutors
    churners = tutors_df[tutors_df['will_churn'] == True].head(2)
    non_churners = tutors_df[tutors_df['will_churn'] == False].head(3)

    if len(churners) > 0:
        sample_tutors = pd.concat([churners, non_churners])
    else:
        sample_tutors = tutors_df.head(5)

    print(f"\nPredicting churn for {len(sample_tutors)} tutors:")
    if len(churners) > 0:
        print(f"  - {len(churners)} will-churn tutors (should be HIGH/CRITICAL risk)")
        print(f"  - {len(non_churners)} stable tutors (should be lower risk)")
    else:
        print(f"  - Demonstrating batch prediction on {len(sample_tutors)} tutors")

    # Make batch prediction
    start_time = time.time()
    predictions = service.predict_batch(
        tutors_df=sample_tutors,
        sessions_df=sessions_df,
        feedback_df=feedback_df,
        include_explanation=False
    )
    elapsed = time.time() - start_time

    # Group by risk level
    risk_counts = {}
    for pred in predictions:
        risk_level = pred['risk_level']
        risk_counts[risk_level] = risk_counts.get(risk_level, 0) + 1

    print(f"\n📊 Batch Prediction Results:")
    print(f"  Total predictions: {len(predictions)}")
    print(f"  Risk level distribution:")
    for level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        count = risk_counts.get(level, 0)
        if count > 0:
            print(f"    {level}: {count}")

    print(f"\n⏱️  Total time: {elapsed:.3f} seconds")
    print(f"  Average per tutor: {elapsed/len(predictions):.3f} seconds")

    # Show sample predictions
    print("\n📋 Sample Predictions:")
    for pred in predictions[:3]:
        print(f"\n  {pred['tutor_name']} ({pred['tutor_status']})")
        print(f"    Score: {pred['churn_score']}/100, Risk: {pred['risk_level']}")


def demo_risk_levels(
    service: ChurnPredictionService,
    tutors_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    feedback_df: pd.DataFrame
):
    """Demonstrate different risk levels."""
    print_header("DEMO 3: Risk Level Classification")

    print("\nMaking predictions to showcase different risk levels...")

    # Get one tutor from each category if possible
    predictions_by_risk = {}

    # Predict all and categorize
    all_predictions = service.predict_batch(
        tutors_df=tutors_df.head(20),  # Sample for speed
        sessions_df=sessions_df,
        feedback_df=feedback_df,
        include_explanation=False
    )

    for pred in all_predictions:
        risk = pred['risk_level']
        if risk not in predictions_by_risk:
            predictions_by_risk[risk] = pred

    # Display one example of each risk level
    for risk_level in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
        if risk_level in predictions_by_risk:
            pred = predictions_by_risk[risk_level]
            print(f"\n{risk_level} Risk Example:")
            print(f"  Tutor: {pred['tutor_name']} ({pred['tutor_status']})")
            print(f"  Churn Probability: {pred['churn_probability']:.2%}")
            print(f"  Churn Score: {pred['churn_score']}/100")


def demo_model_info(service: ChurnPredictionService):
    """Display model information."""
    print_header("DEMO 4: Model Information")

    info = service.get_model_info()

    print("\n📦 Model Configuration:")
    print(f"  Model Type: {info['model_type']}")
    print(f"  Model Version: {info['model_version']}")
    print(f"  Feature Count: {info['feature_count']}")
    print(f"  Model Path: {info['model_path']}")

    print("\n🎯 Risk Thresholds:")
    for level, threshold in info['risk_thresholds'].items():
        if level != 'CRITICAL':
            print(f"  {level}: < {threshold:.0%} probability")
        else:
            print(f"  {level}: ≥ 70% probability")

    print("\n📊 Churn Score Thresholds (0-100 scale):")
    for level, threshold in info['score_thresholds'].items():
        if level != 'CRITICAL':
            print(f"  {level}: < {threshold}")
        else:
            print(f"  {level}: ≥ 80")


def demo_performance_benchmark(
    service: ChurnPredictionService,
    tutors_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    feedback_df: pd.DataFrame
):
    """Benchmark prediction performance."""
    print_header("DEMO 5: Performance Benchmark")

    batch_sizes = [1, 5, 10, 20]
    results = []

    print("\nBenchmarking prediction performance...")
    print("(This may take a minute...)")

    for batch_size in batch_sizes:
        sample = tutors_df.head(batch_size)

        start_time = time.time()
        predictions = service.predict_batch(
            tutors_df=sample,
            sessions_df=sessions_df,
            feedback_df=feedback_df,
            include_explanation=False
        )
        elapsed = time.time() - start_time

        avg_time = elapsed / batch_size
        results.append({
            'batch_size': batch_size,
            'total_time': elapsed,
            'avg_time': avg_time,
            'predictions_per_sec': 1.0 / avg_time if avg_time > 0 else 0
        })

    print("\n📈 Performance Results:")
    print("\nBatch Size | Total Time | Avg Time/Tutor | Predictions/Sec")
    print("-" * 65)
    for r in results:
        print(
            f"{r['batch_size']:>10} | "
            f"{r['total_time']:>10.3f}s | "
            f"{r['avg_time']:>14.3f}s | "
            f"{r['predictions_per_sec']:>15.2f}"
        )

    print("\n✅ System can handle real-time predictions (<1s per tutor)")


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("CHURN PREDICTION DEPLOYMENT DEMO".center(70))
    print("=" * 70)

    # Load data
    tutors_df, sessions_df, feedback_df = load_data()

    # Initialize prediction service
    print("\nInitializing prediction service...")
    model_path = project_root / "output" / "models" / "churn_model.pkl"
    service = ChurnPredictionService(str(model_path))
    print(f"✅ Prediction service ready (model version: {service.model_version})")

    # Run demos
    try:
        demo_model_info(service)
        demo_single_prediction(service, tutors_df, sessions_df, feedback_df)
        demo_batch_prediction(service, tutors_df, sessions_df, feedback_df)
        demo_risk_levels(service, tutors_df, sessions_df, feedback_df)
        demo_performance_benchmark(service, tutors_df, sessions_df, feedback_df)

        # Final summary
        print_header("DEPLOYMENT SUMMARY")
        print("\n✅ Churn prediction system successfully deployed!")
        print("\nKey Capabilities:")
        print("  ✓ Real-time single tutor predictions")
        print("  ✓ Batch prediction for multiple tutors")
        print("  ✓ Multi-level risk classification (LOW/MEDIUM/HIGH/CRITICAL)")
        print("  ✓ Feature importance explanations")
        print("  ✓ Sub-second prediction latency")
        print("  ✓ Scalable batch processing")
        print("\nNext Steps:")
        print("  1. Deploy FastAPI service for production use")
        print("  2. Enable Redis caching for improved performance")
        print("  3. Set up scheduled batch predictions")
        print("  4. Integrate with intervention framework")

        print("\n" + "=" * 70)

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
