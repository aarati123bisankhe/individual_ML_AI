from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from services.dashboard_service import DashboardService
from services.inventory_service import InventoryService
from services.model_service import ModelService
from services.navigation_service import NavigationService


app = FastAPI(
    title="Smart Grocery Backend",
    description="API layer for navigation, inventory, and scan-to-pay intelligence",
    version="1.0.0",
)

navigation_service = NavigationService()
inventory_service = InventoryService()
model_service = ModelService()
dashboard_service = DashboardService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "message": "Smart Grocery Backend is running",
        "available_endpoints": [
            "/health",
            "/api/navigation/search?q=milk&store_id=S01",
            "/api/inventory/demand?product_id=P000001&store_id=S01",
            "/api/models/customer-segment?customer_id=C0000001",
            "/api/models/scan-risk?transaction_id=T00000002",
            "/api/dashboard/summary",
        ],
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/navigation/search")
def navigation_search(
    q: str = Query(..., description="Product search query"),
    store_id: Optional[str] = Query(None, description="Optional store filter"),
    top_k: int = Query(5, ge=1, le=10),
) -> Dict[str, Any]:
    results = navigation_service.search_product(q, store_id, top_k)
    return {"query": q, "store_id": store_id, "results": results}


@app.get("/api/inventory/demand")
def inventory_demand(
    product_id: str = Query(..., description="Product id"),
    store_id: Optional[str] = Query(None, description="Optional store id"),
) -> Dict[str, Any]:
    results = inventory_service.get_product_demand(product_id, store_id)
    return {"product_id": product_id, "store_id": store_id, "results": results}


@app.get("/api/models/customer-segment")
def customer_segment(customer_id: str = Query(...)) -> Dict[str, Any]:
    result = model_service.get_customer_segment(customer_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Customer segment not found")
    return {"customer_id": customer_id, "result": result}


@app.get("/api/models/scan-risk")
def scan_risk(transaction_id: str = Query(...)) -> Dict[str, Any]:
    result = model_service.get_scan_risk(transaction_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Scan risk result not found")
    return {"transaction_id": transaction_id, "result": result}


@app.get("/api/dashboard/summary")
def dashboard_summary() -> Dict[str, Any]:
    return dashboard_service.get_summary()
