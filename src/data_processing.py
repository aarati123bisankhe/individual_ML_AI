from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


DATA_FILES = [
    "stores.csv",
    "zones.csv",
    "aisles.csv",
    "products.csv",
    "customers.csv",
    "transactions.csv",
    "transaction_items.csv",
    "app_events.csv",
    "payment_events.csv",
    "train_transaction_ids.csv",
    "val_transaction_ids.csv",
    "test_transaction_ids.csv",
]


TIMESTAMP_COLUMNS = {
    "customers.csv": ["registered_on"],
    "transactions.csv": ["entry_timestamp", "exit_timestamp"],
    "transaction_items.csv": ["scan_timestamp"],
    "app_events.csv": ["event_timestamp"],
    "payment_events.csv": ["attempt_timestamp"],
}


BOOLEAN_COLUMNS = {
    "zones.csv": ["is_perimeter"],
    "customers.csv": ["uses_app"],
    "transactions.csv": ["scan_to_pay_used", "is_festival_period"],
    "transaction_items.csv": ["scan_success"],
}


PRIMARY_KEYS = {
    "stores.csv": ["store_id"],
    "zones.csv": ["zone_id"],
    "aisles.csv": ["aisle_id"],
    "products.csv": ["product_id"],
    "customers.csv": ["customer_id"],
    "transactions.csv": ["transaction_id"],
    "transaction_items.csv": ["line_item_id"],
    "app_events.csv": ["event_id"],
    "payment_events.csv": ["payment_event_id"],
}


