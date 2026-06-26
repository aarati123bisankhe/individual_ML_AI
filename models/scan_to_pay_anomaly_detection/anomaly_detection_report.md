# Scan-to-Pay Anomaly Detection Summary

- Model: `Robust z-score anomaly scoring`
- Input table: `data/features/transaction_features.csv`
- Scope: only transactions where `scan_to_pay_used = True`
- Evaluation label: proxy anomaly label based on failed payments, retries, failed scans, and rescans
- Proxy anomaly rate in test set: `0.4097`

## Validation Ranking Quality

| Top Fraction | Rows Checked | Precision | Recall |
|-------------:|-------------:|----------:|-------:|
| 0.01 | 43 | 0.6047 | 0.0135 |
| 0.05 | 219 | 0.7534 | 0.0854 |
| 0.10 | 438 | 0.7443 | 0.1686 |

## Test Ranking Quality

| Top Fraction | Rows Checked | Precision | Recall |
|-------------:|-------------:|----------:|-------:|
| 0.01 | 43 | 0.5349 | 0.0129 |
| 0.05 | 217 | 0.6912 | 0.0841 |
| 0.10 | 435 | 0.6897 | 0.1683 |

## Threshold-Based Test Classification

- Threshold: 17.7724
- Precision: 0.6845
- Recall: 0.0718
- Accuracy: 0.6062