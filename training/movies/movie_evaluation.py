"""
Movie LightFM Model Evaluation Script

This script evaluates the trained LightFM model using proper methodology:
1. Loads saved train/test interactions (no rebuilding)
2. Masks training interactions during test evaluation
3. Reports only test metrics (train metrics are diagnostic only)

Metrics:
- Precision@K: Fraction of top-K recommendations that are relevant
- Recall@K: Fraction of relevant items captured in top-K
- AUC: Probability of ranking a positive higher than a negative
"""

import json
import os
from pathlib import Path

import joblib
import numpy as np
from lightfm import LightFM
from lightfm.data import Dataset
from lightfm.evaluation import auc_score, precision_at_k, recall_at_k

# Paths - Support both Docker and local development
if os.path.exists("/models/movie_recommender"):
    # Running in Docker
    MODEL_DIR = Path("/models/movie_recommender")
else:
    # Local development
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    MODEL_DIR = PROJECT_ROOT / "models" / "movie_recommender"

RESULTS_FILE = MODEL_DIR / "evaluation_results.json"


def load_artifacts() -> tuple[LightFM, object, object, object, dict]:
    """
    Load all artifacts needed for evaluation.

    IMPORTANT: We load the saved train/test interactions rather than
    rebuilding them. This ensures consistency with training and avoids
    subtle bugs from reordering or filtering changes.

    Returns:
        Tuple of (model, item_features, train_interactions, test_interactions, config)
    """
    print(f"Loading artifacts from {MODEL_DIR}...")

    if not MODEL_DIR.exists():
        raise FileNotFoundError(f"Model directory not found at {MODEL_DIR}")

    model = joblib.load(MODEL_DIR / "lightfm_model.pkl")
    item_features = joblib.load(MODEL_DIR / "item_features.pkl")

    # CRITICAL: Load the SAVED interactions, don't rebuild
    train_interactions = joblib.load(MODEL_DIR / "train_interactions.pkl")
    test_interactions = joblib.load(MODEL_DIR / "test_interactions.pkl")

    # Load training config if available
    config_path = MODEL_DIR / "training_config.pkl"
    if config_path.exists():
        config = joblib.load(config_path)
    else:
        config = {"note": "Legacy model - no config saved"}

    print("  Model and interactions loaded successfully.")
    print(f"  Train interactions: {train_interactions.nnz:,}")
    print(f"  Test interactions: {test_interactions.nnz:,}")

    return model, item_features, train_interactions, test_interactions, config


def evaluate_model(
    model: LightFM,
    train_interactions: object,
    test_interactions: object,
    item_features: object,
    k: int = 10,
    num_threads: int = 4,
) -> dict[str, float]:
    """
    Evaluate the model with proper masking.

    CRITICAL FIX: We pass train_interactions to the evaluation functions.
    This masks items the user already interacted with during training,
    preventing data leakage and ensuring fair evaluation.

    Args:
        model: Trained LightFM model
        train_interactions: Training interactions (used for masking)
        test_interactions: Test interactions (ground truth)
        item_features: Item feature matrix
        k: Number of recommendations to evaluate
        num_threads: Number of threads for parallel computation

    Returns:
        Dictionary of metric names to values
    """
    print(f"\nEvaluating model (K={k})...")
    print("  (This may take several minutes on large datasets)")

    metrics: dict[str, float] = {}

    # =========================================================================
    # TEST METRICS (Primary - what we report)
    # =========================================================================
    # CRITICAL: Pass train_interactions to mask items the user already saw
    # This prevents the model from being rewarded for recommending known items

    print("  Computing Test Precision@K...")
    test_precision = precision_at_k(
        model,
        test_interactions,
        train_interactions=train_interactions,  # <-- MASK training items
        item_features=item_features,
        k=k,
        num_threads=num_threads,
    ).mean()
    metrics[f"test_precision@{k}"] = float(test_precision)

    print("  Computing Test Recall@K...")
    test_recall = recall_at_k(
        model,
        test_interactions,
        train_interactions=train_interactions,  # <-- MASK training items
        item_features=item_features,
        k=k,
        num_threads=num_threads,
    ).mean()
    metrics[f"test_recall@{k}"] = float(test_recall)

    print("  Computing Test AUC...")
    test_auc = auc_score(
        model,
        test_interactions,
        train_interactions=train_interactions,  # <-- MASK training items
        item_features=item_features,
        num_threads=num_threads,
    ).mean()
    metrics["test_auc"] = float(test_auc)

    # =========================================================================
    # TRAIN METRICS (Diagnostic only - NOT primary metrics)
    # =========================================================================
    # These are computed WITHOUT masking (evaluating on training data itself)
    # They show how well the model fits the training data, not generalization
    # High train + low test = overfitting

    print("  Computing Train Precision@K (diagnostic)...")
    train_precision = precision_at_k(
        model,
        train_interactions,
        # No masking for train metrics
        item_features=item_features,
        k=k,
        num_threads=num_threads,
    ).mean()
    metrics[f"train_precision@{k}"] = float(train_precision)

    print("  Computing Train Recall@K (diagnostic)...")
    train_recall = recall_at_k(
        model,
        train_interactions,
        item_features=item_features,
        k=k,
        num_threads=num_threads,
    ).mean()
    metrics[f"train_recall@{k}"] = float(train_recall)

    print("  Computing Train AUC (diagnostic)...")
    train_auc = auc_score(
        model, train_interactions, item_features=item_features, num_threads=num_threads
    ).mean()
    metrics["train_auc"] = float(train_auc)

    return metrics


