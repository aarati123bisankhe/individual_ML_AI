# Scan-to-Pay Risk Classification Summary

- Model: `Logistic regression implemented with numpy`
- Input: `data/features/transaction_features.csv`
- Scope: only scan-to-pay transactions
- Target: risky vs normal transaction based on retries, failed payments, rescans, and failed scans
- Selected threshold: `0.45`

## Validation Metrics
- Accuracy: 0.9879
- Precision: 0.9875
- Recall: 0.9935
- F1-score: 0.9905

## Test Metrics
- Accuracy: 0.9844
- Precision: 0.9849
- Recall: 0.9900
- F1-score: 0.9874