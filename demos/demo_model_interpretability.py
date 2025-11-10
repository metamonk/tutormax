"""
Demo: Model Interpretability with SHAP Analysis

Demonstrates comprehensive model interpretation including:
- SHAP value computation and visualization
- Feature importance analysis
- Precision-recall curves
- ROC curves
- Individual prediction explanations
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.evaluation.model_interpretability import load_and_interpret_model


def main():
    """Run model interpretability demonstration."""

    print("=" * 70)
    print("MODEL INTERPRETABILITY & SHAP ANALYSIS DEMO")
    print("=" * 70)
    print()
    print("This demo generates comprehensive model interpretability analysis")
    print("including SHAP explanations, feature importance, and performance")
    print("visualizations.")
    print()

    # Paths
    model_path = "output/models/churn_model.pkl"
    features_path = "output/churn_data/features.csv"
    output_dir = "output/interpretability"

    # Check if model exists
    if not Path(model_path).exists():
        print(f"✗ Error: Model not found at {model_path}")
        print("  Please train the model first (Task 4.3)")
        return

    if not Path(features_path).exists():
        print(f"✗ Error: Features not found at {features_path}")
        print("  Please run feature engineering first (Task 4.2)")
        return

    # Run interpretability analysis
    print("Starting interpretability analysis...")
    print("-" * 70)

    try:
        results = load_and_interpret_model(
            model_path=model_path,
            features_path=features_path,
            output_dir=output_dir
        )

        # Display summary
        print("\n" + "=" * 70)
        print("INTERPRETABILITY SUMMARY")
        print("=" * 70)

        # Precision-Recall metrics
        pr_metrics = results['precision_recall']
        print(f"\nPrecision-Recall Metrics:")
        print(f"  Average Precision: {pr_metrics['average_precision']:.4f}")
        print(f"  Best F1 Score: {pr_metrics['best_f1_score']:.4f}")
        print(f"  Optimal Threshold: {pr_metrics['best_threshold']:.4f}")

        # ROC metrics
        roc_metrics = results['roc']
        print(f"\nROC Metrics:")
        print(f"  AUC-ROC: {roc_metrics['roc_auc']:.4f}")

        # Top features
        print(f"\nTop 10 Most Important Features (by SHAP):")
        for i, feat in enumerate(results['feature_importance'][:10], 1):
            print(f"  {i:2d}. {feat['feature']:40s} "
                  f"Mean |SHAP|: {feat['mean_abs_shap']:.4f}")

        # Sample explanations
        print(f"\nSample Predictions Explained:")
        churned = results['sample_explanations']['churned_tutor']
        active = results['sample_explanations']['active_tutor']

        print(f"  Churned Tutor: Prediction={churned['prediction']} "
              f"(prob={churned['probability']:.3f})")
        print(f"    Top contributing feature: {churned['top_features'][0]['feature']}")
        print(f"    SHAP value: {churned['top_features'][0]['shap_value']:.4f}")

        print(f"  Active Tutor: Prediction={active['prediction']} "
              f"(prob={active['probability']:.3f})")
        print(f"    Top contributing feature: {active['top_features'][0]['feature']}")
        print(f"    SHAP value: {active['top_features'][0]['shap_value']:.4f}")

        # Output files
        print(f"\n" + "=" * 70)
        print("OUTPUT FILES")
        print("=" * 70)
        print(f"\nGenerated visualizations in: {output_dir}/")
        print(f"  📊 shap_summary.png          - SHAP value distribution")
        print(f"  📊 shap_bar.png              - Mean absolute SHAP importance")
        print(f"  📊 precision_recall_curve.png - PR curve & threshold analysis")
        print(f"  📊 roc_curve.png             - ROC curve")
        print(f"  📊 explanation_churned.png   - Force plot for churned tutor")
        print(f"  📊 explanation_active.png    - Force plot for active tutor")
        print(f"  📄 interpretability_report.json - Complete analysis data")

        print("\n" + "=" * 70)
        print("NEXT STEPS")
        print("=" * 70)
        print("1. Review SHAP visualizations to understand feature importance")
        print("2. Examine force plots to see how individual predictions are made")
        print("3. Use insights to refine feature engineering (Task 4.2)")
        print("4. Deploy model with confidence (Task 4.5)")
        print()

        print("✓ Interpretability analysis complete!")

    except Exception as e:
        print(f"\n✗ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    main()
