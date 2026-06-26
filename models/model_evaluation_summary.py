from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = BASE_DIR / "models"
SUMMARY_DIR = MODELS_DIR / "evaluation_summary"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pct_improvement(baseline: float, model: float) -> float:
    if baseline == 0:
        return 0.0
    return ((baseline - model) / baseline) * 100


def build_summary_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    seg = load_json(MODELS_DIR / "customer_segmentation" / "model_metadata.json")
    forecast = load_json(MODELS_DIR / "demand_forecasting" / "model_metadata.json")
    reco = load_json(MODELS_DIR / "recommendation_engine" / "model_metadata.json")
    anomaly = load_json(MODELS_DIR / "scan_to_pay_anomaly_detection" / "model_metadata.json")

    overview_rows = [
        {
            "model_name": "Customer Segmentation",
            "model_type": seg["model_type"],
            "dataset_used": "customer_features.csv",
            "primary_metric": "silhouette_score",
            "metric_value": round(seg["evaluation"][0]["silhouette_score"], 4),
            "notes": f"Chosen clusters: {seg['chosen_k']}",
        },
        {
            "model_name": "Demand Forecasting",
            "model_type": forecast["model_type"],
            "dataset_used": "daily_store_product_features.csv",
            "primary_metric": "test_rmse",
            "metric_value": round(forecast["test_model_metrics"]["rmse"], 4),
            "notes": f"Baseline RMSE: {forecast['test_baseline_metrics']['rmse']:.4f}",
        },
        {
            "model_name": "Recommendation Engine",
            "model_type": reco["model_type"],
            "dataset_used": "transaction_items_clean.csv",
            "primary_metric": "hit_rate_at_5",
            "metric_value": round(reco["evaluation_metrics"][1]["hit_rate"], 4),
            "notes": f"MRR@5: {reco['evaluation_metrics'][1]['mrr']:.4f}",
        },
        {
            "model_name": "Scan-to-Pay Anomaly Detection",
            "model_type": anomaly["model_type"],
            "dataset_used": "transaction_features.csv",
            "primary_metric": "precision_at_top_10pct",
            "metric_value": round(anomaly["test_ranking_metrics"][2]["precision_at_fraction"], 4),
            "notes": f"Recall@top10%: {anomaly['test_ranking_metrics'][2]['recall_at_fraction']:.4f}",
        },
    ]

    detail_rows = [
        {
            "model_name": "Customer Segmentation",
            "metric": "silhouette_score",
            "baseline": "",
            "model_value": round(seg["evaluation"][0]["silhouette_score"], 4),
            "improvement_pct": "",
            "interpretation": "Higher is better. Measures cluster separation and cohesion.",
        },
        {
            "model_name": "Demand Forecasting",
            "metric": "validation_rmse",
            "baseline": round(forecast["validation_baseline_metrics"]["rmse"], 4),
            "model_value": round(forecast["validation_model_metrics"]["rmse"], 4),
            "improvement_pct": round(
                pct_improvement(
                    forecast["validation_baseline_metrics"]["rmse"],
                    forecast["validation_model_metrics"]["rmse"],
                ),
                2,
            ),
            "interpretation": "Lower is better. Ridge model reduces forecast error on validation data.",
        },
        {
            "model_name": "Demand Forecasting",
            "metric": "test_rmse",
            "baseline": round(forecast["test_baseline_metrics"]["rmse"], 4),
            "model_value": round(forecast["test_model_metrics"]["rmse"], 4),
            "improvement_pct": round(
                pct_improvement(
                    forecast["test_baseline_metrics"]["rmse"],
                    forecast["test_model_metrics"]["rmse"],
                ),
                2,
            ),
            "interpretation": "Lower is better. Main forecasting result on unseen test data.",
        },
        {
            "model_name": "Demand Forecasting",
            "metric": "test_mae",
            "baseline": round(forecast["test_baseline_metrics"]["mae"], 4),
            "model_value": round(forecast["test_model_metrics"]["mae"], 4),
            "improvement_pct": round(
                pct_improvement(
                    forecast["test_baseline_metrics"]["mae"],
                    forecast["test_model_metrics"]["mae"],
                ),
                2,
            ),
            "interpretation": "Lower is better. Measures average absolute daily forecast error.",
        },
        {
            "model_name": "Recommendation Engine",
            "metric": "hit_rate_at_3",
            "baseline": "",
            "model_value": round(reco["evaluation_metrics"][0]["hit_rate"], 4),
            "improvement_pct": "",
            "interpretation": "Higher is better. True item appears in top 3 recommendations.",
        },
        {
            "model_name": "Recommendation Engine",
            "metric": "hit_rate_at_5",
            "baseline": "",
            "model_value": round(reco["evaluation_metrics"][1]["hit_rate"], 4),
            "improvement_pct": "",
            "interpretation": "Higher is better. True item appears in top 5 recommendations.",
        },
        {
            "model_name": "Recommendation Engine",
            "metric": "mrr_at_5",
            "baseline": "",
            "model_value": round(reco["evaluation_metrics"][1]["mrr"], 4),
            "improvement_pct": "",
            "interpretation": "Higher is better. Rewards correct recommendations appearing earlier.",
        },
        {
            "model_name": "Scan-to-Pay Anomaly Detection",
            "metric": "precision_at_top_5pct",
            "baseline": "",
            "model_value": round(anomaly["test_ranking_metrics"][1]["precision_at_fraction"], 4),
            "improvement_pct": "",
            "interpretation": "Higher is better. Measures anomaly quality among the top-ranked flagged transactions.",
        },
        {
            "model_name": "Scan-to-Pay Anomaly Detection",
            "metric": "precision_at_top_10pct",
            "baseline": "",
            "model_value": round(anomaly["test_ranking_metrics"][2]["precision_at_fraction"], 4),
            "improvement_pct": "",
            "interpretation": "Higher is better. Useful for prioritized operational review.",
        },
        {
            "model_name": "Scan-to-Pay Anomaly Detection",
            "metric": "threshold_precision",
            "baseline": "",
            "model_value": round(anomaly["test_threshold_metrics"]["precision"], 4),
            "improvement_pct": "",
            "interpretation": "Higher is better. Precision of binary anomaly alerts at the selected threshold.",
        },
    ]

    return pd.DataFrame(overview_rows), pd.DataFrame(detail_rows)


