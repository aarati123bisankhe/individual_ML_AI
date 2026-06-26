# Recommendation Engine Summary

- Model: `Item co-occurrence recommendation engine`
- Training source: `transaction_items_clean.csv` + `transactions_clean.csv`
- Recommendation logic: products frequently purchased together are recommended together

## Evaluation

| Top-K | Evaluated Baskets | Hit Rate | MRR |
|------:|------------------:|---------:|----:|
| 3 | 7102 | 0.2629 | 0.2027 |
| 5 | 7102 | 0.2977 | 0.2107 |

## Strong Product Associations

- `Whole Chicken 1.2kg` -> `Onion (Pyaj) per kg` (confidence=0.802, co_purchase_count=324)
- `Dairy Milk 50g` -> `Coca-Cola 2L` (confidence=0.799, co_purchase_count=325)
- `Dairy Milk 50g` -> `Kurkure Masala Munch` (confidence=0.796, co_purchase_count=324)
- `Dairy Milk 50g` -> `Kurkure Masala Munch` (confidence=0.795, co_purchase_count=499)
- `Mutton (Khasi) 1kg` -> `Basmati Rice 5kg (Premium)` (confidence=0.786, co_purchase_count=261)
- `Whole Chicken 1.2kg` -> `Onion (Pyaj) per kg` (confidence=0.786, co_purchase_count=462)
- `KitKat 4-Finger` -> `Mountain Dew 2L` (confidence=0.785, co_purchase_count=438)
- `Dairy Milk 50g` -> `Lays Magic Masala 50g` (confidence=0.785, co_purchase_count=266)
- `Dairy Milk 50g` -> `Mountain Dew 2L` (confidence=0.784, co_purchase_count=433)
- `KitKat 4-Finger` -> `Mountain Dew 2L` (confidence=0.784, co_purchase_count=265)