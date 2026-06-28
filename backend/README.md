# Backend

This backend folder is the starting point for serving the smart retail app.

Main responsibilities:

- product search and navigation
- scan-to-pay transaction support
- inventory and dashboard APIs
- model result APIs

Current structure:

- `app.py`
  Lightweight HTTP API entry point
- `services/navigation_service.py`
  Product search and aisle lookup service
- `services/inventory_service.py`
  Inventory demand and stock insight service
- `services/model_service.py`
  Reads saved model outputs for segmentation, forecasting, and scan-to-pay risk
- `routes.py`
  Simple route mapping helper

Suggested future API endpoints:

- `/health`
- `/api/navigation/search?q=milk&store_id=S01`
- `/api/inventory/demand?store_id=S01&product_id=P000001`
- `/api/models/customer-segment?customer_id=C0000001`
- `/api/models/scan-risk?transaction_id=T00000002`
