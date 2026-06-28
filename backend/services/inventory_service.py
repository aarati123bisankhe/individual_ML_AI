from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
DEMAND_PATH = BASE_DIR / "models" / "inventory_demand_classifier" / "test_predictions.csv"


class InventoryService:
    def __init__(self) -> None:
        self.predictions = pd.read_csv(DEMAND_PATH)

    def get_product_demand(
        self, product_id: str, store_id: Optional[str] = None
    ) -> List[Dict]:
        df = self.predictions[self.predictions["product_id"] == product_id].copy()
        if store_id and "store_id" in df.columns:
            df = df[df["store_id"] == store_id]
        return df.head(30).to_dict(orient="records")
