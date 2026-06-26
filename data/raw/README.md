# UrbanMart Smart Retail Dataset (Synthetic)

**Project:** Smart Grocery Navigation + Scan-to-Pay thesis
**Version:** 1.0.0
**Locale:** Kathmandu valley, Nepal — NPR pricing, Nepali payment rails, festival calendar
**Generator seed:** `7` (fully reproducible)

---

## 1. What this dataset is — and what it is not

This is a **synthetic** dataset modeled on a generic urban supermarket chain operating in the Kathmandu valley. It is referred to throughout as **"UrbanMart"** to make the synthetic nature explicit. It is **not** Bhatbhateni, Big Mart, Salesberry, or any other real Nepali retailer. No real operational data has been scraped, leaked, or otherwise obtained; every row is generated programmatically from documented statistical assumptions in `generate_dataset.py`.

This naming and disclosure is intentional — a thesis that presents synthetic data as if it came from a real, named, privately-held company runs into both academic-integrity and trademark issues. By labeling it "UrbanMart" and being upfront, you can use this dataset freely in your thesis, code repositories, and published artifacts.

The dataset captures the operational reality of a Nepali urban supermarket — it uses NPR pricing, 13% VAT, Nepal-native payment rails (eSewa, Khalti, IME Pay, FonePay, ConnectIPS), local product mix (Wai Wai, DDC milk, Tulsi mustard oil, basmati rice, Tokla tea, etc.), Kathmandu-valley store locations, and a festival calendar with surges around Dashain, Tihar, and Nepali New Year.

---

## 2. Schema (entity-relationship)

```
                ┌─────────┐         ┌──────────┐
                │ stores  │ 1 ───── │  zones   │
                └────┬────┘         └─────┬────┘
                     │ 1                  │ 1
                     │                    │
                     │ N                  │ N
                ┌────┴────┐         ┌─────┴────┐
                │ aisles  │ ─────── │ products │
                └─────────┘    1:N  └──────────┘
                                          │ N
                                          │
        ┌───────────┐                     │ 1
        │ customers │ 1                   │
        └─────┬─────┘                     │
              │ N                         │
              │                  ┌────────┴───────┐
       ┌──────┴───────┐      ┌── │ transaction_   │
       │ transactions │ 1:N ─┤   │ items          │
       └──────┬───────┘      │   └────────────────┘
              │ 1            │
              │              │
              │ 1:N          │
       ┌──────┴───────┐      │
       │ app_events   │      │
       └──────────────┘      │
       ┌──────────────┐      │
       │ payment_     │ 1:N  │
       │ events       ├──────┘
       └──────────────┘
```

### Tables (under `data/`)

| File | Rows | Purpose |
|---|---:|---|
| `stores.csv` | 8 | Store metadata (8 Kathmandu-valley stores) |
| `zones.csv` | 17 | Zone definitions (Fresh, Dairy, Frozen, Snacks, etc.) with ambient temp |
| `aisles.csv` | 200 | Per-store aisle records with floor x/y coordinates |
| `products.csv` | 1,168 | Per-store product listings — each SKU carries shelf coordinates |
| `customers.csv` | 25,000 | Anonymized profiles: loyalty tier, gender, age bucket, home area, app-usage |
| `transactions.csv` | 50,000 | Transaction headers (one row per receipt) |
| `transaction_items.csv` | 652,655 | Line items — **the core scan event log** |
| `app_events.csv` | 158,241 | In-app `search_query` and `directions_request` events — **the navigation signal** |
| `payment_events.csv` | 52,879 | Per-attempt payment events for latency/retry analysis |

Full column-level data dictionary lives in `samples/smart_retail_dataset_overview.xlsx → Data Dictionary` sheet.

---

## 3. Why this schema fits Smart Grocery Navigation + Scan-to-Pay

**Navigation signal** — every product carries `(zone_id, aisle_id, shelf_number, shelf_position)` and every aisle carries `(x_coord, y_coord)`. The `app_events.csv` table records what customers searched for and which aisles they asked the app to navigate them to. This gives you:

- a `search_query → target_aisle_id` supervised dataset (text-to-aisle prediction)
- co-aisle visit graphs from line items (shelf-placement optimization)
- dwell time and aisles-visited per trip (in-store routing)

**Scan-to-pay signal** — every line item carries `(scan_timestamp, scan_method, scan_duration_ms, rescans, scan_success)`. Every transaction carries `(payment_method, scan_to_pay_used, payment_attempts, payment_status)`. The `payment_events.csv` table records each attempt with `latency_ms` and a status of `success/failed/retry`. This gives you:

- scan fraud / error detection (rescans, scan_success)
- payment latency benchmarking across rails (eSewa vs Khalti vs Card)
- multi-attempt failure modeling
- correlation between basket size and checkout time

---

## 4. Train / val / test splits

Splits are **time-based**, not random — this is the right choice for retail data because real production models always train on the past and predict the future. See `splits/` folder for transaction-ID lists.

| Split | Count | Date range |
|---|---:|---|
| Train | 35,000 | 2024-01-01 → 2025-07-30 |
| Val   |  7,500 | 2025-07-30 → 2025-11-30 |
| Test  |  7,500 | 2025-11-30 → 2026-03-31 |

To assemble each split, filter `transactions.csv` by the corresponding ID list, then join `transaction_items`, `app_events`, and `payment_events` on `transaction_id`.

---

## 5. Generation methodology

### Customer behavior model
- 25,000 customers with gamma-distributed visit propensity (heavy-tailed — a few customers come often)
- Loyalty tier multiplier: Standard 1.0× → Silver 1.5× → Gold 2.2× → Platinum 3.0×
- 62% of customers use the smart-shopping app
- Home area drives 65%-probability "go to nearest store" with the rest distributed by store traffic weight

