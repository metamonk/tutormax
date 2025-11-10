"""
XGBoost model training for tutor churn prediction.

Implements:
- Train/test split with stratification
- Hyperparameter optimization using cross-validation
- Model evaluation with AUC-ROC, precision-recall, and other metrics
- Feature importance analysis with SHAP
- Model persistence
"""

from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import (
    roc_auc_score,
    precision_recall_curve,
    average_precision_score,
    classification_report,
    confusion_matrix,
    roc_curve
)
import json
import pickle
from pathlib import Path
from datetime import datetime


class ChurnModelTrainer:
    """
    Train and evaluate XGBoost model for churn prediction.

    Optimizes hyperparameters and provides comprehensive evaluation metrics.
    """

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
        self.feature_names = None
        self.evaluation_results = {}

    def prepare_data(
        self,
        features_df: pd.DataFrame,
        target_col: str = 'will_churn'
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Prepare data for training and testing.

        Args:
            features_df: Feature matrix with target column
            target_col: Name of target column

        Returns:
            X_train, X_test, y_train, y_test
        """
        print("=" * 70)
        print("DATA PREPARATION")
        print("=" * 70)

        # Separate features and target
        X = features_df.drop(columns=[target_col, 'tutor_id'], errors='ignore')
        y = features_df[target_col].astype(int)

        # Store feature names
        self.feature_names = X.columns.tolist()

        print(f"\nDataset info:")
        print(f"  Total samples: {len(X):,}")
        print(f"  Features: {len(X.columns)}")
        print(f"  Churn rate: {y.mean():.2%}")
        print(f"  Class balance: {y.value_counts().to_dict()}")

        # Stratified train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=y
        )

        print(f"\nTrain/test split:")
        print(f"  Train samples: {len(X_train):,} (churn rate: {y_train.mean():.2%})")
        print(f"  Test samples: {len(X_test):,} (churn rate: {y_test.mean():.2%})")

        return X_train, X_test, y_train, y_test

    def train_with_hyperparameter_tuning(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        param_grid: Optional[Dict[str, List[Any]]] = None
    ) -> xgb.XGBClassifier:
        """
        Train XGBoost model with hyperparameter optimization.

        Args:
            X_train: Training features
            y_train: Training labels
            param_grid: Optional custom parameter grid for tuning

        Returns:
            Trained XGBoost model
        """
        print("\n" + "=" * 70)
        print("HYPERPARAMETER OPTIMIZATION")
        print("=" * 70)

        # Default parameter configurations to try
        if param_grid is None:
            param_grid = {
                'max_depth': [3, 4, 5, 6],
                'learning_rate': [0.01, 0.05, 0.1],
                'n_estimators': [100, 200, 300],
                'subsample': [0.8, 0.9, 1.0],
                'colsample_bytree': [0.8, 0.9, 1.0],
                'min_child_weight': [1, 3, 5],
                'gamma': [0, 0.1, 0.2]
            }

        # Calculate scale_pos_weight for imbalanced classes
        scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

        print(f"\nBase configuration:")
        print(f"  scale_pos_weight: {scale_pos_weight:.2f}")
        print(f"  objective: binary:logistic")
        print(f"  eval_metric: auc")

        # Grid search with different hyperparameter combinations
        best_score = 0
        best_params = None
        best_model = None

        # Create stratified k-fold for cross-validation
        cv = StratifiedKFold(
            n_splits=self.cv_folds,
            shuffle=True,
            random_state=self.random_state
        )

        # Test a subset of parameter combinations (full grid search would be too slow)
        print(f"\nTesting hyperparameter combinations...")
        param_combinations = self._generate_param_combinations(param_grid, max_combinations=20)

        for i, params in enumerate(param_combinations, 1):
            # Create model with these parameters
            model = xgb.XGBClassifier(
                **params,
                scale_pos_weight=scale_pos_weight,
                objective='binary:logistic',
                eval_metric='auc',
                random_state=self.random_state,
                use_label_encoder=False
            )

            # Cross-validation
            cv_scores = cross_val_score(
                model, X_train, y_train,
                cv=cv,
                scoring='roc_auc',
                n_jobs=-1
            )

            mean_score = cv_scores.mean()
            std_score = cv_scores.std()

            print(f"  [{i}/{len(param_combinations)}] AUC: {mean_score:.4f} (+/- {std_score:.4f}) - {params}")

            if mean_score > best_score:
                best_score = mean_score
                best_params = params
                best_model = model

        print(f"\n✓ Best CV AUC-ROC: {best_score:.4f}")
        print(f"  Best parameters: {best_params}")

        # Train final model with best parameters on full training set
        print(f"\nTraining final model with best parameters...")
        best_model.fit(
            X_train, y_train,
            verbose=False
        )

        self.model = best_model
        self.evaluation_results['cv_auc_roc'] = best_score
        self.evaluation_results['best_params'] = best_params

        return best_model

    def _generate_param_combinations(
        self,
        param_grid: Dict[str, List[Any]],
        max_combinations: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Generate random parameter combinations from grid.

        Args:
            param_grid: Parameter grid
            max_combinations: Maximum combinations to generate

        Returns:
            List of parameter dictionaries
        """
        import itertools
        import random

        # Get all possible combinations
        keys = param_grid.keys()
        values = param_grid.values()
        all_combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]

        # Sample random subset if too many
        if len(all_combinations) > max_combinations:
            random.seed(self.random_state)
            combinations = random.sample(all_combinations, max_combinations)
        else:
            combinations = all_combinations

        return combinations

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

        if self.model is None:
            raise ValueError("Model must be trained before evaluation")

        # Get predictions
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        y_pred = (y_pred_proba >= threshold).astype(int)

        # AUC-ROC
        auc_roc = roc_auc_score(y_test, y_pred_proba)

        # Precision-Recall
        precision, recall, pr_thresholds = precision_recall_curve(y_test, y_pred_proba)
        avg_precision = average_precision_score(y_test, y_pred_proba)

        # Classification report
        class_report = classification_report(y_test, y_pred, output_dict=True)

        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()

        # Store results
        results = {
            'auc_roc': auc_roc,
            'avg_precision': avg_precision,
            'accuracy': class_report['accuracy'],
            'precision': class_report['1']['precision'],
            'recall': class_report['1']['recall'],
            'f1_score': class_report['1']['f1-score'],
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
        print(f"  AUC-ROC: {auc_roc:.4f}")
        print(f"  Avg Precision: {avg_precision:.4f}")
        print(f"  Accuracy: {class_report['accuracy']:.4f}")
        print(f"  Precision (churn): {class_report['1']['precision']:.4f}")
        print(f"  Recall (churn): {class_report['1']['recall']:.4f}")
        print(f"  F1-Score (churn): {class_report['1']['f1-score']:.4f}")

        print(f"\nConfusion Matrix:")
        print(f"  True Negatives:  {tn:4d}  |  False Positives: {fp:4d}")
        print(f"  False Negatives: {fn:4d}  |  True Positives:  {tp:4d}")

        return results

    def get_feature_importance(
        self,
        top_n: int = 20
    ) -> pd.DataFrame:
        """
        Get feature importance from trained model.

        Args:
            top_n: Number of top features to return

        Returns:
            DataFrame with feature importances
        """
        if self.model is None:
            raise ValueError("Model must be trained before getting feature importance")

        # Get importance scores
        importance_scores = self.model.feature_importances_

        # Create dataframe
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance_scores
        }).sort_values('importance', ascending=False)

        print(f"\nTop {top_n} Most Important Features:")
        print("=" * 70)
        for i, row in importance_df.head(top_n).iterrows():
            print(f"  {row['feature']:40s} {row['importance']:.4f}")

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

        if self.model is None:
            raise ValueError("Model must be trained before saving")

        # Create directory if needed
        model_path = Path(model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)

        # Save model
        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'feature_names': self.feature_names,
                'timestamp': datetime.now().isoformat()
            }, f)

        print(f"\n✓ Model saved to: {model_path}")

        # Save results if path provided
        if results_path:
            results_path = Path(results_path)
            results_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert results to JSON-serializable format
            results_json = self._prepare_results_for_json(self.evaluation_results)

            with open(results_path, 'w') as f:
                json.dump(results_json, f, indent=2)

            print(f"✓ Evaluation results saved to: {results_path}")

    def _prepare_results_for_json(self, results: Dict) -> Dict:
        """Convert results to JSON-serializable format."""
        json_results = {}

        for key, value in results.items():
            if isinstance(value, (np.integer, np.floating)):
                json_results[key] = float(value)
            elif isinstance(value, np.ndarray):
                json_results[key] = value.tolist()
            elif isinstance(value, pd.DataFrame):
                json_results[key] = value.to_dict('records')
            else:
                json_results[key] = value

        return json_results

    @staticmethod
    def load_model(model_path: str) -> Tuple[xgb.XGBClassifier, List[str]]:
        """
        Load saved model.

        Args:
            model_path: Path to saved model

        Returns:
            Tuple of (model, feature_names)
        """
        with open(model_path, 'rb') as f:
            saved_data = pickle.load(f)

        return saved_data['model'], saved_data['feature_names']


