from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]


class DashboardService:
    def __init__(self) -> None:
        self.navigation_meta = json.loads(
            (BASE_DIR / "models" / "navigation_realistic_search" / "model_metadata.json").read_text(encoding="utf-8")
        )
        self.inventory_meta = json.loads(
            (BASE_DIR / "models" / "inventory_demand_classifier" / "model_metadata.json").read_text(encoding="utf-8")
        )
        self.scan_meta = json.loads(
            (BASE_DIR / "models" / "scan_to_pay_risk_classifier" / "model_metadata.json").read_text(encoding="utf-8")
        )
        self.inventory_predictions = pd.read_csv(
            BASE_DIR / "models" / "inventory_demand_classifier" / "test_predictions.csv"
        )
        self.scan_predictions = pd.read_csv(
            BASE_DIR / "models" / "scan_to_pay_risk_classifier" / "test_predictions.csv"
        )

    def get_summary(self) -> Dict[str, Any]:
        high_demand = (
            self.inventory_predictions[self.inventory_predictions["predicted_class"] == 1]
            .sort_values("predicted_probability", ascending=False)
            .head(5)
            .to_dict(orient="records")
        )
        risky_transactions = (
            self.scan_predictions[self.scan_predictions["predicted_class"] == 1]
            .sort_values("predicted_probability", ascending=False)
            .head(5)
            .to_dict(orient="records")
        )

        return {
            "navigation_accuracy_pct": round(
                self.navigation_meta["overall_top1_aisle_accuracy"] * 100, 2
            ),
            "inventory_accuracy_pct": round(
                self.inventory_meta["test_metrics"]["accuracy"] * 100, 2
            ),
            "scan_risk_accuracy_pct": round(
                self.scan_meta["test_metrics"]["accuracy"] * 100, 2
            ),
            "high_demand_products": high_demand,
            "risky_transactions": risky_transactions,
        }
