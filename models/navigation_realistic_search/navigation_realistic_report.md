# Realistic Navigation Search Summary

- Model: `Fuzzy product search and aisle locator`
- Input: `products.csv` with synthetic realistic query variants
- Overall Top-1 product accuracy: `0.7446`
- Overall Top-1 aisle accuracy: `0.8940`
- Overall Top-3 product accuracy: `0.8313`

## Query-Type Results

- `category`: Top-1 product=0.1164, Top-1 aisle=0.6344, Top-3 product=0.3613
- `exact`: Top-1 product=1.0000, Top-1 aisle=1.0000, Top-3 product=1.0000
- `misspelled`: Top-1 product=0.9092, Top-1 aisle=0.9495, Top-3 product=0.9640
- `partial`: Top-1 product=0.9529, Top-1 aisle=0.9923, Top-3 product=1.0000