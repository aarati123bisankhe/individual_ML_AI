from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
FEATURE_DIR = BASE_DIR / "data" / "features"


def read_csv(name: str, parse_dates: list[str] | None = None) -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / name, parse_dates=parse_dates)


def mode_or_na(values: pd.Series) -> object:
    modes = values.dropna().mode()
    return modes.iloc[0] if not modes.empty else pd.NA


def add_time_columns(transactions: pd.DataFrame) -> pd.DataFrame:
    transactions = transactions.copy()
    transactions["transaction_date"] = transactions["entry_timestamp"].dt.date
    transactions["transaction_year"] = transactions["entry_timestamp"].dt.year
    transactions["transaction_month"] = transactions["entry_timestamp"].dt.month
    transactions["transaction_day"] = transactions["entry_timestamp"].dt.day
    transactions["transaction_dayofweek"] = transactions["entry_timestamp"].dt.dayofweek
    transactions["transaction_hour"] = transactions["entry_timestamp"].dt.hour
    transactions["is_weekend"] = transactions["transaction_dayofweek"].isin([5, 6])
    return transactions


def build_transaction_features(
    transactions: pd.DataFrame,
    items: pd.DataFrame,
    payments: pd.DataFrame,
    customers: pd.DataFrame,
    stores: pd.DataFrame,
) -> pd.DataFrame:
    transactions = add_time_columns(transactions)

    item_features = (
        items.groupby("transaction_id")
        .agg(
            item_rows=("line_item_id", "count"),
            basket_size=("product_id", "nunique"),
            total_units=("quantity", "sum"),
            item_revenue_npr=("line_total_npr", "sum"),
            avg_unit_price_npr=("unit_price_npr", "mean"),
            unique_zones=("zone_id", "nunique"),
            unique_aisles=("aisle_id", "nunique"),
            avg_scan_duration_ms=("scan_duration_ms", "mean"),
            max_scan_duration_ms=("scan_duration_ms", "max"),
            total_rescans=("rescans", "sum"),
            failed_scan_items=("scan_success", lambda s: int((~s.astype(bool)).sum())),
            app_scanned_items=(
                "scan_method",
                lambda s: int(s.isin(["barcode", "qr_code", "manual_entry"]).sum()),
            ),
            pos_scanned_items=("scan_method", lambda s: int((s == "checkout_pos").sum())),
        )
        .reset_index()
    )

    payment_features = (
        payments.groupby("transaction_id")
        .agg(
            avg_payment_latency_ms=("latency_ms", "mean"),
            max_payment_latency_ms=("latency_ms", "max"),
            retry_events=("status", lambda s: int((s == "retry").sum())),
            failed_payment_events=("status", lambda s: int((s == "failed").sum())),
        )
        .reset_index()
    )

    customer_columns = customers[
        ["customer_id", "loyalty_tier", "gender", "age_bucket", "home_area", "uses_app"]
    ].rename(columns={"loyalty_tier": "registered_loyalty_tier"})
    store_columns = stores[["store_id", "store_name", "city", "area"]].rename(
        columns={"area": "store_area"}
    )

    features = transactions.merge(item_features, on="transaction_id", how="left")
    features = features.merge(payment_features, on="transaction_id", how="left")
    features = features.merge(customer_columns, on="customer_id", how="left")
    features = features.merge(store_columns, on="store_id", how="left")

    features["discount_rate"] = (
        features["discount_npr"] / features["subtotal_npr"].replace(0, pd.NA)
    ).fillna(0)
    features["vat_rate_observed"] = (
        features["vat_13pct_npr"] / features["total_after_discount_npr"].replace(0, pd.NA)
    ).fillna(0)
    features["rescan_rate"] = (
        features["total_rescans"] / features["item_rows"].replace(0, pd.NA)
    ).fillna(0)
    features["scan_failure_rate"] = (
        features["failed_scan_items"] / features["item_rows"].replace(0, pd.NA)
    ).fillna(0)
    features["app_scan_share"] = (
        features["app_scanned_items"] / features["item_rows"].replace(0, pd.NA)
    ).fillna(0)
    features["payment_success_flag"] = features["payment_status"].eq("success")
    features["checkout_complexity_score"] = (
        features["basket_size"]
        + features["unique_aisles"]
        + features["payment_attempts"]
        + features["total_rescans"]
    )

    return features.sort_values("transaction_id").reset_index(drop=True)


