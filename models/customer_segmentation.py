from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
FEATURE_DIR = BASE_DIR / "data" / "features"
MODEL_DIR = BASE_DIR / "models" / "customer_segmentation"


NUMERIC_FEATURES = [
    "transaction_count",
    "total_spend_npr",
    "avg_order_value_npr",
    "total_units",
    "avg_basket_size",
    "avg_dwell_minutes",
    "avg_aisles_visited",
    "scan_to_pay_rate",
    "payment_success_rate",
    "app_searches_total",
    "app_directions_total",
    "festival_transaction_count",
    "unique_products_bought",
    "customer_tenure_days",
    "recency_days",
    "spend_per_visit_npr",
    "app_engagement_events",
]


def load_dataset() -> pd.DataFrame:
    return pd.read_csv(FEATURE_DIR / "customer_features.csv", parse_dates=["registered_on", "first_purchase_at", "last_purchase_at"])


def standardize_frame(df: pd.DataFrame, columns: list[str]) -> tuple[np.ndarray, dict[str, dict[str, float]]]:
    frame = df[columns].astype(float).copy()
    stats = {}
    for col in columns:
        mean = float(frame[col].mean())
        std = float(frame[col].std(ddof=0))
        if std == 0:
            std = 1.0
        frame[col] = (frame[col] - mean) / std
        stats[col] = {"mean": mean, "std": std}
    return frame.to_numpy(dtype=float), stats


