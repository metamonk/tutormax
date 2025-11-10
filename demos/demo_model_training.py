"""
Demo: XGBoost Model Training for Churn Prediction

Demonstrates the complete model training pipeline including:
- Loading engineered features
- Train/test split
- Hyperparameter optimization
- Cross-validation
- Model evaluation
- Feature importance analysis
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from src.evaluation.model_training import train_churn_model


def main():
    """Run model training demonstration."""

    print("=" * 70)
    print("XGBOOST CHURN PREDICTION MODEL TRAINING DEMO")
    print("=" * 70)
    print()
    print("This demo trains an XGBoost classifier to predict tutor churn")
    print("using engineered features from task 4.2.")
    print()

    # Load features
    features_path = "output/churn_data/features.csv"
    print(f"Loading features from: {features_path}")

    try:
        features_df = pd.read_csv(features_path)
        print(f"✓ Loaded {len(features_df):,} tutors with {len(features_df.columns)-2} features")
    except FileNotFoundError:
        print(f"✗ Error: Features file not found at {features_path}")
        print("  Please run feature engineering first (task 4.2)")
        return

    # Train model
    print("\nStarting model training...")
    print("-" * 70)

    model, results = train_churn_model(
        features_df,
        output_dir="output/models",
        test_size=0.2,
        cv_folds=5
    )

    # Summary
    print("\n" + "=" * 70)
    print("TRAINING SUMMARY")
    print("=" * 70)
    print(f"\n✓ Model trained and saved successfully!")
    print(f"\nKey Metrics:")
    print(f"  - Cross-validation AUC-ROC: {results['cv_auc_roc']:.4f}")
    print(f"  - Test AUC-ROC: {results['auc_roc']:.4f}")
    print(f"  - Test Precision: {results['precision']:.4f}")
    print(f"  - Test Recall: {results['recall']:.4f}")
    print(f"  - Test F1-Score: {results['f1_score']:.4f}")

    print(f"\nConfusion Matrix:")
    cm = results['confusion_matrix']
    print(f"  TN: {cm['tn']:4d} | FP: {cm['fp']:4d}")
    print(f"  FN: {cm['fn']:4d} | TP: {cm['tp']:4d}")

    print(f"\nTop 5 Features:")
    for i, feat in enumerate(results['feature_importance'][:5], 1):
        print(f"  {i}. {feat['feature']:40s} {feat['importance']:.4f}")

    print(f"\nOutput Files:")
    print(f"  - Model: output/models/churn_model.pkl")
    print(f"  - Results: output/models/evaluation_results.json")

    print("\n" + "=" * 70)
    print("Next Steps:")
    print("=" * 70)
    print("1. Review feature importance in evaluation_results.json")
    print("2. Use SHAP for interpretability analysis (Task 4.4)")
    print("3. Deploy model for real-time predictions (Task 4.5)")
    print()


if __name__ == "__main__":
    main()