def build_customer_features(
    customers: pd.DataFrame,
    transaction_features: pd.DataFrame,
    items: pd.DataFrame,
) -> pd.DataFrame:
    tx = transaction_features.copy()
    max_date = tx["entry_timestamp"].max()

    customer_tx = (
        tx.groupby("customer_id")
        .agg(
            transaction_count=("transaction_id", "nunique"),
            first_purchase_at=("entry_timestamp", "min"),
            last_purchase_at=("entry_timestamp", "max"),
            total_spend_npr=("grand_total_npr", "sum"),
            avg_order_value_npr=("grand_total_npr", "mean"),
            total_units=("total_units", "sum"),
            avg_basket_size=("basket_size", "mean"),
            avg_dwell_minutes=("dwell_minutes", "mean"),
            avg_aisles_visited=("aisles_visited", "mean"),
            scan_to_pay_rate=("scan_to_pay_used", "mean"),
            payment_success_rate=("payment_success_flag", "mean"),
            app_searches_total=("n_app_searches", "sum"),
            app_directions_total=("n_app_directions", "sum"),
            festival_transaction_count=("is_festival_period", "sum"),
            preferred_store_id=("store_id", mode_or_na),
            preferred_payment_method=("payment_method", mode_or_na),
            preferred_shopping_hour=("transaction_hour", mode_or_na),
        )
        .reset_index()
    )

    customer_items = (
        tx[["transaction_id", "customer_id"]]
        .merge(items[["transaction_id", "product_id", "subcategory", "zone_id"]], on="transaction_id")
        .groupby("customer_id")
        .agg(
            unique_products_bought=("product_id", "nunique"),
            favorite_subcategory=("subcategory", mode_or_na),
            favorite_zone_id=("zone_id", mode_or_na),
        )
        .reset_index()
    )

    features = customers.merge(customer_tx, on="customer_id", how="left")
    features = features.merge(customer_items, on="customer_id", how="left")
    features["has_purchase_history"] = features["transaction_count"].notna()

    fill_zero_cols = [
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
    ]
    features[fill_zero_cols] = features[fill_zero_cols].fillna(0)
    features["registered_on"] = pd.to_datetime(features["registered_on"])
    features["first_purchase_at"] = features["first_purchase_at"].fillna(features["registered_on"])
    features["last_purchase_at"] = features["last_purchase_at"].fillna(features["registered_on"])
    features["preferred_store_id"] = features["preferred_store_id"].fillna("No Purchase")
    features["preferred_payment_method"] = features["preferred_payment_method"].fillna("No Purchase")
    features["favorite_subcategory"] = features["favorite_subcategory"].fillna("No Purchase")
    features["favorite_zone_id"] = features["favorite_zone_id"].fillna("No Purchase")
    features["preferred_shopping_hour"] = features["preferred_shopping_hour"].fillna(-1).astype(int)
    features["customer_tenure_days"] = (max_date - features["registered_on"]).dt.days
    features["recency_days"] = (max_date - features["last_purchase_at"]).dt.days
    features["spend_per_visit_npr"] = (
        features["total_spend_npr"].div(features["transaction_count"].where(features["transaction_count"].ne(0)))
    ).fillna(0)
    features["app_engagement_events"] = (
        features["app_searches_total"] + features["app_directions_total"]
    )

    return features.sort_values("customer_id").reset_index(drop=True)


