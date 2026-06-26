# Model Evaluation Summary

This report combines the main evaluation results for all current ML models in the project.

## Model Overview

| Model | Type | Dataset | Primary Metric | Value |
|------|------|---------|----------------|------:|
| Customer Segmentation | kmeans_customer_segmentation | customer_features.csv | silhouette_score | 0.3268 |
| Demand Forecasting | ridge_regression_demand_forecasting | daily_store_product_features.csv | test_rmse | 1.3363 |
| Recommendation Engine | item_cooccurrence_recommender | transaction_items_clean.csv | hit_rate_at_5 | 0.2977 |
| Scan-to-Pay Anomaly Detection | robust_zscore_scan_to_pay_anomaly_detection | transaction_features.csv | precision_at_top_10pct | 0.6897 |

## Key Findings

- Customer Segmentation `silhouette_score` = 0.3268. Higher is better. Measures cluster separation and cohesion.
- Demand Forecasting `validation_rmse` improved from 1.7407 to 1.4502 (16.69% better). Lower is better. Ridge model reduces forecast error on validation data.
- Demand Forecasting `test_rmse` improved from 1.6392 to 1.3363 (18.48% better). Lower is better. Main forecasting result on unseen test data.
- Demand Forecasting `test_mae` improved from 1.0853 to 0.9195 (15.27% better). Lower is better. Measures average absolute daily forecast error.
- Recommendation Engine `hit_rate_at_3` = 0.2629. Higher is better. True item appears in top 3 recommendations.
- Recommendation Engine `hit_rate_at_5` = 0.2977. Higher is better. True item appears in top 5 recommendations.
- Recommendation Engine `mrr_at_5` = 0.2107. Higher is better. Rewards correct recommendations appearing earlier.
- Scan-to-Pay Anomaly Detection `precision_at_top_5pct` = 0.6912. Higher is better. Measures anomaly quality among the top-ranked flagged transactions.
- Scan-to-Pay Anomaly Detection `precision_at_top_10pct` = 0.6897. Higher is better. Useful for prioritized operational review.
- Scan-to-Pay Anomaly Detection `threshold_precision` = 0.6845. Higher is better. Precision of binary anomaly alerts at the selected threshold.

## Thesis Interpretation

- Customer segmentation produced meaningful groups with a silhouette score above 0.32, which is a reasonable first clustering result.
- Demand forecasting outperformed the naive baseline on validation and test data, showing that engineered features improved prediction quality.
- The recommendation engine achieved useful top-k hit rates for a baseline market-basket model and can be improved later with more advanced methods.
- The anomaly detector is most useful as a ranked alerting model, where the top flagged scan-to-pay transactions show much higher anomaly concentration than the full dataset.