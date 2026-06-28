from __future__ import annotations

import json
import random
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
MODEL_DIR = BASE_DIR / "models" / "navigation_realistic_search"

STOPWORDS = {
    "per",
    "pack",
    "of",
    "premium",
    "single",
    "imported",
    "local",
    "pc",
    "piece",
    "kg",
    "g",
    "ml",
    "l",
}


def normalize(text: str) -> str:
    return " ".join(str(text).lower().replace("(", " ").replace(")", " ").replace("-", " ").split())


def tokenize(text: str) -> list[str]:
    return [token for token in normalize(text).split() if token not in STOPWORDS and not any(ch.isdigit() for ch in token)]


def build_partial_query(product_name: str) -> str:
    tokens = tokenize(product_name)
    if not tokens:
        return normalize(product_name)
    if len(tokens) == 1:
        return tokens[0]
    return " ".join(tokens[:2])


def build_misspelled_query(product_name: str) -> str:
    base = build_partial_query(product_name).replace(" ", "")
    if len(base) <= 4:
        return base[:-1] if len(base) > 2 else base
    chars = list(base)
    chars[1], chars[2] = chars[2], chars[1]
    return "".join(chars)


def build_category_query(subcategory: str) -> str:
    tokens = tokenize(subcategory)
    return " ".join(tokens[:2]) if tokens else normalize(subcategory)


def jaccard_score(query_tokens: set[str], product_tokens: set[str]) -> float:
    if not query_tokens or not product_tokens:
        return 0.0
    return len(query_tokens & product_tokens) / len(query_tokens | product_tokens)


def score_candidate(query: str, query_type: str, product_name: str, product_tokens: set[str], subcategory: str) -> float:
    norm_query = normalize(query)
    query_tokens = set(tokenize(query))
    name_norm = normalize(product_name)
    subcat_norm = normalize(subcategory)
    seq_name = SequenceMatcher(None, norm_query, name_norm).ratio()
    seq_subcat = SequenceMatcher(None, norm_query, subcat_norm).ratio()
    token_score = jaccard_score(query_tokens, product_tokens)

    if query_type == "exact":
        return 0.65 * seq_name + 0.35 * token_score
    if query_type == "partial":
        return 0.50 * seq_name + 0.50 * token_score
    if query_type == "misspelled":
        return 0.75 * seq_name + 0.25 * token_score
    return 0.35 * seq_name + 0.35 * token_score + 0.30 * seq_subcat


