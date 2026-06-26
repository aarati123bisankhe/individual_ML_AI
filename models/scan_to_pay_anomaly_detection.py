from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
FEATURE_DIR = BASE_DIR / "data" / "features"
MODEL_DIR = BASE_DIR / "models" / "scan_to_pay_anomaly_detection"


ANOMALY_FEATURES = [
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
]

TRAIN_END = "2025-07-30"
VAL_END = "2025-11-30"


def load_dataset() -> pd.DataFrame:
    df = pd.read_csv(FEATURE_DIR / "transaction_features.csv", parse_dates=["entry_timestamp"])
    return df[df["scan_to_pay_used"] == True].copy()


def split_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = df[df["entry_timestamp"] <= pd.Timestamp(TRAIN_END)].copy()
    val = df[(df["entry_timestamp"] > pd.Timestamp(TRAIN_END)) & (df["entry_timestamp"] <= pd.Timestamp(VAL_END))].copy()
    test = df[df["entry_timestamp"] > pd.Timestamp(VAL_END)].copy()
    return train, val, test


def build_proxy_label(df: pd.DataFrame) -> pd.Series:
    return (
        (df["payment_status"] == "failed")
        | (df["failed_payment_events"] > 0)
        | (df["retry_events"] > 0)
        | (df["failed_scan_items"] > 0)
        | (df["total_rescans"] >= 2)
        | (df["scan_failure_rate"] > 0)
    )