### Time distribution
- Date range: Jan 1 2024 → Mar 31 2026 (~821 days)
- Day-of-week weights bias toward weekends (Sat/Sun ~22% each, weekdays 10–13%)
- Hour distribution peaks 17:00–20:00, store closed 00:00–06:00
- Festival windows (Dashain Oct 5-16, Tihar Nov 1-7, Nepali New Year Apr 10-16) increase basket sizes substantially

### Basket composition
Mixture of four regimes — quick-stop (~3 items), regular shop (~8), big shop (~22), festival haul (~50). Within a basket, items are first sampled by category-weighted probability (staples, vegetables, dairy, snacks weighted higher), then "themes" (breakfast, tea-time, wai-wai-meal, meat-meal, veg-meal, kids, cleaning, snacking, festival) probabilistically pull additional related items to create realistic co-occurrence.

### Pricing & taxes
- Per-store ±5% price variance from a master price list
- 13% Nepali VAT
- Loyalty discount: Silver 2%, Gold 4%, Platinum 7%
- Festival period: additional 3% discount

### Payment mix
- App users skew digital (75% probability of using a digital rail)
- Distribution: eSewa ~21%, Khalti ~18%, Cash ~16%, FonePay ~15%, Card ~15%, IME Pay ~14%, ConnectIPS ~2%
- Multi-attempt simulation: ~6% of digital payments require a retry; ~4% of those ultimately fail

### Scan event mix
- App scan-to-pay users: barcode 78%, QR 16%, manual entry 6%; mean scan duration 1.6 s ± 0.7 s
- Cashier (POS) scans: faster, no rescans modeled
- 1.5% of app scans require a rescan; 8% of those a second rescan

---

## 6. Sample size note (50K vs the 100K originally requested)

The generator was executed at **50,000 transactions / 652,655 line items** because the build environment has a runtime cap. To regenerate at the originally requested 100K scale on your own machine:

```bash
# In generate_dataset.py, change:
N_TRANSACTIONS = 50_000
# to:
N_TRANSACTIONS = 100_000

python3 generate_dataset.py     # ~3–4 min on a normal laptop
python3 build_supporting.py     # rebuilds splits + XLSX + metadata
```

50K transactions is already substantial for thesis-grade ML training — comparable to the public Online Retail II UCI dataset (~520K rows) and well above what most academic papers in this space use for prototype evaluation. Doubling to 100K is straightforward but not required.

---

## 7. Research tasks this dataset supports

1. **Search-to-aisle prediction** — given a search_query string from `app_events`, predict the `target_aisle_id` (multi-class classification or retrieval over aisle embeddings).
2. **Shelf placement / store layout optimization** — use market-basket lift between products to evaluate whether co-purchased products are co-located (zones/aisles), and propose layout changes.
3. **In-store path & dwell modeling** — given basket composition + customer profile, predict dwell time and number of aisles visited.
4. **Scan-to-pay anomaly detection** — flag transactions where rescans, scan_success rate, or scan duration deviate from expected baselines (proxy for fraud or app issues).
5. **Payment latency benchmarking** — compare `latency_ms` across `payment_method`s and analyze retry behavior.
6. **Customer segmentation** — RFM (recency / frequency / monetary) on `transactions.csv`, conditioned on `loyalty_tier`, `age_bucket`, and `uses_app`.
7. **Demand forecasting** — `(product_id, store_id, date)` time series for SKU-level forecasting; compare ARIMA, Prophet, gradient boosting.
8. **Festival surge analysis** — use `is_festival_period` to study how basket composition and value shift during festivals.
9. **Recommendation systems** — given current basket, recommend the next product (sequential or matrix-factorization approaches).

---

## 8. Limitations and ethical notes

- **Fully synthetic.** Distributions are realistic but not learned from real Nepali retail data. Findings on this dataset should be reported as proof-of-method on synthetic data and replicated on real data (or at least real public benchmark datasets) before strong claims are made.
- **No PII.** Customer IDs are random strings with no real identity attached. Demographic fields are coarse (age buckets, not ages; areas, not addresses).
- **Co-purchase realism is theme-template driven.** Real receipts would surface associations the templates miss. Treat the basket-affinity structure as a reasonable scaffold, not ground truth.
- **Aisle x/y coordinates are randomly placed within a 0-100 floor unit.** For a real store-routing study, swap these for a measured store layout.
- **No real company is depicted.** The dataset is a generic Kathmandu-valley supermarket simulation. Do not relabel "UrbanMart" as a real chain in your thesis.

---

## 9. File inventory

```
smart_retail_dataset/
├── README.md                                 # this file
├── dataset_metadata.json                     # machine-readable summary
├── generate_dataset.py                       # reproducible generator (seed=7)
├── build_supporting.py                       # builds splits + XLSX + metadata
├── data/
│   ├── stores.csv
│   ├── zones.csv
│   ├── aisles.csv
│   ├── products.csv
│   ├── customers.csv
│   ├── transactions.csv
│   ├── transaction_items.csv
│   ├── app_events.csv
│   └── payment_events.csv
├── splits/
│   ├── train_transaction_ids.csv
│   ├── val_transaction_ids.csv
│   └── test_transaction_ids.csv
└── samples/
    └── smart_retail_dataset_overview.xlsx    # README + dictionary + stats + 1k-row previews
```

---

## 10. How to cite (suggested)

> [Your Name] (2026). *UrbanMart Smart Retail Synthetic Dataset for Smart Grocery Navigation and Scan-to-Pay research.* Synthetic dataset generated for thesis work, Kathmandu-valley locale. Generation seed = 7. Available at: [your repository link].

The dataset is free to use, modify, and redistribute for academic and commercial purposes. Attribution is appreciated but not required.
