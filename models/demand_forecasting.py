from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
FEATURE_DIR = BASE_DIR / "data" / "features"
MODEL_DIR = BASE_DIR / "models" / "demand_forecasting"


FEATURE_COLUMNS = [
    "price_npr",
    "units_sold",
    "transaction_count",
    "avg_unit_price_npr",
    "is_festival_period",
    "day_of_week",
    "month",
    "is_weekend",
    "units_lag_1d",
    "units_rolling_7d",
    "units_rolling_14d",
]

TARGET_COLUMN = "target_next_day_units"
TRAIN_END = "2025-07-30"
VAL_END = "2025-11-30"


def load_dataset() -> pd.DataFrame:
    df = pd.read_csv(FEATURE_DIR / "daily_store_product_features.csv", parse_dates=["sales_date"])
    df["is_festival_period"] = df["is_festival_period"].astype(bool)
    df["is_weekend"] = df["is_weekend"].astype(bool)
    return df


def add_cyclical_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["day_of_week_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["day_of_week_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    return df


def split_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = df[df["sales_date"] <= pd.Timestamp(TRAIN_END)].copy()
    val = df[(df["sales_date"] > pd.Timestamp(TRAIN_END)) & (df["sales_date"] <= pd.Timestamp(VAL_END))].copy()
    test = df[df["sales_date"] > pd.Timestamp(VAL_END)].copy()
    return train, val, test


def prepare_matrix(df: pd.DataFrame, feature_columns: list[str]) -> np.ndarray:
    x = df[feature_columns].copy()
    bool_cols = x.select_dtypes(include=["bool"]).columns
    for col in bool_cols:
        x[col] = x[col].astype(int)
    return x.to_numpy(dtype=float)


def standardize_matrix(x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    means = x.mean(axis=0)
    stds = x.std(axis=0)
    stds[stds == 0] = 1.0
    return (x - means) / stds, means, stds


def apply_standardization(x: np.ndarray, means: np.ndarray, stds: np.ndarray) -> np.ndarray:
    return (x - means) / stds


def fit_ridge_regression(x: np.ndarray, y: np.ndarray, alpha: float) -> np.ndarray:
    x_bias = np.hstack([np.ones((len(x), 1)), x])
    identity = np.eye(x_bias.shape[1])
    identity[0, 0] = 0
    beta = np.linalg.solve(x_bias.T @ x_bias + alpha * identity, x_bias.T @ y)
    return beta


def predict_ridge(x: np.ndarray, beta: np.ndarray) -> np.ndarray:
    x_bias = np.hstack([np.ones((len(x), 1)), x])
    preds = x_bias @ beta
    return np.clip(preds, 0, None)


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def wape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = np.sum(np.abs(y_true))
    if denom == 0:
        return 0.0
    return float(np.sum(np.abs(y_true - y_pred)) / denom)


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "mae": mae(y_true, y_pred),
        "rmse": rmse(y_true, y_pred),
        "wape": wape(y_true, y_pred),
    }


def choose_best_alpha(
    train_x: np.ndarray,
    train_y: np.ndarray,
    val_x: np.ndarray,
    val_y: np.ndarray,
    alphas: list[float],
) -> tuple[float, list[dict[str, float]]]:
    evaluations = []
    best_alpha = alphas[0]
    best_rmse = float("inf")

    for alpha in alphas:
        beta = fit_ridge_regression(train_x, train_y, alpha)
        preds = predict_ridge(val_x, beta)
        metrics = evaluate_predictions(val_y, preds)
        evaluation = {"alpha": alpha, **metrics}
        evaluations.append(evaluation)
        if metrics["rmse"] < best_rmse:
            best_rmse = metrics["rmse"]
            best_alpha = alpha

    return best_alpha, evaluations


def build_naive_baseline(df: pd.DataFrame) -> np.ndarray:
    baseline = 0.6 * df["units_lag_1d"].to_numpy(dtype=float) + 0.4 * df["units_rolling_7d"].to_numpy(dtype=float)
    return np.clip(baseline, 0, None)


def write_markdown_report(
    best_alpha: float,
    alpha_results: list[dict[str, float]],
    val_baseline: dict[str, float],
    val_model: dict[str, float],
    test_baseline: dict[str, float],
    test_model: dict[str, float],
    train_rows: int,
    val_rows: int,
    test_rows: int,
) -> None:
    lines = []
    lines.append("# Demand Forecasting Model Summary")
    lines.append("")
    lines.append("- Model: `Ridge regression implemented with numpy`")
    lines.append("- Input table: `data/features/daily_store_product_features.csv`")
    lines.append("- Prediction target: `target_next_day_units`")
    lines.append(f"- Train rows: `{train_rows}`")
    lines.append(f"- Validation rows: `{val_rows}`")
    lines.append(f"- Test rows: `{test_rows}`")
    lines.append(f"- Selected alpha: `{best_alpha}`")
    lines.append("")
    lines.append("## Alpha Tuning on Validation Set")
    lines.append("")
    lines.append("| Alpha | MAE | RMSE | WAPE |")
    lines.append("|------:|----:|-----:|-----:|")
    for row in alpha_results:
        lines.append(f"| {row['alpha']:.4f} | {row['mae']:.4f} | {row['rmse']:.4f} | {row['wape']:.4f} |")
    lines.append("")
    lines.append("## Validation Performance")
    lines.append("")
    lines.append(f"- Naive baseline MAE: {val_baseline['mae']:.4f}")
    lines.append(f"- Naive baseline RMSE: {val_baseline['rmse']:.4f}")
    lines.append(f"- Naive baseline WAPE: {val_baseline['wape']:.4f}")
    lines.append(f"- Ridge model MAE: {val_model['mae']:.4f}")
    lines.append(f"- Ridge model RMSE: {val_model['rmse']:.4f}")
    lines.append(f"- Ridge model WAPE: {val_model['wape']:.4f}")
    lines.append("")
    lines.append("## Test Performance")
    lines.append("")
    lines.append(f"- Naive baseline MAE: {test_baseline['mae']:.4f}")
    lines.append(f"- Naive baseline RMSE: {test_baseline['rmse']:.4f}")
    lines.append(f"- Naive baseline WAPE: {test_baseline['wape']:.4f}")
    lines.append(f"- Ridge model MAE: {test_model['mae']:.4f}")
    lines.append(f"- Ridge model RMSE: {test_model['rmse']:.4f}")
    lines.append(f"- Ridge model WAPE: {test_model['wape']:.4f}")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("- The baseline uses recent demand only: yesterday's units and the 7-day rolling average.")
    lines.append("- The ridge model adds calendar, price, transaction, and festival features on top of lag features.")
    lines.append("- This makes the forecasting pipeline explainable and easy to present in a thesis.")
    (MODEL_DIR / "demand_forecasting_report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    df = add_cyclical_features(load_dataset())
    feature_columns = FEATURE_COLUMNS + ["day_of_week_sin", "day_of_week_cos", "month_sin", "month_cos"]
    train_df, val_df, test_df = split_dataset(df)

    train_x_raw = prepare_matrix(train_df, feature_columns)
    val_x_raw = prepare_matrix(val_df, feature_columns)
    test_x_raw = prepare_matrix(test_df, feature_columns)

    train_y = train_df[TARGET_COLUMN].to_numpy(dtype=float)
    val_y = val_df[TARGET_COLUMN].to_numpy(dtype=float)
    test_y = test_df[TARGET_COLUMN].to_numpy(dtype=float)

    train_x, means, stds = standardize_matrix(train_x_raw)
    val_x = apply_standardization(val_x_raw, means, stds)
    test_x = apply_standardization(test_x_raw, means, stds)

    best_alpha, alpha_results = choose_best_alpha(
        train_x, train_y, val_x, val_y, [0.1, 1.0, 5.0, 10.0, 25.0, 50.0]
    )

    full_train_x = np.vstack([train_x, val_x])
    full_train_y = np.concatenate([train_y, val_y])
    beta = fit_ridge_regression(full_train_x, full_train_y, best_alpha)

    val_baseline_preds = build_naive_baseline(val_df)
    test_baseline_preds = build_naive_baseline(test_df)
    val_model_preds = predict_ridge(val_x, fit_ridge_regression(train_x, train_y, best_alpha))
    test_model_preds = predict_ridge(test_x, beta)

    val_baseline_metrics = evaluate_predictions(val_y, val_baseline_preds)
    val_model_metrics = evaluate_predictions(val_y, val_model_preds)
    test_baseline_metrics = evaluate_predictions(test_y, test_baseline_preds)
    test_model_metrics = evaluate_predictions(test_y, test_model_preds)

    prediction_columns = [
        "sales_date",
        "store_id",
        "product_id",
        "units_sold",
        "units_lag_1d",
        "units_rolling_7d",
        "units_rolling_14d",
        "target_next_day_units",
    ]
    predictions = test_df[prediction_columns].copy()
    predictions["baseline_prediction"] = np.round(test_baseline_preds, 3)
    predictions["ridge_prediction"] = np.round(test_model_preds, 3)
    predictions["baseline_abs_error"] = np.round(np.abs(test_y - test_baseline_preds), 3)
    predictions["ridge_abs_error"] = np.round(np.abs(test_y - test_model_preds), 3)
    predictions.to_csv(MODEL_DIR / "test_predictions.csv", index=False)

    coefficients = pd.DataFrame(
        {
            "feature": ["intercept"] + feature_columns,
            "coefficient": beta,
        }
    )
    coefficients.to_csv(MODEL_DIR / "ridge_coefficients.csv", index=False)

    metadata = {
        "model_type": "ridge_regression_demand_forecasting",
        "target": TARGET_COLUMN,
        "train_end_date": TRAIN_END,
        "validation_end_date": VAL_END,
        "selected_alpha": best_alpha,
        "feature_columns": feature_columns,
        "train_rows": int(len(train_df)),
        "validation_rows": int(len(val_df)),
        "test_rows": int(len(test_df)),
        "validation_baseline_metrics": val_baseline_metrics,
        "validation_model_metrics": val_model_metrics,
        "test_baseline_metrics": test_baseline_metrics,
        "test_model_metrics": test_model_metrics,
        "feature_means": means.tolist(),
        "feature_stds": stds.tolist(),
    }
    (MODEL_DIR / "model_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    write_markdown_report(
        best_alpha,
        alpha_results,
        val_baseline_metrics,
        val_model_metrics,
        test_baseline_metrics,
        test_model_metrics,
        len(train_df),
        len(val_df),
        len(test_df),
    )

    print(f"Demand forecasting outputs written to: {MODEL_DIR}")


if __name__ == "__main__":
    main()
