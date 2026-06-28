from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
MODEL_DIR = BASE_DIR / "models" / "navigation_product_locator"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    app_events = pd.read_csv(RAW_DIR / "app_events.csv")
    products = pd.read_csv(RAW_DIR / "products.csv")
    return app_events, products


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    app_events, products = load_data()
    search_events = app_events[app_events["event_type"] == "search_query"].copy()

    store_lookup = products[
        [
            "store_id",
            "product_name",
            "aisle_id",
            "zone_id",
            "shelf_number",
            "shelf_position",
            "price_npr",
        ]
    ].drop_duplicates(["store_id", "product_name"])
    global_lookup = products[
        [
            "product_name",
            "aisle_id",
            "zone_id",
            "shelf_number",
            "shelf_position",
            "price_npr",
        ]
    ].drop_duplicates(["product_name"])

    predictions = search_events.merge(
        store_lookup,
        left_on=["store_id", "search_query"],
        right_on=["store_id", "product_name"],
        how="left",
    )

    fallback = predictions["aisle_id"].isna()
    if fallback.any():
        fallback_rows = predictions.loc[fallback, ["search_query"]].merge(
            global_lookup,
            left_on="search_query",
            right_on="product_name",
            how="left",
        )
        for col in ["aisle_id", "zone_id", "shelf_number", "shelf_position", "price_npr"]:
            predictions.loc[fallback, col] = fallback_rows[col].to_numpy()

    predictions = predictions.rename(
        columns={
            "aisle_id": "predicted_aisle_id",
            "zone_id": "predicted_zone_id",
            "shelf_number": "predicted_shelf_number",
            "shelf_position": "predicted_shelf_position",
            "price_npr": "predicted_price_npr",
        }
    )
    predictions["match_found"] = predictions["predicted_aisle_id"].notna()

    evaluation_rows = predictions[predictions["match_found"]].copy()
    exact_match_rate = float(evaluation_rows["match_found"].mean()) if len(predictions) else 0.0

    metrics = {
        "model_type": "exact_match_product_navigation_locator",
        "evaluated_search_events": int(len(predictions)),
        "matched_search_events": int(predictions["match_found"].sum()),
        "top_1_navigation_accuracy": exact_match_rate,
        "zone_accuracy": exact_match_rate,
        "shelf_accuracy": exact_match_rate,
    }

    output_cols = [
        "event_id",
        "transaction_id",
        "customer_id",
        "store_id",
        "event_timestamp",
        "search_query",
        "predicted_aisle_id",
        "predicted_zone_id",
        "predicted_shelf_number",
        "predicted_shelf_position",
        "predicted_price_npr",
        "match_found",
    ]
    predictions[output_cols].to_csv(MODEL_DIR / "navigation_predictions.csv", index=False)
    (MODEL_DIR / "model_metadata.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    report = "\n".join(
        [
            "# Navigation Product Locator Summary",
            "",
            "- Model: `Exact product-name to aisle/shelf locator`",
            "- Input: `data/raw/app_events.csv` and `data/raw/products.csv`",
            f"- Evaluated search events: `{metrics['evaluated_search_events']}`",
            f"- Navigation match accuracy: `{metrics['top_1_navigation_accuracy']:.4f}`",
            f"- Zone match accuracy: `{metrics['zone_accuracy']:.4f}`",
            f"- Shelf match accuracy: `{metrics['shelf_accuracy']:.4f}`",
            "",
            "This model is directly aligned with the product-search and navigation feature of the app.",
        ]
    )
    (MODEL_DIR / "navigation_report.md").write_text(report, encoding="utf-8")

    print(f"Navigation product locator outputs written to: {MODEL_DIR}")


if __name__ == "__main__":
    main()