def write_markdown_report(overview: pd.DataFrame, details: pd.DataFrame) -> None:
    lines = []
    lines.append("# Model Evaluation Summary")
    lines.append("")
    lines.append("This report combines the main evaluation results for all current ML models in the project.")
    lines.append("")
    lines.append("## Model Overview")
    lines.append("")
    lines.append("| Model | Type | Dataset | Primary Metric | Value |")
    lines.append("|------|------|---------|----------------|------:|")
    for _, row in overview.iterrows():
        lines.append(
            f"| {row['model_name']} | {row['model_type']} | {row['dataset_used']} | {row['primary_metric']} | {row['metric_value']} |"
        )
    lines.append("")
    lines.append("## Key Findings")
    lines.append("")
    for _, row in details.iterrows():
        baseline = row["baseline"]
        if baseline == "":
            lines.append(
                f"- {row['model_name']} `{row['metric']}` = {row['model_value']}. {row['interpretation']}"
            )
        else:
            lines.append(
                f"- {row['model_name']} `{row['metric']}` improved from {row['baseline']} to {row['model_value']} "
                f"({row['improvement_pct']}% better). {row['interpretation']}"
            )
    lines.append("")
    lines.append("## Thesis Interpretation")
    lines.append("")
    lines.append("- Customer segmentation produced meaningful groups with a silhouette score above 0.32, which is a reasonable first clustering result.")
    lines.append("- Demand forecasting outperformed the naive baseline on validation and test data, showing that engineered features improved prediction quality.")
    lines.append("- The recommendation engine achieved useful top-k hit rates for a baseline market-basket model and can be improved later with more advanced methods.")
    lines.append("- The anomaly detector is most useful as a ranked alerting model, where the top flagged scan-to-pay transactions show much higher anomaly concentration than the full dataset.")
    (SUMMARY_DIR / "model_evaluation_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    overview, details = build_summary_tables()
    overview.to_csv(SUMMARY_DIR / "model_overview.csv", index=False)
    details.to_csv(SUMMARY_DIR / "model_metrics_detailed.csv", index=False)
    write_markdown_report(overview, details)
    print(f"Evaluation summary written to: {SUMMARY_DIR}")


if __name__ == "__main__":
    main()
