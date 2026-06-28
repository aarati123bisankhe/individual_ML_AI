# Inventory Demand Classification Summary

- Model: `Logistic regression implemented with numpy`
- Input: `data/features/daily_store_product_features.csv`
- Target: `target_has_demand` where 1 means next-day demand is greater than zero
- Train rows: `673936`
- Validation rows: `143664`
- Test rows: `141328`
- Selected threshold: `0.50`

## Validation Metrics
- Accuracy: 0.6329
- Precision: 0.6345
- Recall: 0.4886
- F1-score: 0.5521

## Test Metrics
- Accuracy: 0.6344
- Precision: 0.6216
- Recall: 0.4176
- F1-score: 0.4996