def build_product_features(
    products: pd.DataFrame,
    items: pd.DataFrame,
    transactions: pd.DataFrame,
    aisles: pd.DataFrame,
    zones: pd.DataFrame,
) -> pd.DataFrame:
    tx_context = transactions[
        ["transaction_id", "customer_id", "entry_timestamp", "is_festival_period", "scan_to_pay_used"]
    ]
    item_context = items.merge(tx_context, on="transaction_id", how="left")

    sales = (
        item_context.groupby("product_id")
        .agg(
            units_sold=("quantity", "sum"),
            sales_revenue_npr=("line_total_npr", "sum"),
            transaction_count=("transaction_id", "nunique"),
            unique_customers=("customer_id", "nunique"),
            avg_unit_price_sold_npr=("unit_price_npr", "mean"),
            avg_scan_duration_ms=("scan_duration_ms", "mean"),
            total_rescans=("rescans", "sum"),
            failed_scan_count=("scan_success", lambda s: int((~s.astype(bool)).sum())),
            festival_units_sold=(
                "quantity",
                lambda s: int(s[item_context.loc[s.index, "is_festival_period"].astype(bool)].sum()),
            ),
            scan_to_pay_units=(
                "quantity",
                lambda s: int(s[item_context.loc[s.index, "scan_to_pay_used"].astype(bool)].sum()),
            ),
            first_sold_at=("entry_timestamp", "min"),
            last_sold_at=("entry_timestamp", "max"),
        )
        .reset_index()
    )

    location = aisles.merge(zones, on="zone_id", how="left")[
        ["aisle_id", "x_coord", "y_coord", "zone_name", "ambient_temp_c", "is_perimeter"]
    ]
    features = products.merge(location, on="aisle_id", how="left", suffixes=("", "_aisle"))
    features = features.merge(sales, on="product_id", how="left")

    numeric_zero_cols = [
        "units_sold",
        "sales_revenue_npr",
        "transaction_count",
        "unique_customers",
        "total_rescans",
        "failed_scan_count",
        "festival_units_sold",
        "scan_to_pay_units",
    ]
    features[numeric_zero_cols] = features[numeric_zero_cols].fillna(0)
    features["avg_unit_price_sold_npr"] = features["avg_unit_price_sold_npr"].fillna(
        features["price_npr"]
    )
    features["avg_scan_duration_ms"] = features["avg_scan_duration_ms"].fillna(0)
    features["revenue_per_transaction_npr"] = (
        features["sales_revenue_npr"] / features["transaction_count"].replace(0, pd.NA)
    ).fillna(0)
    features["units_per_transaction"] = (
        features["units_sold"] / features["transaction_count"].replace(0, pd.NA)
    ).fillna(0)
    features["festival_unit_share"] = (
        features["festival_units_sold"] / features["units_sold"].replace(0, pd.NA)
    ).fillna(0)
    features["scan_to_pay_unit_share"] = (
        features["scan_to_pay_units"] / features["units_sold"].replace(0, pd.NA)
    ).fillna(0)
    features["scan_failure_rate"] = (
        features["failed_scan_count"] / features["transaction_count"].replace(0, pd.NA)
    ).fillna(0)
    features["rescan_per_transaction"] = (
        features["total_rescans"] / features["transaction_count"].replace(0, pd.NA)
    ).fillna(0)

    return features.sort_values("product_id").reset_index(drop=True)


def build_daily_store_product_features(
    products: pd.DataFrame,
    items: pd.DataFrame,
    transactions: pd.DataFrame,
) -> pd.DataFrame:
    tx_context = transactions[
        ["transaction_id", "store_id", "entry_timestamp", "is_festival_period"]
    ].copy()
    tx_context["sales_date"] = tx_context["entry_timestamp"].dt.date

    item_context = items.merge(tx_context, on="transaction_id", how="left")
    daily_sales = (
        item_context.groupby(["sales_date", "store_id", "product_id"])
        .agg(
            units_sold=("quantity", "sum"),
            revenue_npr=("line_total_npr", "sum"),
            transaction_count=("transaction_id", "nunique"),
            avg_unit_price_npr=("unit_price_npr", "mean"),
            is_festival_period=("is_festival_period", "max"),
        )
        .reset_index()
    )

    date_range = pd.date_range(
        transactions["entry_timestamp"].min().date(),
        transactions["entry_timestamp"].max().date(),
        freq="D",
    )
    product_store = products[["store_id", "product_id", "subcategory", "zone_id", "aisle_id", "price_npr"]]
    complete_index = (
        pd.MultiIndex.from_product(
            [date_range.date, product_store["product_id"]],
            names=["sales_date", "product_id"],
        )
        .to_frame(index=False)
        .merge(product_store, on="product_id", how="left")
    )

    features = complete_index.merge(
        daily_sales,
        on=["sales_date", "store_id", "product_id"],
        how="left",
    )
    features["units_sold"] = features["units_sold"].fillna(0).astype(int)
    features["revenue_npr"] = features["revenue_npr"].fillna(0)
    features["transaction_count"] = features["transaction_count"].fillna(0).astype(int)
    features["avg_unit_price_npr"] = features["avg_unit_price_npr"].fillna(features["price_npr"])
    features["is_festival_period"] = (
        features["is_festival_period"]
        .where(features["is_festival_period"].notna(), False)
        .astype(bool)
    )
    features["sales_date"] = pd.to_datetime(features["sales_date"])
    features["day_of_week"] = features["sales_date"].dt.dayofweek
    features["month"] = features["sales_date"].dt.month
    features["is_weekend"] = features["day_of_week"].isin([5, 6])

    features = features.sort_values(["store_id", "product_id", "sales_date"]).reset_index(drop=True)
    group_cols = ["store_id", "product_id"]
    features["units_lag_1d"] = features.groupby(group_cols)["units_sold"].shift(1).fillna(0)
    features["units_rolling_7d"] = (
        features.groupby(group_cols)["units_sold"]
        .transform(lambda s: s.shift(1).rolling(7, min_periods=1).mean())
        .fillna(0)
    )
    features["units_rolling_14d"] = (
        features.groupby(group_cols)["units_sold"]
        .transform(lambda s: s.shift(1).rolling(14, min_periods=1).mean())
        .fillna(0)
    )
    features["target_next_day_units"] = (
        features.groupby(group_cols)["units_sold"].shift(-1).fillna(0).astype(int)
    )

    return features