def print_results(metrics: dict[str, float], k: int = 10) -> None:
    """Print formatted evaluation results."""
    print("\n" + "=" * 60)
    print("LIGHTFM MOVIE RECOMMENDER EVALUATION RESULTS")
    print("=" * 60)

    print(f"\n{'Metric':<30} {'Train':<12} {'Test':<12}")
    print("-" * 60)

    print(
        f"{'Precision@' + str(k):<30} {metrics[f'train_precision@{k}']:<12.4f} {metrics[f'test_precision@{k}']:<12.4f}"
    )
    print(
        f"{'Recall@' + str(k):<30} {metrics[f'train_recall@{k}']:<12.4f} {metrics[f'test_recall@{k}']:<12.4f}"
    )
    print(f"{'AUC':<30} {metrics['train_auc']:<12.4f} {metrics['test_auc']:<12.4f}")

    print("-" * 60)

    # Interpretation
    print("\n📊 Interpretation:")

    # Precision interpretation
    test_prec = metrics[f"test_precision@{k}"]
    if test_prec >= 0.10:
        print(
            f"  ✅ Precision@{k}: Strong ({test_prec:.1%} of recommendations are relevant)"
        )
    elif test_prec >= 0.05:
        print(
            f"  ✓ Precision@{k}: Good ({test_prec:.1%} of recommendations are relevant)"
        )
    else:
        print(f"  ⚠ Precision@{k}: Below typical ({test_prec:.1%})")

    # AUC interpretation
    test_auc = metrics["test_auc"]
    if test_auc >= 0.95:
        print(f"  ✅ AUC: Excellent ranking capability ({test_auc:.2%})")
    elif test_auc >= 0.85:
        print(f"  ✓ AUC: Good ranking capability ({test_auc:.2%})")
    else:
        print(f"  ⚠ AUC: Below expected ({test_auc:.2%})")

    # Train/test gap
    train_auc = metrics["train_auc"]
    gap = train_auc - test_auc
    if gap > 0.10:
        print(f"  ⚠ Large train/test gap ({gap:.2%}) - possible overfitting")
    else:
        print(f"  ✅ Minimal train/test gap ({gap:.2%}) - good generalization")


def save_results(metrics: dict[str, float], config: dict) -> None:
    """Save evaluation results to JSON file."""
    print(f"\nSaving results to {RESULTS_FILE}...")

    results = {
        "metrics": metrics,
        "model_config": config,
        "evaluation_notes": {
            "masking_applied": True,
            "description": "Test metrics computed with train_interactions masking to prevent data leakage",
        },
    }

    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, indent=2)

    print(f"✅ Results saved to {RESULTS_FILE}")


def main() -> None:
    """Main evaluation pipeline."""
    print("=" * 60)
    print("MOVIE LIGHTFM MODEL EVALUATION")
    print("=" * 60 + "\n")

    try:
        # 1. Load saved artifacts
        model, item_features, train_interactions, test_interactions, config = (
            load_artifacts()
        )

        # 2. Evaluate with proper masking
        num_threads = max(os.cpu_count() or 4, 4)
        metrics = evaluate_model(
            model,
            train_interactions,
            test_interactions,
            item_features,
            k=10,
            num_threads=num_threads,
        )

        # 3. Print results
        print_results(metrics, k=10)

        # 4. Save results
        save_results(metrics, config)

        print("\n✅ Evaluation complete!")

    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        print("\nMake sure to run movie_training.py first to train the model.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        raise


if __name__ == "__main__":
    main()