def robust_stats(train: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    median = train[ANOMALY_FEATURES].median()
    mad = (train[ANOMALY_FEATURES] - median).abs().median()
    mad = mad.replace(0, 1.0)
    return median, mad


def anomaly_score(df: pd.DataFrame, median: pd.Series, mad: pd.Series) -> pd.Series:
    robust_z = ((df[ANOMALY_FEATURES] - median).abs() / mad).fillna(0)
    weighted = robust_z.copy()
    if "failed_payment_events" in weighted:
        weighted["failed_payment_events"] *= 2.5
    if "failed_scan_items" in weighted:
        weighted["failed_scan_items"] *= 2.0
    if "retry_events" in weighted:
        weighted["retry_events"] *= 1.8
    if "payment_attempts" in weighted:
        weighted["payment_attempts"] *= 1.4
    return weighted.sum(axis=1)


def evaluate_scores(scores: pd.Series, labels: pd.Series, top_fractions: list[float]) -> list[dict[str, float]]:
    ranked = pd.DataFrame({"score": scores, "label": labels.astype(int)}).sort_values("score", ascending=False)
    total_anomalies = max(int(ranked["label"].sum()), 1)
    rows = []

    for frac in top_fractions:
        k = max(int(len(ranked) * frac), 1)
        top = ranked.head(k)
        tp = int(top["label"].sum())
        precision = tp / k if k else 0.0
        recall = tp / total_anomalies if total_anomalies else 0.0
        rows.append(
            {
                "top_fraction": frac,
                "evaluated_rows": k,
                "precision_at_fraction": precision,
                "recall_at_fraction": recall,
            }
        )
    return rows


def threshold_from_validation(scores: pd.Series) -> float:
    return float(scores.quantile(0.95))


def classification_summary(scores: pd.Series, labels: pd.Series, threshold: float) -> dict[str, float]:
    preds = scores >= threshold
    labels = labels.astype(bool)
    tp = int((preds & labels).sum())
    fp = int((preds & ~labels).sum())
    fn = int((~preds & labels).sum())
    tn = int((~preds & ~labels).sum())
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    accuracy = (tp + tn) / len(labels) if len(labels) else 0.0
    return {
        "threshold": threshold,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "accuracy": accuracy,
    }


def write_markdown_report(
    val_eval: list[dict[str, float]],
    test_eval: list[dict[str, float]],
    test_summary: dict[str, float],
    positive_rate: float,
) -> None:
    lines = []
    lines.append("# Scan-to-Pay Anomaly Detection Summary")
    lines.append("")
    lines.append("- Model: `Robust z-score anomaly scoring`")
    lines.append("- Input table: `data/features/transaction_features.csv`")
    lines.append("- Scope: only transactions where `scan_to_pay_used = True`")
    lines.append("- Evaluation label: proxy anomaly label based on failed payments, retries, failed scans, and rescans")
    lines.append(f"- Proxy anomaly rate in test set: `{positive_rate:.4f}`")
    lines.append("")
    lines.append("## Validation Ranking Quality")
    lines.append("")
    lines.append("| Top Fraction | Rows Checked | Precision | Recall |")
    lines.append("|-------------:|-------------:|----------:|-------:|")
    for row in val_eval:
        lines.append(
            f"| {row['top_fraction']:.2f} | {int(row['evaluated_rows'])} | {row['precision_at_fraction']:.4f} | {row['recall_at_fraction']:.4f} |"
        )
    lines.append("")
    lines.append("## Test Ranking Quality")
    lines.append("")
    lines.append("| Top Fraction | Rows Checked | Precision | Recall |")
    lines.append("|-------------:|-------------:|----------:|-------:|")
    for row in test_eval:
        lines.append(
            f"| {row['top_fraction']:.2f} | {int(row['evaluated_rows'])} | {row['precision_at_fraction']:.4f} | {row['recall_at_fraction']:.4f} |"
        )
    lines.append("")
    lines.append("## Threshold-Based Test Classification")
    lines.append("")
    lines.append(f"- Threshold: {test_summary['threshold']:.4f}")
    lines.append(f"- Precision: {test_summary['precision']:.4f}")
    lines.append(f"- Recall: {test_summary['recall']:.4f}")
    lines.append(f"- Accuracy: {test_summary['accuracy']:.4f}")
    (MODEL_DIR / "anomaly_detection_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    df = load_dataset()
    train_df, val_df, test_df = split_dataset(df)

    median, mad = robust_stats(train_df)
    train_scores = anomaly_score(train_df, median, mad)
    val_scores = anomaly_score(val_df, median, mad)
    test_scores = anomaly_score(test_df, median, mad)

    train_labels = build_proxy_label(train_df)
    val_labels = build_proxy_label(val_df)
    test_labels = build_proxy_label(test_df)

    threshold = threshold_from_validation(val_scores)

    val_eval = evaluate_scores(val_scores, val_labels, [0.01, 0.05, 0.10])
    test_eval = evaluate_scores(test_scores, test_labels, [0.01, 0.05, 0.10])
    test_summary = classification_summary(test_scores, test_labels, threshold)

    test_output = test_df[
        [
            "transaction_id",
            "customer_id",
            "store_id",
            "entry_timestamp",
            "grand_total_npr",
            "payment_method",
            "payment_attempts",
            "payment_status",
            "total_rescans",
            "failed_scan_items",
            "retry_events",
            "failed_payment_events",
            "avg_payment_latency_ms",
            "avg_scan_duration_ms",
            "scan_failure_rate",
            "rescan_rate",
            "checkout_complexity_score",
        ]
    ].copy()
    test_output["proxy_anomaly_label"] = test_labels.astype(int).to_numpy()
    test_output["anomaly_score"] = np.round(test_scores.to_numpy(), 4)
    test_output["predicted_anomaly"] = (test_scores >= threshold).to_numpy()
    test_output = test_output.sort_values("anomaly_score", ascending=False)
    test_output.to_csv(MODEL_DIR / "test_anomaly_scores.csv", index=False)

    pd.DataFrame(val_eval).to_csv(MODEL_DIR / "validation_metrics.csv", index=False)
    pd.DataFrame(test_eval).to_csv(MODEL_DIR / "test_metrics.csv", index=False)

    metadata = {
        "model_type": "robust_zscore_scan_to_pay_anomaly_detection",
        "feature_columns": ANOMALY_FEATURES,
        "train_rows": int(len(train_df)),
        "validation_rows": int(len(val_df)),
        "test_rows": int(len(test_df)),
        "threshold": threshold,
        "validation_ranking_metrics": val_eval,
        "test_ranking_metrics": test_eval,
        "test_threshold_metrics": test_summary,
        "test_proxy_anomaly_rate": float(test_labels.mean()),
        "train_proxy_anomaly_rate": float(train_labels.mean()),
    }
    (MODEL_DIR / "model_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    write_markdown_report(val_eval, test_eval, test_summary, float(test_labels.mean()))

    print(f"Scan-to-pay anomaly detection outputs written to: {MODEL_DIR}")


if __name__ == "__main__":
    main()
