# Customer Segmentation Model Summary

- Chosen number of clusters: `3`
- Algorithm: `K-Means clustering implemented with numpy`
- Input table: `data/features/customer_features.csv`
- Output table: `models/customer_segmentation/customer_segments.csv`

## K Evaluation

| k | Inertia | Silhouette Score |
|---|---------|------------------|
| 3 | 215008.15 | 0.3268 |
| 4 | 178196.94 | 0.3239 |
| 5 | 169284.71 | 0.2873 |
| 6 | 151334.81 | 0.2923 |

## Segment Summary

### Segment 0: Occasional Traditional Shoppers
- Customers: 6831
- Avg transactions: 0.03
- Avg spend (NPR): 15.39
- Avg order value (NPR): 15.04
- Avg basket size: 0.05
- Avg scan-to-pay rate: 0.00
- Avg app engagement events: 0.00
- Avg recency days: 942.86
- Most common payment method: No Purchase
- Most common loyalty tier: Standard

### Segment 1: Regular Digital Shoppers
- Customers: 13067
- Avg transactions: 2.08
- Avg spend (NPR): 9723.69
- Avg order value (NPR): 4773.61
- Avg basket size: 10.34
- Avg scan-to-pay rate: 0.51
- Avg app engagement events: 3.74
- Avg recency days: 304.28
- Most common payment method: Cash
- Most common loyalty tier: Standard

### Segment 2: High Value Loyal Customers
- Customers: 5102
- Avg transactions: 4.44
- Avg spend (NPR): 36894.92
- Avg order value (NPR): 10623.99
- Avg basket size: 20.25
- Avg scan-to-pay rate: 0.74
- Avg app engagement events: 21.42
- Avg recency days: 193.30
- Most common payment method: Card
- Most common loyalty tier: Standard
