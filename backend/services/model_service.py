from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]


class ModelService:
    def __init__(self) -> None:
        self.customer_segments = pd.read_csv(
            BASE_DIR / "models" / "customer_segmentation" / "customer_segments.csv"
        )
        self.scan_risk = pd.read_csv(
            BASE_DIR / "models" / "scan_to_pay_risk_classifier" / "test_predictions.csv"
        )

    def get_customer_segment(self, customer_id: str) -> Optional[Dict]:
        match = self.customer_segments[self.customer_segments["customer_id"] == customer_id]
        if match.empty:
            return None
        return match.iloc[0].to_dict()

    def get_scan_risk(self, transaction_id: str) -> Optional[Dict]:
        match = self.scan_risk[self.scan_risk["transaction_id"] == transaction_id]
        if match.empty:
            return None
        return match.iloc[0].to_dict()
