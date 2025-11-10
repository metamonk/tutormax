"""
Model interpretability and evaluation using SHAP and precision-recall analysis.

Provides comprehensive model understanding through:
- SHAP (SHapley Additive exPlanations) values
- Precision-recall curves
- Feature importance analysis
- Individual prediction explanations
- Model calibration assessment
"""

from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import shap
from sklearn.metrics import (
    precision_recall_curve,
    average_precision_score,
    roc_curve,
    auc,
    confusion_matrix,
    classification_report
)
from pathlib import Path
import json
import pickle


class ModelInterpreter:
    """
    Interpret and explain XGBoost churn prediction model.

    Uses SHAP values for model-agnostic explanations and various
    visualization techniques for model understanding.
    """

    def __init__(self, model, feature_names: List[str]):
        """
        Initialize model interpreter.

        Args:
            model: Trained XGBoost model
            feature_names: List of feature names
        """
        self.model = model
        self.feature_names = feature_names
        self.explainer = None
        self.shap_values = None

    def compute_shap_values(
        self,
        X: pd.DataFrame,
        sample_size: Optional[int] = None
    ) -> np.ndarray:
        """
        Compute SHAP values for model predictions.

        Args:
            X: Feature matrix
            sample_size: Optional sample size for background data

        Returns:
            SHAP values array
        """
        print("=" * 70)
        print("COMPUTING SHAP VALUES")
        print("=" * 70)

        # Sample background data if needed (for speed)
        if sample_size and len(X) > sample_size:
            background = X.sample(n=sample_size, random_state=42)
        else:
            background = X

        print(f"\nBackground data size: {len(background):,}")
        print(f"Computing SHAP values for {len(X):,} samples...")

        # Create TreeExplainer (optimized for tree-based models)
        self.explainer = shap.TreeExplainer(self.model)

        # Compute SHAP values
        self.shap_values = self.explainer.shap_values(X)

        print(f"✓ SHAP values computed!")
        print(f"  Shape: {self.shap_values.shape}")

        return self.shap_values

    def plot_shap_summary(
        self,
        X: pd.DataFrame,
        output_path: Optional[str] = None,
        max_display: int = 20
    ):
        """
        Create SHAP summary plot showing feature importance.

        Args:
            X: Feature matrix
            output_path: Optional path to save plot
            max_display: Maximum features to display
        """
        if self.shap_values is None:
            self.compute_shap_values(X)

        print("\nGenerating SHAP summary plot...")

        plt.figure(figsize=(12, 8))
        shap.summary_plot(
            self.shap_values,
            X,
            feature_names=self.feature_names,
            max_display=max_display,
            show=False
        )
        plt.title("SHAP Feature Importance Summary", fontsize=16, fontweight='bold')
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Summary plot saved to: {output_path}")

        plt.close()

    def plot_shap_bar(
        self,
        X: pd.DataFrame,
        output_path: Optional[str] = None,
        max_display: int = 20
    ):
        """
        Create SHAP bar plot showing mean absolute SHAP values.

        Args:
            X: Feature matrix
            output_path: Optional path to save plot
            max_display: Maximum features to display
        """
        if self.shap_values is None:
            self.compute_shap_values(X)

        print("\nGenerating SHAP bar plot...")

        plt.figure(figsize=(10, 8))
        shap.summary_plot(
            self.shap_values,
            X,
            plot_type="bar",
            feature_names=self.feature_names,
            max_display=max_display,
            show=False
        )
        plt.title("SHAP Feature Importance (Mean Absolute)", fontsize=16, fontweight='bold')
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Bar plot saved to: {output_path}")

        plt.close()

    def explain_prediction(
        self,
        X_sample: pd.DataFrame,
        sample_idx: int = 0,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Explain individual prediction using SHAP force plot.

        Args:
            X_sample: Sample to explain
            sample_idx: Index of sample
            output_path: Optional path to save plot

        Returns:
            Dictionary with explanation details
        """
        if self.shap_values is None:
            self.compute_shap_values(X_sample)

        print(f"\nExplaining prediction for sample {sample_idx}...")

        # Get prediction
        prediction_proba = self.model.predict_proba(X_sample.iloc[[sample_idx]])[0, 1]
        prediction = int(prediction_proba >= 0.5)

        # Get SHAP values for this sample
        sample_shap = self.shap_values[sample_idx]

        # Get top contributing features
        feature_contributions = pd.DataFrame({
            'feature': self.feature_names,
            'value': X_sample.iloc[sample_idx].values,
            'shap_value': sample_shap
        }).sort_values('shap_value', key=abs, ascending=False)

        # Create force plot
        plt.figure(figsize=(14, 3))
        shap.force_plot(
            self.explainer.expected_value,
            sample_shap,
            X_sample.iloc[sample_idx],
            feature_names=self.feature_names,
            matplotlib=True,
            show=False
        )
        plt.title(f"SHAP Force Plot - Prediction: {prediction} (prob: {prediction_proba:.3f})",
                  fontsize=14, fontweight='bold')

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ Force plot saved to: {output_path}")

        plt.close()

        explanation = {
            'prediction': prediction,
            'probability': float(prediction_proba),
            'base_value': float(self.explainer.expected_value),
            'top_features': feature_contributions.head(10).to_dict('records')
        }

        return explanation

    def plot_precision_recall_curve(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        output_path: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Plot precision-recall curve.

        Args:
            X: Feature matrix
            y: True labels
            output_path: Optional path to save plot

        Returns:
            Dictionary with PR metrics
        """
        print("\n" + "=" * 70)
        print("PRECISION-RECALL ANALYSIS")
        print("=" * 70)

        # Get predictions
        y_pred_proba = self.model.predict_proba(X)[:, 1]

        # Compute precision-recall curve
        precision, recall, thresholds = precision_recall_curve(y, y_pred_proba)
        avg_precision = average_precision_score(y, y_pred_proba)

        # Find best F1 threshold
        f1_scores = 2 * (precision * recall) / (precision + recall + 1e-10)
        best_f1_idx = np.argmax(f1_scores[:-1])  # Exclude last element
        best_threshold = thresholds[best_f1_idx]
        best_f1 = f1_scores[best_f1_idx]

        print(f"\nAverage Precision: {avg_precision:.4f}")
        print(f"Best F1 Score: {best_f1:.4f}")
        print(f"Best Threshold: {best_threshold:.4f}")

        # Plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Precision-Recall curve
        ax1.plot(recall, precision, linewidth=2, color='blue')
        ax1.fill_between(recall, precision, alpha=0.2, color='blue')
        ax1.set_xlabel('Recall', fontsize=12)
        ax1.set_ylabel('Precision', fontsize=12)
        ax1.set_title(f'Precision-Recall Curve\n(AP = {avg_precision:.4f})',
                      fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim([0, 1])
        ax1.set_ylim([0, 1.05])

        # Threshold vs Precision/Recall
        ax2.plot(thresholds, precision[:-1], label='Precision', linewidth=2, color='green')
        ax2.plot(thresholds, recall[:-1], label='Recall', linewidth=2, color='red')
        ax2.plot(thresholds, f1_scores[:-1], label='F1 Score', linewidth=2,
                color='purple', linestyle='--')
        ax2.axvline(best_threshold, color='black', linestyle=':',
                   label=f'Best Threshold ({best_threshold:.3f})')
        ax2.set_xlabel('Threshold', fontsize=12)
        ax2.set_ylabel('Score', fontsize=12)
        ax2.set_title('Metrics vs Classification Threshold',
                      fontsize=14, fontweight='bold')
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim([0, 1])
        ax2.set_ylim([0, 1.05])

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ PR curve saved to: {output_path}")

        plt.close()

        return {
            'average_precision': float(avg_precision),
            'best_f1_score': float(best_f1),
            'best_threshold': float(best_threshold)
        }

    def plot_roc_curve(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        output_path: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Plot ROC curve.

        Args:
            X: Feature matrix
            y: True labels
            output_path: Optional path to save plot

        Returns:
            Dictionary with ROC metrics
        """
        print("\nGenerating ROC curve...")

        # Get predictions
        y_pred_proba = self.model.predict_proba(X)[:, 1]

        # Compute ROC curve
        fpr, tpr, thresholds = roc_curve(y, y_pred_proba)
        roc_auc = auc(fpr, tpr)

        # Plot
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, linewidth=2, label=f'ROC Curve (AUC = {roc_auc:.4f})')
        plt.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random Classifier')
        plt.fill_between(fpr, tpr, alpha=0.2)
        plt.xlabel('False Positive Rate', fontsize=12)
        plt.ylabel('True Positive Rate', fontsize=12)
        plt.title('ROC Curve', fontsize=14, fontweight='bold')
        plt.legend(loc='lower right', fontsize=11)
        plt.grid(True, alpha=0.3)
        plt.xlim([0, 1])
        plt.ylim([0, 1.05])
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"✓ ROC curve saved to: {output_path}")

        plt.close()

        return {
            'roc_auc': float(roc_auc)
        }

    def analyze_feature_importance(
        self,
        X: pd.DataFrame,
        top_n: int = 20
    ) -> pd.DataFrame:
        """
        Analyze feature importance using SHAP values.

        Args:
            X: Feature matrix
            top_n: Number of top features to return

        Returns:
            DataFrame with feature importance analysis
        """
        if self.shap_values is None:
            self.compute_shap_values(X)

        print("\n" + "=" * 70)
        print("FEATURE IMPORTANCE ANALYSIS")
        print("=" * 70)

        # Calculate mean absolute SHAP values
        mean_abs_shap = np.abs(self.shap_values).mean(axis=0)

        # Create dataframe
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'mean_abs_shap': mean_abs_shap,
            'mean_shap': self.shap_values.mean(axis=0),
            'std_shap': self.shap_values.std(axis=0)
        }).sort_values('mean_abs_shap', ascending=False)

        print(f"\nTop {top_n} Features by SHAP Importance:")
        print("-" * 70)
        for i, row in importance_df.head(top_n).iterrows():
            print(f"  {row['feature']:40s} | "
                  f"Mean |SHAP|: {row['mean_abs_shap']:.4f} | "
                  f"Mean SHAP: {row['mean_shap']:+.4f}")

        return importance_df

    def generate_comprehensive_report(
        self,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series,
        output_dir: str
    ) -> Dict[str, Any]:
        """
        Generate comprehensive interpretability report.

        Args:
            X_train: Training features
            X_test: Test features
            y_train: Training labels
            y_test: Test labels
            output_dir: Directory to save outputs

        Returns:
            Dictionary with all analysis results
        """
        print("\n" + "=" * 70)
        print("GENERATING COMPREHENSIVE INTERPRETABILITY REPORT")
        print("=" * 70)

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = {}

        # 1. Compute SHAP values
        print("\n1. Computing SHAP values...")
        self.compute_shap_values(X_test, sample_size=100)

        # 2. Feature importance
        print("\n2. Analyzing feature importance...")
        importance_df = self.analyze_feature_importance(X_test, top_n=20)
        results['feature_importance'] = importance_df.to_dict('records')

        # 3. SHAP visualizations
        print("\n3. Creating SHAP visualizations...")
        self.plot_shap_summary(X_test, output_path / "shap_summary.png")
        self.plot_shap_bar(X_test, output_path / "shap_bar.png")

        # 4. Precision-Recall analysis
        print("\n4. Precision-Recall analysis...")
        pr_metrics = self.plot_precision_recall_curve(
            X_test, y_test,
            output_path / "precision_recall_curve.png"
        )
        results['precision_recall'] = pr_metrics

        # 5. ROC curve
        print("\n5. ROC curve analysis...")
        roc_metrics = self.plot_roc_curve(
            X_test, y_test,
            output_path / "roc_curve.png"
        )
        results['roc'] = roc_metrics

        # 6. Individual predictions
        print("\n6. Explaining individual predictions...")
        # Explain one churned and one active tutor
        churned_idx = np.where(y_test == 1)[0][0] if any(y_test == 1) else 0
        active_idx = np.where(y_test == 0)[0][0] if any(y_test == 0) else 1

        churned_explanation = self.explain_prediction(
            X_test, churned_idx,
            output_path / "explanation_churned.png"
        )
        active_explanation = self.explain_prediction(
            X_test, active_idx,
            output_path / "explanation_active.png"
        )

        results['sample_explanations'] = {
            'churned_tutor': churned_explanation,
            'active_tutor': active_explanation
        }

        # 7. Save results
        print("\n7. Saving results...")
        with open(output_path / "interpretability_report.json", 'w') as f:
            json.dump(results, f, indent=2)

        print("\n" + "=" * 70)
        print("REPORT GENERATION COMPLETE!")
        print("=" * 70)
        print(f"\nOutputs saved to: {output_path}")
        print(f"  - SHAP summary plot: shap_summary.png")
        print(f"  - SHAP bar plot: shap_bar.png")
        print(f"  - Precision-Recall curve: precision_recall_curve.png")
        print(f"  - ROC curve: roc_curve.png")
        print(f"  - Sample explanations: explanation_*.png")
        print(f"  - Full report: interpretability_report.json")

        return results


def load_and_interpret_model(
    model_path: str,
    features_path: str,
    output_dir: str = "output/interpretability"
) -> Dict[str, Any]:
    """
    Convenience function to load model and generate interpretability report.

    Args:
        model_path: Path to saved model
        features_path: Path to features CSV
        output_dir: Directory to save outputs

    Returns:
        Dictionary with interpretability results
    """
    from .model_training import ChurnModelTrainer

    # Load model
    print("Loading model...")
    model, feature_names = ChurnModelTrainer.load_model(model_path)

    # Load features
    print("Loading features...")
    features_df = pd.read_csv(features_path)

    # Prepare data
    X = features_df.drop(columns=['will_churn', 'tutor_id'], errors='ignore')
    y = features_df['will_churn'].astype(int)

    # Split (use same split as training)
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Create interpreter
    interpreter = ModelInterpreter(model, feature_names)

    # Generate report
    results = interpreter.generate_comprehensive_report(
        X_train, X_test, y_train, y_test,
        output_dir
    )

    return results


if __name__ == "__main__":
    # Demo execution
    results = load_and_interpret_model(
        model_path="output/models/churn_model.pkl",
        features_path="output/churn_data/features.csv",
        output_dir="output/interpretability"
    )

    print("\n✓ Interpretability analysis complete!")
