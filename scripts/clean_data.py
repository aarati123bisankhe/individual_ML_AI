from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
CLEAN_DIR = ROOT / "data" / "cleaned"
REPORT_PATH = CLEAN_DIR / "quality_report.json"


FILE_ORDER = [
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


def clean_text(value: object) -> object:
    if pd.isna(value):
        return pd.NA
    if isinstance(value, str):
        value = " ".join(value.strip().split())
        return value if value else pd.NA
    return value


def normalize_object_columns(df: pd.DataFrame) -> pd.DataFrame:
    obj_cols = df.select_dtypes(include=["object"]).columns
    for col in obj_cols:
        df[col] = df[col].map(clean_text)
    return df


def normalize_booleans(df: pd.DataFrame, file_name: str) -> pd.DataFrame:
    for col in BOOLEAN_COLUMNS.get(file_name, []):
        if col in df.columns:
            df[col] = df[col].astype("boolean")
    return df


def normalize_timestamps(df: pd.DataFrame, file_name: str) -> pd.DataFrame:
    for col in TIMESTAMP_COLUMNS.get(file_name, []):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def enforce_app_event_rules(df: pd.DataFrame) -> pd.DataFrame:
    search_mask = df["event_type"].eq("search_query")
    directions_mask = df["event_type"].eq("directions_request")

    df.loc[search_mask, "target_aisle_id"] = pd.NA
    df.loc[directions_mask, "search_query"] = pd.NA
    return df


def sort_for_stability(df: pd.DataFrame, file_name: str) -> pd.DataFrame:
    key_cols = PRIMARY_KEYS.get(file_name)
    if key_cols:
        return df.sort_values(key_cols).reset_index(drop=True)
    return df.reset_index(drop=True)


def dataframe_summary(df: pd.DataFrame, file_name: str) -> dict:
    summary = {
        "rows": int(len(df)),
        "columns": list(df.columns),
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_values": {
            col: int(count)
            for col, count in df.isna().sum().items()
            if int(count) > 0
        },
    }

    key_cols = PRIMARY_KEYS.get(file_name)
    if key_cols:
        summary["duplicate_primary_keys"] = int(df.duplicated(subset=key_cols).sum())

    if file_name in TIMESTAMP_COLUMNS:
        timestamp_ranges = {}
        for col in TIMESTAMP_COLUMNS[file_name]:
            if col in df.columns and df[col].notna().any():
                timestamp_ranges[col] = {
                    "min": df[col].min().isoformat(sep=" "),
                    "max": df[col].max().isoformat(sep=" "),
                }
        if timestamp_ranges:
            summary["timestamp_ranges"] = timestamp_ranges

    return summary


def validate_foreign_keys(cleaned: dict[str, pd.DataFrame]) -> dict:
    checks = {
        "aisles.store_id": (~cleaned["aisles.csv"]["store_id"].isin(cleaned["stores.csv"]["store_id"])).sum(),
        "aisles.zone_id": (~cleaned["aisles.csv"]["zone_id"].isin(cleaned["zones.csv"]["zone_id"])).sum(),
        "products.store_id": (~cleaned["products.csv"]["store_id"].isin(cleaned["stores.csv"]["store_id"])).sum(),
        "products.zone_id": (~cleaned["products.csv"]["zone_id"].isin(cleaned["zones.csv"]["zone_id"])).sum(),
        "products.aisle_id": (~cleaned["products.csv"]["aisle_id"].isin(cleaned["aisles.csv"]["aisle_id"])).sum(),
        "transactions.customer_id": (~cleaned["transactions.csv"]["customer_id"].isin(cleaned["customers.csv"]["customer_id"])).sum(),
        "transactions.store_id": (~cleaned["transactions.csv"]["store_id"].isin(cleaned["stores.csv"]["store_id"])).sum(),
        "transaction_items.transaction_id": (~cleaned["transaction_items.csv"]["transaction_id"].isin(cleaned["transactions.csv"]["transaction_id"])).sum(),
        "transaction_items.product_id": (~cleaned["transaction_items.csv"]["product_id"].isin(cleaned["products.csv"]["product_id"])).sum(),
        "transaction_items.aisle_id": (~cleaned["transaction_items.csv"]["aisle_id"].isin(cleaned["aisles.csv"]["aisle_id"])).sum(),
        "app_events.transaction_id": (~cleaned["app_events.csv"]["transaction_id"].isin(cleaned["transactions.csv"]["transaction_id"])).sum(),
        "app_events.customer_id": (~cleaned["app_events.csv"]["customer_id"].isin(cleaned["customers.csv"]["customer_id"])).sum(),
        "app_events.store_id": (~cleaned["app_events.csv"]["store_id"].isin(cleaned["stores.csv"]["store_id"])).sum(),
        "app_events.target_aisle_id_non_null": (
            ~cleaned["app_events.csv"]["target_aisle_id"].dropna().isin(cleaned["aisles.csv"]["aisle_id"])
        ).sum(),
        "payment_events.transaction_id": (~cleaned["payment_events.csv"]["transaction_id"].isin(cleaned["transactions.csv"]["transaction_id"])).sum(),
    }
    return {key: int(value) for key, value in checks.items()}


def load_and_clean_csv(file_name: str) -> pd.DataFrame:
    df = pd.read_csv(RAW_DIR / file_name)
    df.columns = [col.strip() for col in df.columns]
    df = normalize_object_columns(df)
    df = normalize_booleans(df, file_name)
    df = normalize_timestamps(df, file_name)

    if file_name == "app_events.csv":
        df = enforce_app_event_rules(df)

    return sort_for_stability(df, file_name)


def save_clean_csv(df: pd.DataFrame, file_name: str) -> None:
    output_path = CLEAN_DIR / file_name
    export_df = df.copy()

    for col in TIMESTAMP_COLUMNS.get(file_name, []):
        if col in export_df.columns:
            export_df[col] = export_df[col].dt.strftime("%Y-%m-%d %H:%M:%S")

    for col in BOOLEAN_COLUMNS.get(file_name, []):
        if col in export_df.columns:
            export_df[col] = export_df[col].astype("string")

    export_df.to_csv(output_path, index=False)


def main() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    cleaned_frames: dict[str, pd.DataFrame] = {}
    file_summaries: dict[str, dict] = {}

    for file_name in FILE_ORDER:
        df = load_and_clean_csv(file_name)
        cleaned_frames[file_name] = df
        file_summaries[file_name] = dataframe_summary(df, file_name)
        save_clean_csv(df, file_name)

    report = {
        "raw_directory": str(RAW_DIR),
        "clean_directory": str(CLEAN_DIR),
        "files": file_summaries,
        "foreign_key_violations": validate_foreign_keys(cleaned_frames),
        "notes": [
            "Raw files are preserved unchanged in data/raw.",
            "Whitespace was normalized across string columns.",
            "Timestamp columns were parsed and exported in YYYY-MM-DD HH:MM:SS format.",
            "Boolean columns were normalized consistently.",
            "app_events keeps semantically valid missing values: search_query is blank for directions_request rows, and target_aisle_id is blank for search_query rows.",
        ],
    }

    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Cleaned files written to: {CLEAN_DIR}")
    print(f"Quality report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
