# Demand Forecasting Model Summary

- Model: `Ridge regression implemented with numpy`
- Input table: `data/features/daily_store_product_features.csv`
- Prediction target: `target_next_day_units`
- Train rows: `673936`
- Validation rows: `143664`
- Test rows: `141328`
- Selected alpha: `0.1`

## Alpha Tuning on Validation Set

| Alpha | MAE | RMSE | WAPE |
|------:|----:|-----:|-----:|
| 0.1000 | 1.0071 | 1.4502 | 1.0052 |
| 1.0000 | 1.0071 | 1.4502 | 1.0052 |
| 5.0000 | 1.0071 | 1.4502 | 1.0052 |
| 10.0000 | 1.0071 | 1.4502 | 1.0052 |
| 25.0000 | 1.0071 | 1.4502 | 1.0052 |
| 50.0000 | 1.0071 | 1.4502 | 1.0052 |

## Validation Performance

- Naive baseline MAE: 1.1524
- Naive baseline RMSE: 1.7407
- Naive baseline WAPE: 1.1502
- Ridge model MAE: 1.0071
- Ridge model RMSE: 1.4502
- Ridge model WAPE: 1.0052

## Test Performance

- Naive baseline MAE: 1.0853
- Naive baseline RMSE: 1.6392
- Naive baseline WAPE: 1.2179
- Ridge model MAE: 0.9195
- Ridge model RMSE: 1.3363
- Ridge model WAPE: 1.0319

## Interpretation

- The baseline uses recent demand only: yesterday's units and the 7-day rolling average.
- The ridge model adds calendar, price, transaction, and festival features on top of lag features.
- This makes the forecasting pipeline explainable and easy to present in a thesis.