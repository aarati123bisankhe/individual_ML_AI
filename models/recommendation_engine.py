from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
FEATURE_DIR = BASE_DIR / "data" / "features"
MODEL_DIR = BASE_DIR / "models" / "recommendation_engine"


TRAIN_END = "2025-07-30"
VAL_END = "2025-11-30"
TOP_K_VALUES = [3, 5]


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    items = pd.read_csv(PROCESSED_DIR / "transaction_items_clean.csv")
    transactions = pd.read_csv(
        PROCESSED_DIR / "transactions_clean.csv",
        parse_dates=["entry_timestamp"],
    )
    products = pd.read_csv(FEATURE_DIR / "product_features.csv")
    return items, transactions, products


def split_transactions(transactions: pd.DataFrame) -> tuple[set[str], set[str], set[str]]:
    train_ids = set(transactions.loc[transactions["entry_timestamp"] <= pd.Timestamp(TRAIN_END), "transaction_id"])
    val_ids = set(
        transactions.loc[
            (transactions["entry_timestamp"] > pd.Timestamp(TRAIN_END))
            & (transactions["entry_timestamp"] <= pd.Timestamp(VAL_END)),
            "transaction_id",
        ]
    )
    test_ids = set(transactions.loc[transactions["entry_timestamp"] > pd.Timestamp(VAL_END), "transaction_id"])
    return train_ids, val_ids, test_ids


def build_baskets(items: pd.DataFrame, transaction_ids: set[str]) -> list[list[str]]:
    subset = items[items["transaction_id"].isin(transaction_ids)].copy()
    grouped = (
        subset.groupby("transaction_id")["product_id"]
        .apply(lambda s: sorted(set(s.tolist())))
        .tolist()
    )
    return [basket for basket in grouped if len(basket) >= 2]


def train_item_cooccurrence(baskets: list[list[str]]) -> tuple[dict[str, Counter], Counter]:
    pair_counts: dict[str, Counter] = defaultdict(Counter)
    product_counts: Counter = Counter()

    for basket in baskets:
        unique_items = sorted(set(basket))
        for item in unique_items:
            product_counts[item] += 1
        for item in unique_items:
            for other in unique_items:
                if item == other:
                    continue
                pair_counts[item][other] += 1

    return pair_counts, product_counts


def popularity_rank(product_counts: Counter) -> list[str]:
    return [product for product, _ in product_counts.most_common()]


def recommend_for_basket(
    basket: list[str],
    pair_counts: dict[str, Counter],
    product_counts: Counter,
    top_k: int,
) -> list[str]:
    scores: Counter = Counter()
    basket_set = set(basket)
    for item in basket:
        for other, count in pair_counts.get(item, {}).items():
            if other in basket_set:
                continue
            support_item = max(product_counts[item], 1)
            scores[other] += count / support_item

    ranked = [product for product, _ in scores.most_common(top_k)]

    if len(ranked) < top_k:
        for product, _ in product_counts.most_common():
            if product not in basket_set and product not in ranked:
                ranked.append(product)
            if len(ranked) == top_k:
                break

    return ranked[:top_k]


def evaluate_recommender(
    baskets: list[list[str]],
    pair_counts: dict[str, Counter],
    product_counts: Counter,
) -> tuple[list[dict[str, float]], list[dict[str, object]]]:
    metric_rows = []
    example_rows = []

    for k in TOP_K_VALUES:
        hits = 0
        total = 0
        reciprocal_ranks = []

        for basket in baskets:
            if len(basket) < 2:
                continue
            context = basket[:-1]
            actual_next = basket[-1]
            recommendations = recommend_for_basket(context, pair_counts, product_counts, k)
            total += 1
            if actual_next in recommendations:
                hits += 1
                reciprocal_ranks.append(1.0 / (recommendations.index(actual_next) + 1))
            else:
                reciprocal_ranks.append(0.0)

            if len(example_rows) < 15 and k == 5:
                example_rows.append(
                    {
                        "context_products": " | ".join(context),
                        "actual_next_product": actual_next,
                        "recommended_products": " | ".join(recommendations),
                        "hit": actual_next in recommendations,
                    }
                )

        metric_rows.append(
            {
                "top_k": k,
                "evaluated_baskets": total,
                "hit_rate": hits / total if total else 0.0,
                "mrr": sum(reciprocal_ranks) / total if total else 0.0,
            }
        )

    return metric_rows, example_rows