def resolve_product_shelf_collisions(products: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    products = products.copy()
    duplicate_mask = products.duplicated(
        subset=["store_id", "aisle_id", "shelf_number", "shelf_position"],
        keep=False,
    )
    affected_rows = int(duplicate_mask.sum())

    if affected_rows:
        products = products.sort_values(
            ["store_id", "aisle_id", "shelf_number", "shelf_position", "product_id"]
        ).reset_index(drop=True)
        products["shelf_position"] = (
            products.groupby(["store_id", "aisle_id", "shelf_number"]).cumcount() + 1
        )

    return products, affected_rows


def reconcile_payment_amounts(
    payment_events: pd.DataFrame, transactions: pd.DataFrame
) -> tuple[pd.DataFrame, int]:
    payment_events = payment_events.copy()
    payment_events = payment_events.merge(
        transactions[["transaction_id", "grand_total_npr"]],
        on="transaction_id",
        how="left",
    )

    mismatch_mask = payment_events["amount_npr"] != payment_events["grand_total_npr"]
    corrections = int(mismatch_mask.sum())
    payment_events.loc[mismatch_mask, "amount_npr"] = payment_events.loc[
        mismatch_mask, "grand_total_npr"
    ]

    payment_events = payment_events.drop(columns=["grand_total_npr"])
    return payment_events, corrections


def rebuild_transaction_summary(
    transactions: pd.DataFrame,
    transaction_items: pd.DataFrame,
    app_events: pd.DataFrame,
    payment_events: pd.DataFrame,
    customers: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    transactions = transactions.copy()

    item_summary = (
        transaction_items.groupby("transaction_id")
        .agg(
            num_distinct_items=("product_id", "nunique"),
            num_total_units=("quantity", "sum"),
            aisles_visited=("aisle_id", "nunique"),
            subtotal_npr=("line_total_npr", "sum"),
            last_scan_timestamp=("scan_timestamp", "max"),
        )
        .reset_index()
    )

    app_summary = (
        app_events.groupby("transaction_id")
        .agg(
            n_app_searches=("event_type", lambda s: int((s == "search_query").sum())),
            n_app_directions=(
                "event_type",
                lambda s: int((s == "directions_request").sum()),
            ),
        )
        .reset_index()
    )

    payment_events = payment_events.sort_values(["transaction_id", "attempt_number"])
    payment_summary = (
        payment_events.groupby("transaction_id")
        .agg(
            payment_attempts=("attempt_number", "max"),
            payment_method=("payment_method", "last"),
            payment_status=("status", "last"),
            last_payment_timestamp=("attempt_timestamp", "max"),
        )
        .reset_index()
    )

    loyalty_summary = customers[["customer_id", "loyalty_tier"]].rename(
        columns={"loyalty_tier": "customer_loyalty_tier"}
    )

    before = transactions.copy()
    transactions = transactions.merge(item_summary, on="transaction_id", how="left", suffixes=("", "_new"))
    transactions = transactions.merge(app_summary, on="transaction_id", how="left", suffixes=("", "_new"))
    transactions = transactions.merge(payment_summary, on="transaction_id", how="left", suffixes=("", "_new"))
    transactions = transactions.merge(loyalty_summary, on="customer_id", how="left", suffixes=("", "_new"))

    transactions["num_distinct_items"] = transactions["num_distinct_items_new"].fillna(
        transactions["num_distinct_items"]
    )
    transactions["num_total_units"] = transactions["num_total_units_new"].fillna(
        transactions["num_total_units"]
    )
    transactions["aisles_visited"] = transactions["aisles_visited_new"].fillna(
        transactions["aisles_visited"]
    )
    transactions["subtotal_npr"] = transactions["subtotal_npr_new"].fillna(
        transactions["subtotal_npr"]
    )
    transactions["n_app_searches"] = (
        transactions["n_app_searches_new"].fillna(0).astype(int)
    )
    transactions["n_app_directions"] = (
        transactions["n_app_directions_new"].fillna(0).astype(int)
    )
    transactions["payment_attempts"] = transactions["payment_attempts_new"].fillna(
        transactions["payment_attempts"]
    )
    transactions["payment_method"] = transactions["payment_method_new"].fillna(
        transactions["payment_method"]
    )
    transactions["payment_status"] = transactions["payment_status_new"].fillna(
        transactions["payment_status"]
    )
    transactions["customer_loyalty_tier"] = transactions[
        "customer_loyalty_tier_new"
    ].fillna(transactions["customer_loyalty_tier"])

    recomputed_dwell = (
        transactions["exit_timestamp"] - transactions["entry_timestamp"]
    ).dt.total_seconds() / 60
    transactions["dwell_minutes"] = recomputed_dwell.round(2)

    corrections = {
        "transaction_num_distinct_items_updates": int(
            (before["num_distinct_items"] != transactions["num_distinct_items"]).sum()
        ),
        "transaction_num_total_units_updates": int(
            (before["num_total_units"] != transactions["num_total_units"]).sum()
        ),
        "transaction_aisles_visited_updates": int(
            (before["aisles_visited"] != transactions["aisles_visited"]).sum()
        ),
        "transaction_subtotal_updates": int(
            (before["subtotal_npr"] != transactions["subtotal_npr"]).sum()
        ),
        "transaction_app_search_count_updates": int(
            (before["n_app_searches"] != transactions["n_app_searches"]).sum()
        ),
        "transaction_app_direction_count_updates": int(
            (before["n_app_directions"] != transactions["n_app_directions"]).sum()
        ),
        "transaction_payment_attempt_updates": int(
            (before["payment_attempts"] != transactions["payment_attempts"]).sum()
        ),
        "transaction_payment_method_updates": int(
            (before["payment_method"] != transactions["payment_method"]).sum()
        ),
        "transaction_payment_status_updates": int(
            (before["payment_status"] != transactions["payment_status"]).sum()
        ),
        "transaction_loyalty_updates": int(
            (before["customer_loyalty_tier"] != transactions["customer_loyalty_tier"]).sum()
        ),
    }

    transactions = transactions.drop(
        columns=[
            "num_distinct_items_new",
            "num_total_units_new",
            "aisles_visited_new",
            "subtotal_npr_new",
            "last_scan_timestamp",
            "n_app_searches_new",
            "n_app_directions_new",
            "payment_attempts_new",
            "payment_method_new",
            "payment_status_new",
            "last_payment_timestamp",
            "customer_loyalty_tier_new",
        ],
        errors="ignore",
    )

    return transactions, corrections


def foreign_key_summary(cleaned_frames: dict[str, pd.DataFrame]) -> dict[str, int]:
    return {
        "aisles.store_id": int(
            (~cleaned_frames["aisles.csv"]["store_id"].isin(cleaned_frames["stores.csv"]["store_id"])).sum()
        ),
        "aisles.zone_id": int(
            (~cleaned_frames["aisles.csv"]["zone_id"].isin(cleaned_frames["zones.csv"]["zone_id"])).sum()
        ),
        "products.store_id": int(
            (~cleaned_frames["products.csv"]["store_id"].isin(cleaned_frames["stores.csv"]["store_id"])).sum()
        ),
        "products.zone_id": int(
            (~cleaned_frames["products.csv"]["zone_id"].isin(cleaned_frames["zones.csv"]["zone_id"])).sum()
        ),
        "products.aisle_id": int(
            (~cleaned_frames["products.csv"]["aisle_id"].isin(cleaned_frames["aisles.csv"]["aisle_id"])).sum()
        ),
        "transactions.customer_id": int(
            (~cleaned_frames["transactions.csv"]["customer_id"].isin(cleaned_frames["customers.csv"]["customer_id"])).sum()
        ),
        "transactions.store_id": int(
            (~cleaned_frames["transactions.csv"]["store_id"].isin(cleaned_frames["stores.csv"]["store_id"])).sum()
        ),
        "transaction_items.transaction_id": int(
            (~cleaned_frames["transaction_items.csv"]["transaction_id"].isin(cleaned_frames["transactions.csv"]["transaction_id"])).sum()
        ),
        "transaction_items.product_id": int(
            (~cleaned_frames["transaction_items.csv"]["product_id"].isin(cleaned_frames["products.csv"]["product_id"])).sum()
        ),
        "app_events.transaction_id": int(
            (~cleaned_frames["app_events.csv"]["transaction_id"].isin(cleaned_frames["transactions.csv"]["transaction_id"])).sum()
        ),
        "payment_events.transaction_id": int(
            (~cleaned_frames["payment_events.csv"]["transaction_id"].isin(cleaned_frames["transactions.csv"]["transaction_id"])).sum()
        ),
    }


def normalize_text(value: object) -> object:
    if pd.isna(value):
        return pd.NA
    if isinstance(value, str):
        value = " ".join(value.strip().split())
        return value if value else pd.NA
    return value


def clean_dataframe(file_name: str) -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / file_name)
    df.columns = [col.strip() for col in df.columns]

    object_columns = df.select_dtypes(include=["object"]).columns
    for col in object_columns:
        df[col] = df[col].map(normalize_text)

    for col in TIMESTAMP_COLUMNS.get(file_name, []):
        df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in BOOLEAN_COLUMNS.get(file_name, []):
        df[col] = df[col].astype("boolean")

    if file_name == "app_events.csv":
        search_mask = df["event_type"].eq("search_query")
        direction_mask = df["event_type"].eq("directions_request")
        df.loc[search_mask, "target_aisle_id"] = pd.NA
        df.loc[direction_mask, "search_query"] = pd.NA

    primary_key = PRIMARY_KEYS.get(file_name)
    if primary_key:
        df = df.drop_duplicates(subset=primary_key, keep="first")
        df = df.sort_values(primary_key).reset_index(drop=True)
    else:
        df = df.drop_duplicates().reset_index(drop=True)

    return df


def export_dataframe(df: pd.DataFrame, output_name: str, source_name: str) -> None:
    export_df = df.copy()

    for col in TIMESTAMP_COLUMNS.get(source_name, []):
        export_df[col] = export_df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

    for col in BOOLEAN_COLUMNS.get(source_name, []):
        export_df[col] = export_df[col].astype("string")

    export_df.to_csv(PROCESSED_DIR / output_name, index=False)


def build_cleaning_report(
    cleaned_frames: dict[str, pd.DataFrame], correction_summary: dict[str, int]
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for file_name, df in cleaned_frames.items():
        missing_counts = df.isna().sum()
        primary_key = PRIMARY_KEYS.get(file_name)

        row = {
            "dataset": file_name,
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "duplicate_rows": int(df.duplicated().sum()),
            "missing_columns_count": int((missing_counts > 0).sum()),
            "total_missing_values": int(missing_counts.sum()),
            "duplicate_primary_keys": int(df.duplicated(subset=primary_key).sum()) if primary_key else 0,
        }

        if file_name in TIMESTAMP_COLUMNS:
            for col in TIMESTAMP_COLUMNS[file_name]:
                if col in df.columns and df[col].notna().any():
                    row[f"{col}_min"] = df[col].min().strftime("%Y-%m-%d %H:%M:%S")
                    row[f"{col}_max"] = df[col].max().strftime("%Y-%m-%d %H:%M:%S")

        if file_name == "app_events.csv":
            row["note"] = (
                "Missing values are expected: search_query is blank for directions_request "
                "and target_aisle_id is blank for search_query."
            )
        else:
            row["note"] = "No major cleaning issue detected."

        rows.append(row)

    report_df = pd.DataFrame(rows)
    report_df["foreign_key_violations_total"] = sum(foreign_key_summary(cleaned_frames).values())
    report_df["pipeline_corrections_applied"] = 0

    correction_map = {
        "products.csv": correction_summary.get("product_shelf_position_fixes", 0),
        "transactions.csv": sum(
            value
            for key, value in correction_summary.items()
            if key.startswith("transaction_")
        ),
        "payment_events.csv": correction_summary.get("payment_amount_reconciliations", 0),
    }
    report_df["pipeline_corrections_applied"] = report_df["dataset"].map(correction_map).fillna(0).astype(int)
    return report_df


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    cleaned_frames: dict[str, pd.DataFrame] = {}
    for file_name in DATA_FILES:
        cleaned = clean_dataframe(file_name)
        cleaned_frames[file_name] = cleaned

    correction_summary: dict[str, int] = {}
    cleaned_frames["products.csv"], correction_summary["product_shelf_position_fixes"] = (
        resolve_product_shelf_collisions(cleaned_frames["products.csv"])
    )
    cleaned_frames["payment_events.csv"], correction_summary["payment_amount_reconciliations"] = (
        reconcile_payment_amounts(
            cleaned_frames["payment_events.csv"], cleaned_frames["transactions.csv"]
        )
    )
    cleaned_frames["transactions.csv"], transaction_corrections = rebuild_transaction_summary(
        cleaned_frames["transactions.csv"],
        cleaned_frames["transaction_items.csv"],
        cleaned_frames["app_events.csv"],
        cleaned_frames["payment_events.csv"],
        cleaned_frames["customers.csv"],
    )
    correction_summary.update(transaction_corrections)

    for file_name, cleaned in cleaned_frames.items():
        stem = Path(file_name).stem
        export_dataframe(cleaned, f"{stem}_clean.csv", file_name)

    report_df = build_cleaning_report(cleaned_frames, correction_summary)
    report_df.to_csv(PROCESSED_DIR / "cleaning_report.csv", index=False)

    print("Data cleaning completed.")
    print(f"Processed files saved in: {PROCESSED_DIR}")
    print(f"Cleaning report saved as: {PROCESSED_DIR / 'cleaning_report.csv'}")


if __name__ == "__main__":
    main()