def initialize_centroids(x: np.ndarray, k: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    indices = rng.choice(len(x), size=1, replace=False)
    centroids = [x[indices[0]]]

    while len(centroids) < k:
        distances = np.min(
            np.vstack([np.sum((x - centroid) ** 2, axis=1) for centroid in centroids]),
            axis=0,
        )
        probs = distances / distances.sum()
        next_index = rng.choice(len(x), p=probs)
        centroids.append(x[next_index])

    return np.vstack(centroids)


def run_kmeans(x: np.ndarray, k: int, seed: int = 42, max_iter: int = 100) -> tuple[np.ndarray, np.ndarray, float]:
    centroids = initialize_centroids(x, k, seed)
    labels = np.zeros(len(x), dtype=int)

    for _ in range(max_iter):
        distances = np.linalg.norm(x[:, None, :] - centroids[None, :, :], axis=2)
        new_labels = distances.argmin(axis=1)
        new_centroids = centroids.copy()

        for cluster_id in range(k):
            cluster_points = x[new_labels == cluster_id]
            if len(cluster_points) > 0:
                new_centroids[cluster_id] = cluster_points.mean(axis=0)

        if np.array_equal(new_labels, labels):
            centroids = new_centroids
            labels = new_labels
            break

        labels = new_labels
        centroids = new_centroids

    inertia = float(np.sum((x - centroids[labels]) ** 2))
    return labels, centroids, inertia


def silhouette_score(x: np.ndarray, labels: np.ndarray, sample_size: int = 1500, seed: int = 42) -> float:
    unique_labels = np.unique(labels)
    if len(unique_labels) < 2:
        return -1.0

    if len(x) > sample_size:
        rng = np.random.default_rng(seed)
        sample_indices = rng.choice(len(x), size=sample_size, replace=False)
        x = x[sample_indices]
        labels = labels[sample_indices]

    distances = np.linalg.norm(x[:, None, :] - x[None, :, :], axis=2)
    scores = []

    for idx in range(len(x)):
        same_cluster = labels == labels[idx]
        same_cluster[idx] = False

        if same_cluster.sum() == 0:
            a = 0.0
        else:
            a = float(distances[idx, same_cluster].mean())

        b_values = []
        for other_label in unique_labels:
            if other_label == labels[idx]:
                continue
            other_cluster = labels == other_label
            if other_cluster.sum() > 0:
                b_values.append(float(distances[idx, other_cluster].mean()))
        b = min(b_values) if b_values else 0.0

        denom = max(a, b)
        score = 0.0 if denom == 0 else (b - a) / denom
        scores.append(score)

    return float(np.mean(scores))


def pick_best_k(x: np.ndarray, candidate_ks: list[int]) -> tuple[int, list[dict[str, float]]]:
    evaluations = []
    best = None
    for k in candidate_ks:
        labels, centroids, inertia = run_kmeans(x, k, seed=42)
        sil = silhouette_score(x, labels)
        entry = {
            "k": k,
            "inertia": inertia,
            "silhouette_score": sil,
        }
        evaluations.append(entry)
        if best is None or sil > best["silhouette_score"]:
            best = {**entry, "labels": labels, "centroids": centroids}
    return int(best["k"]), evaluations


def assign_segment_names(summary: pd.DataFrame) -> dict[int, str]:
    ranked = summary.sort_values(["total_spend_npr_mean", "transaction_count_mean"], ascending=[False, False]).reset_index(drop=True)
    names = [
        "High Value Loyal Customers",
        "Regular Digital Shoppers",
        "Occasional Traditional Shoppers",
        "Low Engagement Customers",
        "Dormant Customers",
        "Mixed Behavior Customers",
    ]
    mapping = {}
    for idx, row in ranked.iterrows():
        mapping[int(row["segment_id"])] = names[idx] if idx < len(names) else f"Customer Segment {idx + 1}"
    return mapping


def build_segment_summary(df: pd.DataFrame, segment_col: str) -> pd.DataFrame:
    summary = (
        df.groupby(segment_col)
        .agg(
            customer_count=("customer_id", "count"),
            transaction_count_mean=("transaction_count", "mean"),
            total_spend_npr_mean=("total_spend_npr", "mean"),
            avg_order_value_npr_mean=("avg_order_value_npr", "mean"),
            total_units_mean=("total_units", "mean"),
            avg_basket_size_mean=("avg_basket_size", "mean"),
            scan_to_pay_rate_mean=("scan_to_pay_rate", "mean"),
            app_engagement_events_mean=("app_engagement_events", "mean"),
            recency_days_mean=("recency_days", "mean"),
            preferred_payment_method_mode=("preferred_payment_method", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
            loyalty_tier_mode=("loyalty_tier", lambda s: s.mode().iloc[0] if not s.mode().empty else "Unknown"),
        )
        .reset_index()
        .rename(columns={segment_col: "segment_id"})
    )
    return summary


def write_markdown_report(summary: pd.DataFrame, chosen_k: int, evaluations: list[dict[str, float]]) -> None:
    lines = []
    lines.append("# Customer Segmentation Model Summary")
    lines.append("")
    lines.append(f"- Chosen number of clusters: `{chosen_k}`")
    lines.append("- Algorithm: `K-Means clustering implemented with numpy`")
    lines.append("- Input table: `data/features/customer_features.csv`")
    lines.append("- Output table: `models/customer_segmentation/customer_segments.csv`")
    lines.append("")
    lines.append("## K Evaluation")
    lines.append("")
    lines.append("| k | Inertia | Silhouette Score |")
    lines.append("|---|---------|------------------|")
    for item in evaluations:
        lines.append(f"| {item['k']} | {item['inertia']:.2f} | {item['silhouette_score']:.4f} |")
    lines.append("")
    lines.append("## Segment Summary")
    lines.append("")
    for _, row in summary.iterrows():
        lines.append(f"### Segment {int(row['segment_id'])}: {row['segment_name']}")
        lines.append(f"- Customers: {int(row['customer_count'])}")
        lines.append(f"- Avg transactions: {row['transaction_count_mean']:.2f}")
        lines.append(f"- Avg spend (NPR): {row['total_spend_npr_mean']:.2f}")
        lines.append(f"- Avg order value (NPR): {row['avg_order_value_npr_mean']:.2f}")
        lines.append(f"- Avg basket size: {row['avg_basket_size_mean']:.2f}")
        lines.append(f"- Avg scan-to-pay rate: {row['scan_to_pay_rate_mean']:.2f}")
        lines.append(f"- Avg app engagement events: {row['app_engagement_events_mean']:.2f}")
        lines.append(f"- Avg recency days: {row['recency_days_mean']:.2f}")
        lines.append(f"- Most common payment method: {row['preferred_payment_method_mode']}")
        lines.append(f"- Most common loyalty tier: {row['loyalty_tier_mode']}")
        lines.append("")

    (MODEL_DIR / "customer_segmentation_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    df = load_dataset()
    x, stats = standardize_frame(df, NUMERIC_FEATURES)
    chosen_k, evaluations = pick_best_k(x, [3, 4, 5, 6])
    labels, centroids, inertia = run_kmeans(x, chosen_k, seed=42)

    df["segment_id"] = labels
    segment_summary = build_segment_summary(df, "segment_id")
    name_map = assign_segment_names(segment_summary)
    df["segment_name"] = df["segment_id"].map(name_map)
    segment_summary["segment_name"] = segment_summary["segment_id"].map(name_map)
    segment_summary = segment_summary.sort_values("segment_id").reset_index(drop=True)

    centroids_df = pd.DataFrame(centroids, columns=NUMERIC_FEATURES)
    centroids_df.insert(0, "segment_id", range(chosen_k))
    centroids_df["segment_name"] = centroids_df["segment_id"].map(name_map)

    output_columns = [
        "customer_id",
        "segment_id",
        "segment_name",
        "loyalty_tier",
        "uses_app",
        "transaction_count",
        "total_spend_npr",
        "avg_order_value_npr",
        "recency_days",
        "scan_to_pay_rate",
        "app_engagement_events",
        "preferred_store_id",
        "preferred_payment_method",
        "favorite_subcategory",
    ]
    df[output_columns].to_csv(MODEL_DIR / "customer_segments.csv", index=False)
    segment_summary.to_csv(MODEL_DIR / "segment_summary.csv", index=False)
    centroids_df.to_csv(MODEL_DIR / "segment_centroids_scaled.csv", index=False)

    metadata = {
        "model_type": "kmeans_customer_segmentation",
        "chosen_k": chosen_k,
        "inertia": inertia,
        "evaluation": evaluations,
        "numeric_features": NUMERIC_FEATURES,
        "scaling_stats": stats,
    }
    (MODEL_DIR / "model_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    write_markdown_report(segment_summary, chosen_k, evaluations)

    print(f"Customer segmentation outputs written to: {MODEL_DIR}")


if __name__ == "__main__":
    main()
