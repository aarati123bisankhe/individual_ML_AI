from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
FEATURE_DIR = BASE_DIR / "data" / "features"
MODEL_DIR = BASE_DIR / "models" / "scan_to_pay_risk_classifier"


FEATURE_COLUMNS = [
    "payment_attempts",
    "avg_payment_latency_ms",
    "max_payment_latency_ms",
    "retry_events",
    "failed_payment_events",
    "total_rescans",
    "failed_scan_items",
    "avg_scan_duration_ms",
    "max_scan_duration_ms",
    "scan_failure_rate",
    "rescan_rate",
    "checkout_complexity_score",
    "app_scan_share",
]

TRAIN_END = "2025-07-30"
VAL_END = "2025-11-30"


def sigmoid(z: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-np.clip(z, -35, 35)))


def build_target(df: pd.DataFrame) -> pd.Series:
    return (
        (df["payment_status"] != "success")
        | (df["retry_events"] > 0)
        | (df["failed_payment_events"] > 0)
        | (df["failed_scan_items"] > 0)
        | (df["total_rescans"] > 0)
    ).astype(int)


def load_dataset() -> pd.DataFrame:
    df = pd.read_csv(FEATURE_DIR / "transaction_features.csv", parse_dates=["entry_timestamp"])
    df = df[df["scan_to_pay_used"] == True].copy()
    df["target_risky_transaction"] = build_target(df)
    return df


def split_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = df[df["entry_timestamp"] <= pd.Timestamp(TRAIN_END)].copy()
    val = df[(df["entry_timestamp"] > pd.Timestamp(TRAIN_END)) & (df["entry_timestamp"] <= pd.Timestamp(VAL_END))].copy()
    test = df[df["entry_timestamp"] > pd.Timestamp(VAL_END)].copy()
    return train, val, test


def standardize(train_x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    means = train_x.mean(axis=0)
    stds = train_x.std(axis=0)
    stds[stds == 0] = 1.0
    return (train_x - means) / stds, means, stds


def apply_standardize(x: np.ndarray, means: np.ndarray, stds: np.ndarray) -> np.ndarray:
    return (x - means) / stds


def add_bias(x: np.ndarray) -> np.ndarray:
    return np.hstack([np.ones((len(x), 1)), x])


def train_logistic(x: np.ndarray, y: np.ndarray, epochs: int = 20, batch_size: int = 4096, lr: float = 0.08) -> np.ndarray:
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


def metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
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
        current = metrics(y_true, preds)
        if best_metrics is None or current["accuracy"] > best_metrics["accuracy"]:
            best_t = float(t)
            best_metrics = current
    return best_t, best_metrics


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    df = load_dataset()
    train_df, val_df, test_df = split_dataset(df)

    train_x_raw = train_df[FEATURE_COLUMNS].to_numpy(dtype=float)
    val_x_raw = val_df[FEATURE_COLUMNS].to_numpy(dtype=float)
    test_x_raw = test_df[FEATURE_COLUMNS].to_numpy(dtype=float)

    train_x, means, stds = standardize(train_x_raw)
    val_x = apply_standardize(val_x_raw, means, stds)
    test_x = apply_standardize(test_x_raw, means, stds)

    train_y = train_df["target_risky_transaction"].to_numpy(dtype=float)
    val_y = val_df["target_risky_transaction"].to_numpy(dtype=int)
    test_y = test_df["target_risky_transaction"].to_numpy(dtype=int)

    weights = train_logistic(train_x, train_y)
    val_probs = predict_probs(val_x, weights)
    test_probs = predict_probs(test_x, weights)

    threshold, val_metrics = best_threshold(val_y, val_probs)
    test_preds = (test_probs >= threshold).astype(int)
    test_metrics = metrics(test_y, test_preds)

    output = test_df[
        [
            "transaction_id",
            "customer_id",
            "store_id",
            "entry_timestamp",
            "payment_method",
            "payment_status",
            "payment_attempts",
            "retry_events",
            "failed_payment_events",
            "total_rescans",
            "failed_scan_items",
            "avg_payment_latency_ms",
            "avg_scan_duration_ms",
            "scan_failure_rate",
            "rescan_rate",
        ]
    ].copy()
    output["target_risky_transaction"] = test_y
    output["predicted_probability"] = np.round(test_probs, 4)
    output["predicted_class"] = test_preds
    output.to_csv(MODEL_DIR / "test_predictions.csv", index=False)

    pd.DataFrame({"feature": ["intercept"] + FEATURE_COLUMNS, "weight": weights}).to_csv(
        MODEL_DIR / "model_weights.csv", index=False
    )

    metadata = {
        "model_type": "logistic_scan_to_pay_risk_classifier",
        "feature_columns": FEATURE_COLUMNS,
        "selected_threshold": threshold,
        "train_rows": int(len(train_df)),
        "validation_rows": int(len(val_df)),
        "test_rows": int(len(test_df)),
        "validation_metrics": val_metrics,
        "test_metrics": test_metrics,
        "positive_rate_test": float(test_y.mean()),
    }
    (MODEL_DIR / "model_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    report = "\n".join(
        [
            "# Scan-to-Pay Risk Classification Summary",
            "",
            "- Model: `Logistic regression implemented with numpy`",
            "- Input: `data/features/transaction_features.csv`",
            "- Scope: only scan-to-pay transactions",
            "- Target: risky vs normal transaction based on retries, failed payments, rescans, and failed scans",
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
    (MODEL_DIR / "scan_to_pay_risk_report.md").write_text(report, encoding="utf-8")

    print(f"Scan-to-pay risk classifier outputs written to: {MODEL_DIR}")


if __name__ == "__main__":
    main()