def build_product_lookup(products: pd.DataFrame) -> dict[str, str]:
    return dict(zip(products["product_id"], products["product_name"]))


def convert_product_ids_to_names(text: str, lookup: dict[str, str]) -> str:
    return " | ".join(lookup.get(pid, pid) for pid in text.split(" | "))


def write_markdown_report(
    metrics: list[dict[str, float]],
    frequent_rules: pd.DataFrame,
) -> None:
    lines = []
    lines.append("# Recommendation Engine Summary")
    lines.append("")
    lines.append("- Model: `Item co-occurrence recommendation engine`")
    lines.append("- Training source: `transaction_items_clean.csv` + `transactions_clean.csv`")
    lines.append("- Recommendation logic: products frequently purchased together are recommended together")
    lines.append("")
    lines.append("## Evaluation")
    lines.append("")
    lines.append("| Top-K | Evaluated Baskets | Hit Rate | MRR |")
    lines.append("|------:|------------------:|---------:|----:|")
    for row in metrics:
        lines.append(
            f"| {int(row['top_k'])} | {int(row['evaluated_baskets'])} | {row['hit_rate']:.4f} | {row['mrr']:.4f} |"
        )
    lines.append("")
    lines.append("## Strong Product Associations")
    lines.append("")
    for _, row in frequent_rules.head(10).iterrows():
        lines.append(
            f"- `{row['anchor_product_name']}` -> `{row['recommended_product_name']}` "
            f"(confidence={row['confidence']:.3f}, co_purchase_count={int(row['co_purchase_count'])})"
        )
    (MODEL_DIR / "recommendation_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    items, transactions, products = load_data()
    lookup = build_product_lookup(products)
    train_ids, val_ids, test_ids = split_transactions(transactions)

    train_baskets = build_baskets(items, train_ids)
    val_baskets = build_baskets(items, val_ids)
    test_baskets = build_baskets(items, test_ids)

    pair_counts, product_counts = train_item_cooccurrence(train_baskets)
    metrics, examples = evaluate_recommender(test_baskets, pair_counts, product_counts)

    rules = []
    for anchor, counter in pair_counts.items():
        base_count = max(product_counts[anchor], 1)
        for other, count in counter.items():
            rules.append(
                {
                    "anchor_product_id": anchor,
                    "recommended_product_id": other,
                    "co_purchase_count": count,
                    "anchor_support": base_count,
                    "confidence": count / base_count,
                }
            )

    rules_df = pd.DataFrame(rules).sort_values(
        ["confidence", "co_purchase_count"], ascending=[False, False]
    )
    rules_df["anchor_product_name"] = rules_df["anchor_product_id"].map(lookup)
    rules_df["recommended_product_name"] = rules_df["recommended_product_id"].map(lookup)

    example_df = pd.DataFrame(examples)
    if not example_df.empty:
        example_df["context_products"] = example_df["context_products"].map(
            lambda x: convert_product_ids_to_names(x, lookup)
        )
        example_df["actual_next_product"] = example_df["actual_next_product"].map(
            lambda x: lookup.get(x, x)
        )
        example_df["recommended_products"] = example_df["recommended_products"].map(
            lambda x: convert_product_ids_to_names(x, lookup)
        )

    metrics_df = pd.DataFrame(metrics)
    metrics_df.to_csv(MODEL_DIR / "evaluation_metrics.csv", index=False)
    rules_df.to_csv(MODEL_DIR / "association_rules.csv", index=False)
    example_df.to_csv(MODEL_DIR / "recommendation_examples.csv", index=False)

    metadata = {
        "model_type": "item_cooccurrence_recommender",
        "train_transaction_count": len(train_ids),
        "validation_transaction_count": len(val_ids),
        "test_transaction_count": len(test_ids),
        "train_basket_count": len(train_baskets),
        "validation_basket_count": len(val_baskets),
        "test_basket_count": len(test_baskets),
        "top_k_values": TOP_K_VALUES,
        "evaluation_metrics": metrics,
        "most_popular_products": popularity_rank(product_counts)[:20],
    }
    (MODEL_DIR / "model_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    write_markdown_report(metrics, rules_df)

    print(f"Recommendation engine outputs written to: {MODEL_DIR}")


if __name__ == "__main__":
    main()
