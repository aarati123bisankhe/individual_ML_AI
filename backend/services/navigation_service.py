from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]
PRODUCTS_PATH = BASE_DIR / "data" / "raw" / "products.csv"


def normalize(text: str) -> str:
    return " ".join(str(text).lower().replace("-", " ").split())


class NavigationService:
    def __init__(self) -> None:
        self.products = pd.read_csv(PRODUCTS_PATH)
        self.products["normalized_name"] = self.products["product_name"].map(normalize)

    def search_product(
        self, query: str, store_id: Optional[str] = None, top_k: int = 5
    ) -> List[Dict]:
        query_norm = normalize(query)
        df = self.products.copy()
        if store_id:
            df = df[df["store_id"] == store_id]

        df["score"] = df["normalized_name"].map(
            lambda name: SequenceMatcher(None, query_norm, name).ratio()
        )
        ranked = df.sort_values("score", ascending=False).head(top_k)
        columns = [
            "product_id",
            "product_name",
            "subcategory",
            "store_id",
            "zone_id",
            "aisle_id",
            "shelf_number",
            "shelf_position",
            "price_npr",
            "score",
        ]
        return ranked[columns].to_dict(orient="records")