def build_query_dataset(products: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in products.iterrows():
        rows.append(
            {
                "store_id": row["store_id"],
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "subcategory": row["subcategory"],
                "zone_id": row["zone_id"],
                "aisle_id": row["aisle_id"],
                "shelf_number": row["shelf_number"],
                "shelf_position": row["shelf_position"],
                "query_type": "exact",
                "query_text": normalize(row["product_name"]),
            }
        )
        rows.append(
            {
                "store_id": row["store_id"],
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "subcategory": row["subcategory"],
                "zone_id": row["zone_id"],
                "aisle_id": row["aisle_id"],
                "shelf_number": row["shelf_number"],
                "shelf_position": row["shelf_position"],
                "query_type": "partial",
                "query_text": build_partial_query(row["product_name"]),
            }
        )
        rows.append(
            {
                "store_id": row["store_id"],
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "subcategory": row["subcategory"],
                "zone_id": row["zone_id"],
                "aisle_id": row["aisle_id"],
                "shelf_number": row["shelf_number"],
                "shelf_position": row["shelf_position"],
                "query_type": "misspelled",
                "query_text": build_misspelled_query(row["product_name"]),
            }
        )
        rows.append(
            {
                "store_id": row["store_id"],
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "subcategory": row["subcategory"],
                "zone_id": row["zone_id"],
                "aisle_id": row["aisle_id"],
                "shelf_number": row["shelf_number"],
                "shelf_position": row["shelf_position"],
                "query_type": "category",
                "query_text": build_category_query(row["subcategory"]),
            }
        )
    return pd.DataFrame(rows)


def predict_queries(products: pd.DataFrame, query_df: pd.DataFrame) -> pd.DataFrame:
    product_catalog = defaultdict(list)
    for _, row in products.iterrows():
        product_catalog[row["store_id"]].append(
            {
                "product_id": row["product_id"],
                "product_name": row["product_name"],
                "subcategory": row["subcategory"],
                "zone_id": row["zone_id"],
                "aisle_id": row["aisle_id"],
                "shelf_number": row["shelf_number"],
                "shelf_position": row["shelf_position"],
                "product_tokens": set(tokenize(row["product_name"])),
            }
        )

    outputs = []
    for _, row in query_df.iterrows():
        candidates = product_catalog[row["store_id"]]
        ranked = sorted(
            (
                {
                    **candidate,
                    "score": score_candidate(
                        row["query_text"],
                        row["query_type"],
                        candidate["product_name"],
                        candidate["product_tokens"],
                        candidate["subcategory"],
                    ),
                }
                for candidate in candidates
            ),
            key=lambda item: item["score"],
            reverse=True,
        )
        best = ranked[0]
        top3 = ranked[:3]
        outputs.append(
            {
                **row.to_dict(),
                "predicted_product_id": best["product_id"],
                "predicted_product_name": best["product_name"],
                "predicted_zone_id": best["zone_id"],
                "predicted_aisle_id": best["aisle_id"],
                "predicted_shelf_number": best["shelf_number"],
                "predicted_shelf_position": best["shelf_position"],
                "top1_score": round(best["score"], 4),
                "top1_product_match": best["product_id"] == row["product_id"],
                "top1_aisle_match": best["aisle_id"] == row["aisle_id"],
                "top1_zone_match": best["zone_id"] == row["zone_id"],
                "top3_contains_true_product": any(item["product_id"] == row["product_id"] for item in top3),
            }
        )
    return pd.DataFrame(outputs)


def summarize_by_query_type(predictions: pd.DataFrame) -> pd.DataFrame:
    summary = (
        predictions.groupby("query_type")
        .agg(
            total_queries=("query_text", "count"),
            top1_product_accuracy=("top1_product_match", "mean"),
            top1_aisle_accuracy=("top1_aisle_match", "mean"),
            top1_zone_accuracy=("top1_zone_match", "mean"),
            top3_product_accuracy=("top3_contains_true_product", "mean"),
        )
        .reset_index()
    )
    return summary


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    products = pd.read_csv(RAW_DIR / "products.csv")
    products["product_name"] = products["product_name"].astype(str)
    products["subcategory"] = products["subcategory"].astype(str)

    query_df = build_query_dataset(products)
    predictions = predict_queries(products, query_df)
    summary = summarize_by_query_type(predictions)

    overall = {
        "model_type": "fuzzy_navigation_product_locator",
        "overall_top1_product_accuracy": float(predictions["top1_product_match"].mean()),
        "overall_top1_aisle_accuracy": float(predictions["top1_aisle_match"].mean()),
        "overall_top1_zone_accuracy": float(predictions["top1_zone_match"].mean()),
        "overall_top3_product_accuracy": float(predictions["top3_contains_true_product"].mean()),
        "query_type_metrics": summary.to_dict(orient="records"),
    }

    predictions.to_csv(MODEL_DIR / "navigation_realistic_predictions.csv", index=False)
    summary.to_csv(MODEL_DIR / "navigation_query_type_summary.csv", index=False)
    (MODEL_DIR / "model_metadata.json").write_text(json.dumps(overall, indent=2), encoding="utf-8")

    lines = [
        "# Realistic Navigation Search Summary",
        "",
        "- Model: `Fuzzy product search and aisle locator`",
        "- Input: `products.csv` with synthetic realistic query variants",
        f"- Overall Top-1 product accuracy: `{overall['overall_top1_product_accuracy']:.4f}`",
        f"- Overall Top-1 aisle accuracy: `{overall['overall_top1_aisle_accuracy']:.4f}`",
        f"- Overall Top-3 product accuracy: `{overall['overall_top3_product_accuracy']:.4f}`",
        "",
        "## Query-Type Results",
        "",
    ]
    for _, row in summary.iterrows():
        lines.append(
            f"- `{row['query_type']}`: Top-1 product={row['top1_product_accuracy']:.4f}, "
            f"Top-1 aisle={row['top1_aisle_accuracy']:.4f}, Top-3 product={row['top3_product_accuracy']:.4f}"
        )
    (MODEL_DIR / "navigation_realistic_report.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Realistic navigation outputs written to: {MODEL_DIR}")


if __name__ == "__main__":
    main()
