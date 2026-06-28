from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
FEATURE_DIR = BASE_DIR / "data" / "features"
MODEL_DIR = BASE_DIR / "models" / "inventory_demand_classifier"


FEATURE_COLUMNS = [
    "price_npr",
    "units_sold",
    "transaction_count",
    "is_festival_period",
    "day_of_week",
    "month",
    "is_weekend",
    "units_lag_1d",
    "units_rolling_7d",
    "units_rolling_14d",
]

TRAIN_END = "2025-07-30"
VAL_END = "2025-11-30"


def sigmoid(z: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-np.clip(z, -35, 35)))


def load_dataset() -> pd.DataFrame:
    df = pd.read_csv(FEATURE_DIR / "daily_store_product_features.csv", parse_dates=["sales_date"])
    df["target_has_demand"] = (df["target_next_day_units"] > 0).astype(int)
    df["is_festival_period"] = df["is_festival_period"].astype(int)
    df["is_weekend"] = df["is_weekend"].astype(int)
    return df


def split_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = df[df["sales_date"] <= pd.Timestamp(TRAIN_END)].copy()
    val = df[(df["sales_date"] > pd.Timestamp(TRAIN_END)) & (df["sales_date"] <= pd.Timestamp(VAL_END))].copy()
    test = df[df["sales_date"] > pd.Timestamp(VAL_END)].copy()
    return train, val, test


def prepare_x(df: pd.DataFrame) -> np.ndarray:
    return df[FEATURE_COLUMNS].to_numpy(dtype=float)


def standardize(train_x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    means = train_x.mean(axis=0)
    stds = train_x.std(axis=0)
    stds[stds == 0] = 1.0
    return (train_x - means) / stds, means, stds


def apply_standardize(x: np.ndarray, means: np.ndarray, stds: np.ndarray) -> np.ndarray:
    return (x - means) / stds


def add_bias(x: np.ndarray) -> np.ndarray:
    return np.hstack([np.ones((len(x), 1)), x])


def train_logistic_regression(
    x: np.ndarray,
    y: np.ndarray,
    epochs: int = 8,
    batch_size: int = 65536,
    lr: float = 0.08,
) -> np.ndarray:
    xb = add_bias(x)
    weights = np.zeros(xb.shape[1], dtype=float)

    for _ in range(epochs):
        for start in range(0, len(xb), batch_size):
            end = start + batch_size
            batch_x = xb[start:end]
            batch_y = y[start:end]
            preds = sigmoid(batch_x @ weights)
            grad = (batch_x.T @ (preds - batch_y)) / len(batch_x)
            weights -= lr * grad

    return weights


def predict_probs(x: np.ndarray, weights: np.ndarray) -> np.ndarray:
    return sigmoid(add_bias(x) @ weights)


def classification_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    accuracy = (tp + tn) / len(y_true) if len(y_true) else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def best_threshold(y_true: np.ndarray, probs: np.ndarray) -> tuple[float, dict[str, float]]:
    best_t = 0.5
    best_metrics = None
    for t in np.arange(0.30, 0.71, 0.05):
        preds = (probs >= t).astype(int)
        metrics = classification_metrics(y_true, preds)
        if best_metrics is None or metrics["accuracy"] > best_metrics["accuracy"]:
            best_t = float(t)
            best_metrics = metrics
    return best_t, best_metrics


def write_report(
    val_metrics: dict[str, float],
    test_metrics: dict[str, float],
    threshold: float,
    train_rows: int,
    val_rows: int,
    test_rows: int,
) -> None:
    text = "\n".join(
        [
            "# Inventory Demand Classification Summary",
            "",
            "- Model: `Logistic regression implemented with numpy`",
            "- Input: `data/features/daily_store_product_features.csv`",
            "- Target: `target_has_demand` where 1 means next-day demand is greater than zero",
            f"- Train rows: `{train_rows}`",
            f"- Validation rows: `{val_rows}`",
            f"- Test rows: `{test_rows}`",
            f"- Selected threshold: `{threshold:.2f}`",
            "",
            "## Validation Metrics",
            f"- Accuracy: {val_metrics['accuracy']:.4f}",
            f"- Precision: {val_metrics['precision']:.4f}",
            f"- Recall: {val_metrics['recall']:.4f}",
            f"- F1-score: {val_metrics['f1_score']:.4f}",
            "",
            "## Test Metrics",
            f"- Accuracy: {test_metrics['accuracy']:.4f}",
            f"- Precision: {test_metrics['precision']:.4f}",
            f"- Recall: {test_metrics['recall']:.4f}",
            f"- F1-score: {test_metrics['f1_score']:.4f}",
        ]
    )
    (MODEL_DIR / "inventory_demand_report.md").write_text(text, encoding="utf-8")


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    df = load_dataset()
    train_df, val_df, test_df = split_dataset(df)

    train_x_raw = prepare_x(train_df)
    val_x_raw = prepare_x(val_df)
    test_x_raw = prepare_x(test_df)

    train_x, means, stds = standardize(train_x_raw)
    val_x = apply_standardize(val_x_raw, means, stds)
    test_x = apply_standardize(test_x_raw, means, stds)

    train_y = train_df["target_has_demand"].to_numpy(dtype=float)
    val_y = val_df["target_has_demand"].to_numpy(dtype=int)
    test_y = test_df["target_has_demand"].to_numpy(dtype=int)

    weights = train_logistic_regression(train_x, train_y)

    val_probs = predict_probs(val_x, weights)
    test_probs = predict_probs(test_x, weights)
    threshold, val_metrics = best_threshold(val_y, val_probs)
    test_preds = (test_probs >= threshold).astype(int)
    test_metrics = classification_metrics(test_y, test_preds)

    predictions = test_df[
        [
            "sales_date",
            "store_id",
            "product_id",
            "units_sold",
            "units_lag_1d",
            "units_rolling_7d",
            "units_rolling_14d",
            "target_next_day_units",
            "target_has_demand",
        ]
    ].copy()
    predictions["predicted_probability"] = np.round(test_probs, 4)
    predictions["predicted_class"] = test_preds
    predictions.to_csv(MODEL_DIR / "test_predictions.csv", index=False)

    weights_df = pd.DataFrame(
        {"feature": ["intercept"] + FEATURE_COLUMNS, "weight": weights}
    )
    weights_df.to_csv(MODEL_DIR / "model_weights.csv", index=False)

    metadata = {
        "model_type": "logistic_inventory_demand_classifier",
        "target_definition": "target_next_day_units > 0",
        "feature_columns": FEATURE_COLUMNS,
        "selected_threshold": threshold,
        "train_rows": int(len(train_df)),
        "validation_rows": int(len(val_df)),
        "test_rows": int(len(test_df)),
        "validation_metrics": val_metrics,
        "test_metrics": test_metrics,
        "feature_means": means.tolist(),
        "feature_stds": stds.tolist(),
    }
    (MODEL_DIR / "model_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    write_report(val_metrics, test_metrics, threshold, len(train_df), len(val_df), len(test_df))

    print(f"Inventory demand classifier outputs written to: {MODEL_DIR}")


if __name__ == "__main__":
    main()