def train_churn_model(
    features_df: pd.DataFrame,
    output_dir: str = "output/models",
    test_size: float = 0.2,
    cv_folds: int = 5
) -> Tuple[xgb.XGBClassifier, Dict[str, Any]]:
    """
    Convenience function to train churn prediction model.

    Args:
        features_df: Feature matrix with 'will_churn' target
        output_dir: Directory to save model and results
        test_size: Proportion for test set
        cv_folds: Number of CV folds

    Returns:
        Tuple of (trained_model, evaluation_results)
    """
    # Initialize trainer
    trainer = ChurnModelTrainer(
        test_size=test_size,
        random_state=42,
        cv_folds=cv_folds
    )

    # Prepare data
    X_train, X_test, y_train, y_test = trainer.prepare_data(features_df)

    # Train with hyperparameter tuning
    model = trainer.train_with_hyperparameter_tuning(X_train, y_train)

    # Evaluate
    results = trainer.evaluate(X_test, y_test)

    # Get feature importance
    trainer.get_feature_importance(top_n=20)

    # Save model and results
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    trainer.save_model(
        model_path=output_path / "churn_model.pkl",
        results_path=output_path / "evaluation_results.json"
    )

    print("\n" + "=" * 70)
    print("TRAINING COMPLETE!")
    print("=" * 70)
    print(f"\nModel ready for deployment")
    print(f"Test AUC-ROC: {results['auc_roc']:.4f}")

    return model, trainer.evaluation_results


if __name__ == "__main__":
    # Demo execution
    import sys

    # Load features
    features_df = pd.read_csv("output/churn_data/features.csv")

    print(f"Loaded {len(features_df):,} tutors with {len(features_df.columns)-2} features")

    # Train model
    model, results = train_churn_model(
        features_df,
        output_dir="output/models",
        test_size=0.2,
        cv_folds=5
    )