def build_navigation_features(
    app_events: pd.DataFrame,
    transactions: pd.DataFrame,
    aisles: pd.DataFrame,
    zones: pd.DataFrame,
    stores: pd.DataFrame,
) -> pd.DataFrame:
    aisle_location = aisles.merge(zones, on="zone_id", how="left")
    aisle_location = aisle_location.rename(
        columns={
            "aisle_id": "target_aisle_id",
            "x_coord": "target_x_coord",
            "y_coord": "target_y_coord",
        }
    )

    tx_context = transactions[
        ["transaction_id", "entry_timestamp", "exit_timestamp", "dwell_minutes", "is_festival_period"]
    ]
    store_context = stores[["store_id", "store_name", "city", "area"]].rename(
        columns={"area": "store_area"}
    )
    features = app_events.merge(tx_context, on="transaction_id", how="left")
    features = features.merge(store_context, on="store_id", how="left")
    features = features.merge(aisle_location, on=["target_aisle_id", "store_id"], how="left")
    features["event_hour"] = features["event_timestamp"].dt.hour
    features["event_dayofweek"] = features["event_timestamp"].dt.dayofweek
    features["minutes_after_entry"] = (
        features["event_timestamp"] - features["entry_timestamp"]
    ).dt.total_seconds() / 60
    features["has_search_query"] = features["search_query"].notna()
    features["has_target_aisle"] = features["target_aisle_id"].notna()
    features["search_query"] = features["search_query"].fillna("No Search Query")
    features["target_aisle_id"] = features["target_aisle_id"].fillna("No Target Aisle")
    features["zone_id"] = features["zone_id"].fillna("No Target Zone")
    features["zone_name"] = features["zone_name"].fillna("No Target Zone")
    features["aisle_number_in_zone"] = features["aisle_number_in_zone"].fillna(-1).astype(int)
    features["target_x_coord"] = features["target_x_coord"].fillna(-1)
    features["target_y_coord"] = features["target_y_coord"].fillna(-1)
    features["ambient_temp_c"] = features["ambient_temp_c"].fillna(-1)
    features["is_perimeter"] = (
        features["is_perimeter"].where(features["is_perimeter"].notna(), False).astype(bool)
    )

    return features.sort_values("event_id").reset_index(drop=True)


def write_feature_report(feature_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, df in feature_frames.items():
        rows.append(
            {
                "feature_table": name,
                "rows": len(df),
                "columns": len(df.columns),
                "duplicate_rows": int(df.duplicated().sum()),
                "total_missing_values": int(df.isna().sum().sum()),
                "missing_columns": ", ".join(df.columns[df.isna().any()].tolist()),
            }
        )
    report = pd.DataFrame(rows)
    report.to_csv(FEATURE_DIR / "feature_engineering_report.csv", index=False)
    return report


def main() -> None:
    FEATURE_DIR.mkdir(parents=True, exist_ok=True)

    stores = read_csv("stores_clean.csv")
    zones = read_csv("zones_clean.csv")
    aisles = read_csv("aisles_clean.csv")
    products = read_csv("products_clean.csv")
    customers = read_csv("customers_clean.csv", ["registered_on"])
    transactions = read_csv("transactions_clean.csv", ["entry_timestamp", "exit_timestamp"])
    items = read_csv("transaction_items_clean.csv", ["scan_timestamp"])
    app_events = read_csv("app_events_clean.csv", ["event_timestamp"])
    payments = read_csv("payment_events_clean.csv", ["attempt_timestamp"])

    items = items.merge(
        products[["product_id", "subcategory"]],
        on="product_id",
        how="left",
    )

    transaction_features = build_transaction_features(
        transactions, items, payments, customers, stores
    )
    customer_features = build_customer_features(customers, transaction_features, items)
    product_features = build_product_features(products, items, transactions, aisles, zones)
    daily_features = build_daily_store_product_features(products, items, transactions)
    navigation_features = build_navigation_features(
        app_events, transactions, aisles, zones, stores
    )

    feature_frames = {
        "transaction_features.csv": transaction_features,
        "customer_features.csv": customer_features,
        "product_features.csv": product_features,
        "daily_store_product_features.csv": daily_features,
        "navigation_features.csv": navigation_features,
    }

    for file_name, frame in feature_frames.items():
        frame.to_csv(FEATURE_DIR / file_name, index=False)

    write_feature_report(feature_frames)
    print(f"Feature tables written to: {FEATURE_DIR}")


if __name__ == "__main__":
    main()
