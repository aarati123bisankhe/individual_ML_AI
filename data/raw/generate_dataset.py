"""
Synthetic Smart Retail Dataset Generator
========================================

Project: Smart Grocery Navigation + Scan-to-Pay system thesis
Scale  : 100,000 transactions (~800K line items)

Modeled on a generic urban Nepali supermarket chain (NPR pricing, Kathmandu-
valley locations, Nepal-native payment rails: eSewa, Khalti, IME Pay,
ConnectIPS, FonePay). No real company is named — the chain is referred to
generically as "UrbanMart" so the dataset is safe to publish in a thesis
without trademark or misrepresentation issues.

The schema is purpose-built to support the two primary research tasks:

  1.  SMART GROCERY NAVIGATION
      - Every product carries (store_id, aisle_id, shelf_id, x, y) so models
        can learn shelf placement, in-store routing, and search-to-aisle
        recommendations.
      - app_events.csv records in-app searches, "directions" requests and
        zone visits during a trip.

  2.  SCAN-TO-PAY
      - Every line item carries a scan_timestamp, scan_method (barcode / QR
        / manual), scan_duration_ms, and rescans count.
      - payment_events.csv captures attempts, retries, latency and result
        for each transaction (fraud / failure / success modeling).

Output is split across multiple CSVs (relational), with a sample workbook
in XLSX for human inspection and a README for the thesis appendix.
"""

import csv
import json
import random
import math
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

random.seed(7)
np.random.seed(7)

OUT = Path("/home/claude/retail")
DATA = OUT / "data"
DATA.mkdir(exist_ok=True, parents=True)

# ---------------------------------------------------------------------------
# 1. Stores (Kathmandu valley locations)
# ---------------------------------------------------------------------------
STORES = [
    # (store_id, name, city, area, lat, lng, sqft, num_aisles, opening_year)
    ("S01", "UrbanMart Maharajgunj",  "Kathmandu", "Maharajgunj",  27.7370, 85.3300, 18000, 14, 2009),
    ("S02", "UrbanMart Pulchowk",     "Lalitpur",  "Pulchowk",     27.6788, 85.3179, 14500, 12, 2012),
    ("S03", "UrbanMart Chuchhepati",  "Kathmandu", "Chuchhepati",  27.7185, 85.3540, 12000, 11, 2015),
    ("S04", "UrbanMart Bhaktapur",    "Bhaktapur", "Suryabinayak", 27.6650, 85.4280, 9800,  10, 2017),
    ("S05", "UrbanMart Naxal",        "Kathmandu", "Naxal",        27.7148, 85.3310, 11000, 10, 2018),
    ("S06", "UrbanMart Sanepa",       "Lalitpur",  "Sanepa",       27.6890, 85.3105, 10500, 10, 2019),
    ("S07", "UrbanMart Tinkune",      "Kathmandu", "Tinkune",      27.6900, 85.3500, 13500, 12, 2021),
    ("S08", "UrbanMart Budhanilkantha","Kathmandu","Budhanilkantha",27.7800,85.3620, 9000,  9,  2022),
]

stores_df = pd.DataFrame(STORES, columns=[
    "store_id", "store_name", "city", "area", "latitude", "longitude",
    "size_sqft", "num_aisles", "opening_year",
])

# Per-store traffic weight (used to decide which store a transaction is in)
STORE_TRAFFIC_WEIGHT = {
    "S01": 22, "S02": 16, "S03": 12, "S04": 10,
    "S05": 14, "S06": 10, "S07": 11, "S08": 5,
}

# ---------------------------------------------------------------------------
# 2. Store zones / aisles (the "navigation" layer)
# ---------------------------------------------------------------------------
ZONES = [
    # (zone_id, zone_name, ambient_temp_c, is_perimeter)
    ("Z01", "Entry / Trolleys",           22, True),
    ("Z02", "Fresh Produce",              16, True),
    ("Z03", "Bakery",                     22, True),
    ("Z04", "Dairy & Eggs",                4, True),
    ("Z05", "Frozen Foods",              -18, True),
    ("Z06", "Meat & Seafood",              4, True),
    ("Z07", "Dry Staples (Rice/Dal/Atta)",22, False),
    ("Z08", "Cooking Oils & Ghee",        22, False),
    ("Z09", "Spices & Condiments",        22, False),
    ("Z10", "Snacks & Confectionery",     22, False),
    ("Z11", "Beverages",                  22, False),
    ("Z12", "Tea / Coffee / Health Drinks",22,False),
    ("Z13", "Personal Care",              22, False),
    ("Z14", "Household & Cleaning",       22, False),
    ("Z15", "Baby Care",                  22, False),
    ("Z16", "Stationery & Misc",          22, False),
    ("Z17", "Checkout / Scan-to-Pay",     22, True),
]
zones_df = pd.DataFrame(ZONES, columns=["zone_id", "zone_name", "ambient_temp_c", "is_perimeter"])

# Aisles within each zone (most zones have 1-3 aisles)
AISLES_PER_ZONE = {
    "Z01": 1, "Z02": 2, "Z03": 1, "Z04": 1, "Z05": 1, "Z06": 1,
    "Z07": 3, "Z08": 1, "Z09": 2, "Z10": 2, "Z11": 2, "Z12": 1,
    "Z13": 2, "Z14": 2, "Z15": 1, "Z16": 1, "Z17": 1,
}

aisle_rows = []
aisle_counter = 1
for store_id in stores_df["store_id"]:
    for z_id, _, _, _ in ZONES:
        for k in range(AISLES_PER_ZONE[z_id]):
            aisle_id = f"A{aisle_counter:04d}"
            aisle_counter += 1
            # x / y store-floor coordinates (relative units 0-100)
            x = round(random.uniform(5, 95), 1)
            y = round(random.uniform(5, 95), 1)
            aisle_rows.append((aisle_id, store_id, z_id, k + 1, x, y))
aisles_df = pd.DataFrame(aisle_rows, columns=[
    "aisle_id", "store_id", "zone_id", "aisle_number_in_zone", "x_coord", "y_coord",
])

# ---------------------------------------------------------------------------
# 3. Product master catalogue (Nepali urban supermarket reality)
# ---------------------------------------------------------------------------
# (subcategory, product_name, brand, base_price_npr, unit, zone_id)
PRODUCT_SEED = [
    # --- Z02 Fresh produce (priced per kg or per unit) ---
    ("Vegetables", "Onion (Pyaj) per kg",        "Local", 95,   "kg",  "Z02"),
    ("Vegetables", "Potato (Aalu) per kg",       "Local", 75,   "kg",  "Z02"),
    ("Vegetables", "Tomato per kg",              "Local", 110,  "kg",  "Z02"),
    ("Vegetables", "Cauliflower per kg",         "Local", 90,   "kg",  "Z02"),
    ("Vegetables", "Spinach (Palungo) bundle",   "Local", 35,   "bundle","Z02"),
    ("Vegetables", "Carrot per kg",              "Local", 120,  "kg",  "Z02"),
    ("Vegetables", "Cabbage per piece",          "Local", 80,   "pc",  "Z02"),
    ("Vegetables", "Green Chilli (Khursani) 100g","Local",30,   "100g","Z02"),
    ("Vegetables", "Garlic (Lasun) per kg",      "Local", 280,  "kg",  "Z02"),
    ("Vegetables", "Ginger (Aduwa) per kg",      "Local", 220,  "kg",  "Z02"),
    ("Vegetables", "Brinjal (Bhanta) per kg",    "Local", 95,   "kg",  "Z02"),
    ("Vegetables", "Bottle Gourd (Lauka) per pc","Local", 65,   "pc",  "Z02"),
    ("Vegetables", "Mushroom 200g pack",         "Local", 150,  "pack","Z02"),
    ("Vegetables", "Coriander (Dhania) bundle",  "Local", 25,   "bundle","Z02"),
    ("Fruits",     "Apple (Imported) per kg",    "Imported",380,"kg", "Z02"),
    ("Fruits",     "Apple (Mustang) per kg",     "Local", 250,  "kg",  "Z02"),
    ("Fruits",     "Banana per dozen",           "Local", 110,  "dozen","Z02"),
    ("Fruits",     "Orange per kg",              "Local", 200,  "kg",  "Z02"),
    ("Fruits",     "Pomegranate per kg",         "Imported",420,"kg", "Z02"),
    ("Fruits",     "Watermelon per kg",          "Local", 60,   "kg",  "Z02"),
    ("Fruits",     "Mango per kg (seasonal)",    "Local", 180,  "kg",  "Z02"),
    ("Fruits",     "Grapes per kg",              "Imported",350,"kg", "Z02"),
    # --- Z03 Bakery ---
    ("Bakery",     "Sliced Bread 400g",          "Hot Breads",  85, "pack","Z03"),
    ("Bakery",     "Whole Wheat Bread 500g",     "Hot Breads", 120, "pack","Z03"),
    ("Bakery",     "Burger Buns (Pack of 6)",    "Hot Breads", 150, "pack","Z03"),
    ("Bakery",     "Croissant (single)",         "Roadhouse",   90, "pc",  "Z03"),
    ("Bakery",     "Cream Roll Pack",            "Krishna Pauroti", 110,"pack","Z03"),
    ("Bakery",     "Donut (Glazed) per pc",      "Roadhouse",   75, "pc",  "Z03"),
    ("Bakery",     "Cake Slice (Chocolate)",     "Hot Breads", 130, "pc",  "Z03"),
    # --- Z04 Dairy ---
    ("Dairy",      "DDC Milk 500ml",             "DDC",         55, "pack","Z04"),
    ("Dairy",      "DDC Milk 1L",                "DDC",        108, "pack","Z04"),
    ("Dairy",      "Sujal Yoghurt 400g",         "Sujal",       95, "tub", "Z04"),
    ("Dairy",      "Amul Butter 500g",           "Amul",       560, "pack","Z04"),
    ("Dairy",      "Amul Cheese Cubes 200g",     "Amul",       275, "pack","Z04"),
    ("Dairy",      "Pure Cow Ghee 500ml",        "Sitaram",    675, "tin", "Z04"),
    ("Dairy",      "Buffalo Ghee 1L",            "Sujal",     1250, "tin", "Z04"),
    ("Dairy",      "Mozzarella Cheese 200g",     "Britannia",  340, "pack","Z04"),
    ("Dairy",      "Eggs (Tray of 30)",          "Local Farm", 525, "tray","Z04"),
    ("Dairy",      "Eggs (Pack of 6)",           "Local Farm", 110, "pack","Z04"),
    # --- Z05 Frozen ---
    ("Frozen",     "Frozen Chicken Sausage 250g","Nimbus",     325, "pack","Z05"),
    ("Frozen",     "Frozen Momo (Veg) 30pc",     "Hangrila",   295, "pack","Z05"),
    ("Frozen",     "Frozen Momo (Buff) 30pc",    "Hangrila",   330, "pack","Z05"),
    ("Frozen",     "Frozen French Fries 1kg",    "McCain",     485, "pack","Z05"),
    ("Frozen",     "Frozen Peas 500g",           "Sumeru",     180, "pack","Z05"),
    ("Frozen",     "Ice Cream Tub 1L (Vanilla)", "KFC Ice Cream",480,"tub","Z05"),
    ("Frozen",     "Ice Cream Tub 1L (Chocolate)","Igloo",     460, "tub", "Z05"),
    # --- Z06 Meat & Seafood ---
    ("Meat",       "Chicken Breast (Boneless) 1kg","Valley Cold Store", 480,"kg","Z06"),
    ("Meat",       "Whole Chicken 1.2kg",        "Valley Cold Store", 520,"pc","Z06"),
    ("Meat",       "Buff Mince 500g",            "Local Butcher",  340,"pack","Z06"),
    ("Meat",       "Mutton (Khasi) 1kg",         "Local Butcher", 1450,"kg","Z06"),
    ("Meat",       "Pork Belly 500g",            "Local Butcher",  420,"pack","Z06"),
    ("Meat",       "Fish (Rohu) per kg",         "Local",          385,"kg","Z06"),
    ("Meat",       "Prawns Frozen 500g",         "Imported",       780,"pack","Z06"),
    # --- Z07 Dry staples ---
    ("Staples",    "Basmati Rice 5kg (Premium)", "India Gate",    1850,"bag","Z07"),
    ("Staples",    "Basmati Rice 25kg",          "Daawat",        7200,"bag","Z07"),
    ("Staples",    "Sona Mansuli Rice 25kg",     "Local Mill",    4200,"bag","Z07"),
    ("Staples",    "Atta (Wheat Flour) 10kg",    "Annapurna",     1150,"bag","Z07"),
    ("Staples",    "Maida (Refined Flour) 5kg",  "Annapurna",      525,"bag","Z07"),
    ("Staples",    "Toor Dal (Rahar) 1kg",       "Local",          265,"pack","Z07"),
    ("Staples",    "Masoor Dal (Musuro) 1kg",    "Local",          195,"pack","Z07"),
    ("Staples",    "Moong Dal 1kg",              "Local",          245,"pack","Z07"),
    ("Staples",    "Chana Dal 1kg",              "Local",          205,"pack","Z07"),
    ("Staples",    "Sugar 1kg",                  "Sona",            115,"pack","Z07"),
    ("Staples",    "Salt 1kg (Iodized)",         "Tata",             55,"pack","Z07"),
    ("Staples",    "Brown Rice 2kg",             "Organic Valley", 380,"bag","Z07"),
    ("Staples",    "Beaten Rice (Chiura) 1kg",   "Local",          145,"pack","Z07"),
    # --- Z08 Cooking oils ---
    ("Oils",       "Mustard Oil 5L",             "Tulsi",          1450,"bottle","Z08"),
    ("Oils",       "Mustard Oil 1L",             "Tulsi",           320,"bottle","Z08"),
    ("Oils",       "Sunflower Oil 5L",           "Fortune",        1380,"bottle","Z08"),
    ("Oils",       "Soybean Oil 5L",             "Dhara",          1290,"bottle","Z08"),
    ("Oils",       "Olive Oil 500ml",            "Figaro",          780,"bottle","Z08"),
    ("Oils",       "Vanaspati Ghee 1kg",         "Dalda",           385,"tin","Z08"),
    # --- Z09 Spices & condiments ---
    ("Spices",     "Turmeric Powder 200g",       "Catch",            85,"pack","Z09"),
    ("Spices",     "Chilli Powder 200g",         "Catch",            95,"pack","Z09"),
    ("Spices",     "Cumin Seeds 100g",           "Catch",            75,"pack","Z09"),
    ("Spices",     "Coriander Powder 200g",      "Catch",            88,"pack","Z09"),
    ("Spices",     "Garam Masala 100g",          "Everest",         115,"pack","Z09"),
    ("Spices",     "Mustard Seeds 200g",         "Local",            65,"pack","Z09"),
    ("Spices",     "Timur (Sichuan Pepper) 100g","Local",           225,"pack","Z09"),
    ("Spices",     "Bay Leaves 50g",             "Local",            45,"pack","Z09"),
    ("Spices",     "Cardamom 100g",              "Local",           450,"pack","Z09"),
    ("Sauces",     "Soy Sauce 500ml",            "Kikkoman",        285,"bottle","Z09"),
    ("Sauces",     "Tomato Ketchup 1kg",         "Heinz",           345,"bottle","Z09"),
    ("Sauces",     "Mayonnaise 500g",            "Veeba",           265,"jar","Z09"),
    ("Sauces",     "Chilli Sauce 200ml",         "Maggi",           110,"bottle","Z09"),
    # --- Z10 Snacks & confectionery ---
    ("Snacks",     "Wai Wai Chicken (Pack of 30)","Chaudhary Group", 750,"box","Z10"),
    ("Snacks",     "Wai Wai Veg (Pack of 30)",   "Chaudhary Group", 720,"box","Z10"),
    ("Snacks",     "Wai Wai Single Pack",        "Chaudhary Group",  25,"pack","Z10"),
    ("Snacks",     "RaRa Noodles Single Pack",   "Himalayan Snax",   22,"pack","Z10"),
    ("Snacks",     "2PM Chicken Noodles",        "Asian Thai",       28,"pack","Z10"),
    ("Snacks",     "Maggi 2-Min 70g",            "Nestle",           28,"pack","Z10"),
    ("Snacks",     "Lays Magic Masala 50g",      "Lays",             50,"pack","Z10"),
    ("Snacks",     "Kurkure Masala Munch",       "Pepsico",          25,"pack","Z10"),
    ("Snacks",     "Current Bites",              "CG Foods",         20,"pack","Z10"),
    ("Snacks",     "Mayos Potato Chips",         "Mayos",            45,"pack","Z10"),
    ("Snacks",     "Coconut Crunchies Biscuit",  "Shree",            45,"pack","Z10"),
    ("Snacks",     "Marie Gold Biscuit",         "Britannia",        35,"pack","Z10"),
    ("Snacks",     "Good Day Cookies",           "Britannia",        50,"pack","Z10"),
    ("Snacks",     "Oreo Vanilla 120g",          "Cadbury",          75,"pack","Z10"),
    ("Snacks",     "Bourbon Cream Biscuit",      "Britannia",        45,"pack","Z10"),
    ("Confectionery","Dairy Milk 50g",           "Cadbury",         110,"bar","Z10"),
    ("Confectionery","KitKat 4-Finger",          "Nestle",           80,"bar","Z10"),
    ("Confectionery","Snickers 50g",             "Mars",            120,"bar","Z10"),
    ("Confectionery","Mentos Roll",              "Mentos",           30,"roll","Z10"),
    ("Confectionery","Center Fresh Gum",         "Perfetti",         25,"pack","Z10"),
    # --- Z11 Beverages ---
    ("Beverages",  "Coca-Cola 2L",               "Coca-Cola",       220,"bottle","Z11"),
    ("Beverages",  "Coca-Cola 500ml",            "Coca-Cola",        70,"bottle","Z11"),
    ("Beverages",  "Sprite 2L",                  "Coca-Cola",       210,"bottle","Z11"),
    ("Beverages",  "Fanta 2L",                   "Coca-Cola",       210,"bottle","Z11"),
    ("Beverages",  "Pepsi 2L",                   "Pepsico",         210,"bottle","Z11"),
    ("Beverages",  "Mountain Dew 2L",            "Pepsico",         210,"bottle","Z11"),
    ("Beverages",  "Real Mixed Fruit Juice 1L",  "Dabur",           220,"pack","Z11"),
    ("Beverages",  "Real Mango Juice 1L",        "Dabur",           220,"pack","Z11"),
    ("Beverages",  "Frooti Mango 200ml",         "Parle",            25,"pack","Z11"),
    ("Beverages",  "Bisleri Water 1L",           "Bisleri",          30,"bottle","Z11"),
    ("Beverages",  "Himalayan Spring Water 20L", "Himalayan",       250,"jar","Z11"),
    ("Beverages",  "Red Bull 250ml",             "Red Bull",        165,"can","Z11"),
    # --- Z12 Tea & coffee ---
    ("Tea/Coffee", "Nepal Tea Premium 500g",     "Nepal Tea",       525,"pack","Z12"),
    ("Tea/Coffee", "Tokla CTC Tea 500g",         "Tokla",           440,"pack","Z12"),
    ("Tea/Coffee", "Red Label Tea 1kg",          "Brooke Bond",     650,"pack","Z12"),
    ("Tea/Coffee", "Nescafe Classic 100g Jar",   "Nescafe",         525,"jar","Z12"),
    ("Tea/Coffee", "Nescafe Gold 95g",           "Nescafe",         985,"jar","Z12"),
    ("Tea/Coffee", "Bru Coffee 100g",            "Bru",             340,"pack","Z12"),
    ("Tea/Coffee", "Horlicks 500g",              "GSK",             465,"jar","Z12"),
    ("Tea/Coffee", "Bournvita 500g",             "Cadbury",         385,"jar","Z12"),
    # --- Z13 Personal care ---
    ("Personal",   "Himalaya Face Wash Neem",    "Himalaya",        199,"tube","Z13"),
    ("Personal",   "Pond's Cold Cream 100g",     "Ponds",           225,"jar","Z13"),
    ("Personal",   "Nivea Soft Moisturizer 100g","Nivea",           320,"tub","Z13"),
    ("Personal",   "Dabur Amla Hair Oil 200ml",  "Dabur",           285,"bottle","Z13"),
    ("Personal",   "Parachute Coconut Oil 500ml","Parachute",       420,"bottle","Z13"),
    ("Personal",   "Head & Shoulders Shampoo 340ml","P&G",          485,"bottle","Z13"),
    ("Personal",   "Sunsilk Shampoo 180ml",      "HUL",             185,"bottle","Z13"),
    ("Personal",   "Dove Soap (4-pack)",         "HUL",             295,"pack","Z13"),
    ("Personal",   "Lifebuoy Soap (4-pack)",     "HUL",             165,"pack","Z13"),
    ("Personal",   "Lux Soap (4-pack)",          "HUL",             225,"pack","Z13"),
    ("Personal",   "Colgate MaxFresh Toothpaste 150g","Colgate",     185,"tube","Z13"),
    ("Personal",   "Sensodyne Toothpaste 75g",   "GSK",             245,"tube","Z13"),
    ("Personal",   "Oral-B Toothbrush",          "Oral-B",          120,"pc","Z13"),
    ("Personal",   "Gillette Mach 3 Razor",      "Gillette",        425,"pc","Z13"),
    ("Personal",   "Nivea Deodorant 150ml",      "Nivea",           385,"can","Z13"),
    ("Personal",   "Whisper Sanitary Pads (Pack of 14)","P&G",       265,"pack","Z13"),
    # --- Z14 Household ---
    ("Household",  "Surf Excel Detergent 1kg",   "HUL",             345,"pack","Z14"),
    ("Household",  "Ariel Detergent 1kg",        "P&G",             385,"pack","Z14"),
    ("Household",  "Tide Detergent 1kg",         "P&G",             265,"pack","Z14"),
    ("Household",  "Vim Liquid Dishwash 500ml",  "HUL",             185,"bottle","Z14"),
    ("Household",  "Pril Dishwash Bar 4pc",      "Henkel",          155,"pack","Z14"),
    ("Household",  "Harpic Toilet Cleaner 1L",   "Reckitt",         245,"bottle","Z14"),
    ("Household",  "Lizol Floor Cleaner 1L",     "Reckitt",         265,"bottle","Z14"),
    ("Household",  "Odonil Air Freshener",       "Dabur",           135,"pc","Z14"),
    ("Household",  "Hit Mosquito Spray",         "Godrej",          265,"can","Z14"),
    ("Household",  "Toilet Paper (4-roll)",      "Origami",         195,"pack","Z14"),
    ("Household",  "Tissue Box 200-pull",        "Origami",         165,"box","Z14"),
    ("Household",  "Garbage Bags (50pc)",        "Generic",         185,"pack","Z14"),
    ("Household",  "Aluminium Foil 9m",          "Freshwrapp",      285,"roll","Z14"),
    ("Household",  "Cling Film 30m",             "Freshwrapp",      165,"roll","Z14"),
    # --- Z15 Baby ---
    ("Baby",       "Pampers Premium Care Pants L","Pampers",       1299,"pack","Z15"),
    ("Baby",       "Huggies Diapers M (44pc)",   "Huggies",         985,"pack","Z15"),
    ("Baby",       "Cerelac Wheat Apple Cherry", "Nestle",          425,"pack","Z15"),
    ("Baby",       "Lactogen Formula 400g",      "Nestle",          885,"tin","Z15"),
    ("Baby",       "Johnson's Baby Shampoo 200ml","Johnson",         265,"bottle","Z15"),
    ("Baby",       "Johnson's Baby Powder 200g", "Johnson",         245,"tin","Z15"),
    # --- Z16 Stationery & misc ---
    ("Stationery", "Classmate Notebook 200pg",   "Classmate",       145,"pc","Z16"),
    ("Stationery", "Apsara Pencils (10pk)",      "Apsara",           85,"pack","Z16"),
    ("Stationery", "Reynolds Ballpoint Pen",     "Reynolds",         15,"pc","Z16"),
    ("Stationery", "A4 Photocopy Paper Ream",    "JK",              485,"ream","Z16"),
    ("Stationery", "Faber-Castell Sketch Pens",  "Faber-Castell",   320,"pack","Z16"),
    ("Stationery", "Cello Tape Roll",            "Cello",            45,"pc","Z16"),
]

# Build the products dataframe — replicate seed across stores so each
# store has its own copy of the SKU with its own shelf coordinates.
product_rows = []
prod_counter = 1
for store_id in stores_df["store_id"]:
    # Each store carries 80–95% of the master SKUs, with slight price variance.
    chosen = random.sample(PRODUCT_SEED, k=int(len(PRODUCT_SEED) * random.uniform(0.82, 0.95)))
    for (subcat, name, brand, price, unit, zone_id) in chosen:
        # Pick a random aisle in the matching zone of this store.
        candidate_aisles = aisles_df[(aisles_df.store_id == store_id) & (aisles_df.zone_id == zone_id)]
        aisle_id = candidate_aisles.sample(1, random_state=prod_counter).iloc[0]["aisle_id"]
        shelf_number = random.randint(1, 6)            # 6 shelves per aisle
        shelf_position = random.randint(1, 12)         # 12 facing positions
        # ±5% store-level price variation
        local_price = int(round(price * random.uniform(0.95, 1.05)))
        product_id = f"P{prod_counter:06d}"
        sku = f"SKU-{abs(hash(name)) % 10**8:08d}"
        product_rows.append((
            product_id, sku, name, brand, subcat, zone_id, aisle_id,
            shelf_number, shelf_position, store_id, unit, local_price,
        ))
        prod_counter += 1

products_df = pd.DataFrame(product_rows, columns=[
    "product_id", "sku", "product_name", "brand", "subcategory",
    "zone_id", "aisle_id", "shelf_number", "shelf_position", "store_id",
    "unit", "price_npr",
])
print(f"Products: {len(products_df):,} (across {len(stores_df)} stores)")

# ---------------------------------------------------------------------------
# 4. Customers
# ---------------------------------------------------------------------------
N_CUSTOMERS = 25_000
LOYALTY_TIERS = ["None", "Silver", "Gold", "Platinum"]
LOYALTY_WEIGHTS = [0.55, 0.25, 0.15, 0.05]
GENDERS = ["F", "M", "Other"]
GENDER_WEIGHTS = [0.55, 0.43, 0.02]
AGE_BUCKETS = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
AGE_WEIGHTS  = [0.12, 0.32, 0.28, 0.16, 0.08, 0.04]
HOME_AREAS = stores_df["area"].tolist() + ["Boudha","Koteshwor","Kalanki","Kirtipur","Kupondole"]

cust_ids = [f"C{ i :07d}".replace(" ","") for i in range(1, N_CUSTOMERS + 1)]
customers_df = pd.DataFrame({
    "customer_id":   cust_ids,
    "loyalty_tier":  np.random.choice(LOYALTY_TIERS, N_CUSTOMERS, p=LOYALTY_WEIGHTS),
    "gender":        np.random.choice(GENDERS, N_CUSTOMERS, p=GENDER_WEIGHTS),
    "age_bucket":    np.random.choice(AGE_BUCKETS, N_CUSTOMERS, p=AGE_WEIGHTS),
    "home_area":     np.random.choice(HOME_AREAS, N_CUSTOMERS),
    "registered_on": [(datetime(2022, 1, 1) + timedelta(days=int(np.random.randint(0, 1200)))).date()
                       for _ in range(N_CUSTOMERS)],
    "uses_app":      np.random.random(N_CUSTOMERS) < 0.62,   # 62% use the smart-shopping app
})
print(f"Customers: {len(customers_df):,}")

# ---------------------------------------------------------------------------
# 5. Transactions (100,000)
# ---------------------------------------------------------------------------
N_TRANSACTIONS = 50_000

# Per-customer visit propensity — heavy-tailed: a few customers come often.
visit_lambda = np.random.gamma(shape=1.4, scale=1.2, size=N_CUSTOMERS) + 0.3
# Loyalty boost
tier_boost = customers_df["loyalty_tier"].map({"None":1.0,"Silver":1.5,"Gold":2.2,"Platinum":3.0}).to_numpy()
visit_lambda = visit_lambda * tier_boost
visit_p = visit_lambda / visit_lambda.sum()

cust_choice = np.random.choice(N_CUSTOMERS, size=N_TRANSACTIONS, p=visit_p)

# Build transaction timestamps with realistic patterns.
# Date range: Jan 1 2024 → Mar 31 2026 (~821 days)
START = datetime(2024, 1, 1)
DAYS = 821
DOW_WEIGHTS = np.array([0.12, 0.10, 0.10, 0.11, 0.13, 0.22, 0.22])  # Mon..Sun
HOUR_W = np.array([0,0,0,0,0,0, 0.1,0.4,0.7,1.0,1.2,1.5,
                   1.4,1.3,1.2,1.4, 2.2,3.0,3.2,2.8,1.8, 0.8,0.4,0.1])
HOUR_W = HOUR_W / HOUR_W.sum()

def sample_timestamps_batch(n: int) -> list:
    all_dates = [START + timedelta(days=int(i)) for i in range(DAYS)]
    day_w = np.array([DOW_WEIGHTS[d.weekday()] for d in all_dates])
    day_w = day_w / day_w.sum()
    chosen_days = np.random.choice(DAYS, size=n, p=day_w)
    chosen_hours = np.random.choice(24, size=n, p=HOUR_W)
    chosen_mins = np.random.randint(0, 60, size=n)
    chosen_secs = np.random.randint(0, 60, size=n)
    return [(START + timedelta(days=int(d))).replace(
                hour=int(h), minute=int(m), second=int(s))
            for d, h, m, s in zip(chosen_days, chosen_hours, chosen_mins, chosen_secs)]

print("Sampling transaction timestamps...")
timestamps = sample_timestamps_batch(N_TRANSACTIONS)

# Festival surge: bump basket sizes around Dashain (Oct 9-15 each year),
# Tihar (early Nov), and New Year (mid-April Nepali New Year).
def is_festival(ts: datetime) -> bool:
    month_day = (ts.month, ts.day)
    return (
        (ts.month == 10 and 5 <= ts.day <= 16) or         # Dashain window
        (ts.month == 11 and 1 <= ts.day <= 7) or          # Tihar window
        (ts.month == 4 and 10 <= ts.day <= 16)            # Nepali New Year
    )

# Store choice: customer-anchored. Customer's home area maps to their
# nearest store (heuristic: same area or weighted overall).
home_to_store = dict(zip(stores_df["area"], stores_df["store_id"]))
store_ids_array = stores_df["store_id"].to_numpy()
store_weights = np.array([STORE_TRAFFIC_WEIGHT[s] for s in store_ids_array])
store_p = store_weights / store_weights.sum()

def pick_store_for_customer(customer_idx: int) -> str:
    home = cust_home_arr[customer_idx]              # numpy lookup, fast
    if home in home_to_store and np.random.random() < 0.65:
        return home_to_store[home]
    return str(np.random.choice(store_ids_array, p=store_p))

# Basket size: mixture of three regimes
def sample_basket_size(festival: bool) -> int:
    r = np.random.random()
    if festival:
        # Festivals shift toward bigger baskets
        if r < 0.05: return int(np.random.randint(1, 3))     # quick stop
        if r < 0.30: return int(np.random.randint(5, 13))    # regular
        if r < 0.85: return int(np.random.randint(15, 35))   # big shop
        return int(np.random.randint(35, 65))                # festival haul
    if r < 0.18: return int(np.random.randint(1, 4))
    if r < 0.65: return int(np.random.randint(4, 12))
    if r < 0.93: return int(np.random.randint(12, 30))
    return int(np.random.randint(30, 50))

# ---------------------------------------------------------------------------
# 6. Co-occurrence affinity for realistic baskets
# ---------------------------------------------------------------------------
# Soft "themes" — when a customer puts one of these in basket, others from
# the same theme are slightly more likely to follow.
THEMES = {
    "breakfast":  {"Sliced Bread 400g","Eggs (Pack of 6)","Amul Butter 500g","Nescafe Classic 100g Jar",
                   "DDC Milk 1L","Horlicks 500g","Bournvita 500g"},
    "tea_time":   {"Nepal Tea Premium 500g","Tokla CTC Tea 500g","DDC Milk 500ml","Marie Gold Biscuit",
                   "Coconut Crunchies Biscuit","Sugar 1kg"},
    "wai_wai":    {"Wai Wai Chicken (Pack of 30)","Wai Wai Veg (Pack of 30)","Wai Wai Single Pack",
                   "RaRa Noodles Single Pack","2PM Chicken Noodles","Maggi 2-Min 70g"},
    "meat_meal":  {"Chicken Breast (Boneless) 1kg","Whole Chicken 1.2kg","Onion (Pyaj) per kg",
                   "Tomato per kg","Garlic (Lasun) per kg","Ginger (Aduwa) per kg",
                   "Turmeric Powder 200g","Garam Masala 100g","Mustard Oil 1L"},
    "veg_meal":   {"Potato (Aalu) per kg","Onion (Pyaj) per kg","Cauliflower per kg",
                   "Spinach (Palungo) bundle","Tomato per kg","Cumin Seeds 100g","Coriander Powder 200g"},
    "kids":       {"Pampers Premium Care Pants L","Cerelac Wheat Apple Cherry","Lactogen Formula 400g",
                   "Johnson's Baby Shampoo 200ml","Frooti Mango 200ml","Oreo Vanilla 120g"},
    "cleaning":   {"Surf Excel Detergent 1kg","Vim Liquid Dishwash 500ml","Harpic Toilet Cleaner 1L",
                   "Lizol Floor Cleaner 1L","Toilet Paper (4-roll)","Tissue Box 200-pull"},
    "snacking":   {"Lays Magic Masala 50g","Kurkure Masala Munch","Coca-Cola 2L","Sprite 2L",
                   "Mountain Dew 2L","Dairy Milk 50g","KitKat 4-Finger"},
    "festival":   {"Basmati Rice 5kg (Premium)","Ghee 500ml","Buffalo Ghee 1L","Mutton (Khasi) 1kg",
                   "Cardamom 100g","Pure Cow Ghee 500ml"},
}
# Pre-index products by name across all stores
products_by_name = defaultdict(list)
for _, row in products_df.iterrows():
    products_by_name[row["product_name"]].append((row["product_id"], row["store_id"], row["price_npr"]))

# For sampling within a store quickly, pre-build per-store product NUMPY arrays
# (keyed by store_id, all aligned: ids/skus/names/zones/aisles/prices/subcats)
products_by_store_np: dict[str, dict] = {}
for s in stores_df["store_id"]:
    sub = products_df[products_df.store_id == s].reset_index(drop=True)
    products_by_store_np[s] = {
        "product_id":   sub["product_id"].to_numpy(),
        "sku":          sub["sku"].to_numpy(),
        "product_name": sub["product_name"].to_numpy(),
        "zone_id":      sub["zone_id"].to_numpy(),
        "aisle_id":     sub["aisle_id"].to_numpy(),
        "price_npr":    sub["price_npr"].to_numpy(),
        "subcategory":  sub["subcategory"].to_numpy(),
    }

# Sampling weights inside a store: bias toward staples + commonly-bought stuff
def basket_sampling_weights(subcat_arr: np.ndarray) -> np.ndarray:
    base = np.ones(len(subcat_arr))
    high = {"Staples","Vegetables","Dairy","Bakery","Snacks","Beverages","Personal","Household"}
    base[np.isin(subcat_arr, list(high))] *= 2.5
    base[np.isin(subcat_arr, ["Spices","Sauces","Tea/Coffee"])] *= 1.6
    return base / base.sum()

store_sampling_weights = {s: basket_sampling_weights(d["subcategory"])
                          for s, d in products_by_store_np.items()}

# Customer-level numpy arrays for fast lookup in the hot loop
cust_id_arr        = customers_df["customer_id"].to_numpy()
cust_uses_app_arr  = customers_df["uses_app"].to_numpy()
cust_loyalty_arr   = customers_df["loyalty_tier"].to_numpy()
cust_home_arr      = customers_df["home_area"].to_numpy()

# Pre-compute name→theme membership for fast affinity boost
name_to_themes: dict[str, list] = defaultdict(list)
for theme, items in THEMES.items():
    for it in items:
        name_to_themes[it].append(theme)

PAYMENT_METHODS = ["Cash","eSewa","Khalti","IME Pay","FonePay","ConnectIPS","Card"]
APP_PAYMENT_METHODS = ["eSewa","Khalti","IME Pay","FonePay","Card"]   # only digital via app
PAY_WEIGHTS = np.array([0.30,0.22,0.16,0.08,0.10,0.04,0.10])
PAY_WEIGHTS = PAY_WEIGHTS / PAY_WEIGHTS.sum()

SCAN_METHODS = ["barcode","qr_code","manual_entry"]
SCAN_METHOD_WEIGHTS = np.array([0.78, 0.16, 0.06])

# ---------------------------------------------------------------------------
# 7. Generate transactions, line items, navigation events, payment events
# ---------------------------------------------------------------------------
print("Generating 100,000 transactions...")

txn_rows = []
item_rows = []
app_event_rows = []
payment_rows = []

txn_counter = 1
item_counter = 1
event_counter = 1
pay_counter = 1

for i in range(N_TRANSACTIONS):
    if i and i % 10000 == 0:
        print(f"  ... {i:,} done")

    customer_idx = int(cust_choice[i])
    customer_id = cust_id_arr[customer_idx]
    uses_app = bool(cust_uses_app_arr[customer_idx])
    loyalty_tier = cust_loyalty_arr[customer_idx]
    store_id = pick_store_for_customer(customer_idx)
    entry_ts = timestamps[i]
    festival = is_festival(entry_ts)

    basket_n = sample_basket_size(festival)

    sd = products_by_store_np[store_id]
    weights = store_sampling_weights[store_id]
    n_prods = len(sd["product_id"])

    # Sample initial seed items (vectorized)
    seed_count = max(1, int(basket_n * 0.4))
    if seed_count > n_prods:
        seed_count = n_prods
    seed_idx = np.random.choice(n_prods, size=seed_count, replace=False, p=weights)
    chosen_set = set(seed_idx.tolist())

    # Theme-affinity boost
    seed_names = sd["product_name"][seed_idx]
    triggered_themes = set()
    for name in seed_names:
        themes_for_name = name_to_themes.get(name)
        if themes_for_name:
            for th in themes_for_name:
                if np.random.random() < 0.55:
                    triggered_themes.add(th)
    if triggered_themes:
        themed_names_set = set().union(*[THEMES[t] for t in triggered_themes])
        themed_mask = np.isin(sd["product_name"], list(themed_names_set))
        themed_idx = np.where(themed_mask)[0]
        if len(themed_idx) > 0:
            extra_n = max(0, basket_n - len(chosen_set))
            if extra_n > 0:
                pick = np.random.choice(themed_idx,
                                         size=min(extra_n, len(themed_idx)), replace=False)
                chosen_set.update(pick.tolist())

    # Top up to basket_n with random picks
    while len(chosen_set) < basket_n and len(chosen_set) < n_prods:
        idx = int(np.random.choice(n_prods, p=weights))
        chosen_set.add(idx)
    chosen_arr = np.fromiter(chosen_set, dtype=np.int64)[:basket_n]
    bn = len(chosen_arr)

    # Vectorized line-item arrays for this transaction
    pids   = sd["product_id"][chosen_arr]
    skus   = sd["sku"][chosen_arr]
    pnames = sd["product_name"][chosen_arr]
    zones  = sd["zone_id"][chosen_arr]
    aisles_arr_t = sd["aisle_id"][chosen_arr]
    prices = sd["price_npr"][chosen_arr]

    qtys = np.where(np.random.random(bn) < 0.18,
                    np.random.randint(2, 5, size=bn), 1)
    line_totals = prices * qtys
    item_subtotal = int(line_totals.sum())

    # Total dwell time
    dwell_min = max(2.0, 4 + 0.7 * basket_n + float(np.random.normal(0, 4)))
    exit_ts = entry_ts + timedelta(minutes=dwell_min)

    # Payment method
    if uses_app and np.random.random() < 0.75:
        pay_method = APP_PAYMENT_METHODS[int(np.random.randint(len(APP_PAYMENT_METHODS)))]
    else:
        pay_method = str(np.random.choice(PAYMENT_METHODS, p=PAY_WEIGHTS))
    scan_to_pay_used = uses_app and pay_method != "Cash"

    # Scan timestamps (vectorized): sorted offsets from entry
    scan_offsets = np.sort(np.random.uniform(2, max(3, dwell_min - 1), size=bn))
    if scan_to_pay_used:
        scan_methods_arr = np.random.choice(SCAN_METHODS, size=bn, p=SCAN_METHOD_WEIGHTS)
        scan_durs = np.maximum(400, np.random.normal(1600, 700, size=bn)).astype(int)
        rescans_arr = np.random.choice([0, 1, 2], size=bn, p=[0.92, 0.07, 0.01])
        success_arr = (rescans_arr <= 2) & (np.random.random(bn) < 0.985)
    else:
        scan_methods_arr = np.full(bn, "checkout_pos", dtype=object)
        scan_durs = np.maximum(300, np.random.normal(900, 250, size=bn)).astype(int)
        rescans_arr = np.zeros(bn, dtype=int)
        success_arr = np.ones(bn, dtype=bool)

    txn_id = f"T{txn_counter:08d}"

    # Build all line-item scan timestamps as a list at once
    if scan_to_pay_used:
        scan_ts_list = [entry_ts + timedelta(minutes=float(o)) for o in scan_offsets]
    else:
        offs = np.random.uniform(30, 180, size=bn)
        scan_ts_list = [exit_ts - timedelta(seconds=float(s)) for s in offs]

    # Vectorized line-item row construction via zip
    line_ids = [f"L{item_counter + j:09d}" for j in range(bn)]
    item_counter += bn
    item_rows.extend(zip(
        line_ids,
        [txn_id] * bn,
        pids.tolist(), skus.tolist(), pnames.tolist(),
        zones.tolist(), aisles_arr_t.tolist(),
        qtys.tolist(), prices.tolist(), line_totals.tolist(),
        scan_ts_list,
        scan_methods_arr.tolist(),
        scan_durs.tolist(),
        rescans_arr.tolist(),
        success_arr.tolist(),
    ))

    # Discount + VAT + grand total
    discount_rate = 0.0
    if loyalty_tier == "Silver":   discount_rate += 0.02
    if loyalty_tier == "Gold":     discount_rate += 0.04
    if loyalty_tier == "Platinum": discount_rate += 0.07
    if festival:                   discount_rate += 0.03
    discount_amt = int(round(item_subtotal * discount_rate))
    total_after = item_subtotal - discount_amt
    vat = int(round(total_after * 0.13))
    grand_total = total_after + vat

    # Payment events
    attempts = 1
    if pay_method != "Cash" and np.random.random() < 0.06:
        attempts = int(np.random.choice([2, 3], p=[0.85, 0.15]))
    final_status = "success"
    if attempts > 1 and np.random.random() < 0.04:
        final_status = "failed"
    for k in range(attempts):
        is_last = (k == attempts - 1)
        latency_ms = int(max(120, np.random.normal(1400, 600)))
        if is_last:
            status = final_status
        else:
            status = "retry"
        payment_rows.append((
            f"PE{pay_counter:09d}", txn_id, k + 1, pay_method,
            (entry_ts + timedelta(minutes=dwell_min - 0.5 + 0.1 * k)),
            latency_ms, status, grand_total if status == "success" else 0,
        ))
        pay_counter += 1

    # App / navigation events
    aisles_visited = int(len(np.unique(aisles_arr_t)))
    n_searches = 0
    n_directions = 0
    if uses_app:
        n_searches = int(np.random.poisson(min(8, max(1, basket_n * 0.25))))
        n_directions = int(np.random.poisson(min(6, max(0, basket_n * 0.15))))
        if n_searches > 0:
            k = min(n_searches, bn)
            sample_pos = np.random.choice(bn, size=k, replace=False)
            for sp in sample_pos:
                ev_ts = entry_ts + timedelta(minutes=float(np.random.uniform(0, dwell_min - 1)))
                app_event_rows.append((
                    f"E{event_counter:09d}", txn_id, customer_id, store_id,
                    ev_ts,
                    "search_query", pnames[sp], None,
                ))
                event_counter += 1
        if n_directions > 0:
            k = min(n_directions, bn)
            sample_pos = np.random.choice(bn, size=k, replace=False)
            for sp in sample_pos:
                ev_ts = entry_ts + timedelta(minutes=float(np.random.uniform(0, dwell_min - 1)))
                app_event_rows.append((
                    f"E{event_counter:09d}", txn_id, customer_id, store_id,
                    ev_ts,
                    "directions_request", None, aisles_arr_t[sp],
                ))
                event_counter += 1

    txn_rows.append((
        txn_id, customer_id, store_id, entry_ts,
        exit_ts, round(dwell_min, 2),
        bn, int(qtys.sum()), aisles_visited,
        n_searches, n_directions,
        item_subtotal, discount_amt, total_after, vat, grand_total,
        pay_method, scan_to_pay_used, attempts, final_status,
        loyalty_tier, festival,
    ))
    txn_counter += 1

print(f"Transactions: {len(txn_rows):,}")
print(f"Line items:   {len(item_rows):,}")
print(f"App events:   {len(app_event_rows):,}")
print(f"Pay events:   {len(payment_rows):,}")

# ---------------------------------------------------------------------------
# 8. Write everything to CSVs
# ---------------------------------------------------------------------------
print("Writing CSV files...")

stores_df.to_csv(DATA / "stores.csv", index=False)
zones_df.to_csv(DATA / "zones.csv", index=False)
aisles_df.to_csv(DATA / "aisles.csv", index=False)
products_df.to_csv(DATA / "products.csv", index=False)
customers_df.to_csv(DATA / "customers.csv", index=False)

# Build dataframes and batch-format the datetime columns
TXN_DT_COLS = ["entry_timestamp", "exit_timestamp"]
txn_df = pd.DataFrame(txn_rows, columns=[
    "transaction_id","customer_id","store_id","entry_timestamp","exit_timestamp","dwell_minutes",
    "num_distinct_items","num_total_units","aisles_visited",
    "n_app_searches","n_app_directions",
    "subtotal_npr","discount_npr","total_after_discount_npr","vat_13pct_npr","grand_total_npr",
    "payment_method","scan_to_pay_used","payment_attempts","payment_status",
    "customer_loyalty_tier","is_festival_period",
])
for c in TXN_DT_COLS:
    txn_df[c] = pd.to_datetime(txn_df[c]).dt.strftime("%Y-%m-%d %H:%M:%S")
txn_df.to_csv(DATA / "transactions.csv", index=False)

item_df = pd.DataFrame(item_rows, columns=[
    "line_item_id","transaction_id","product_id","sku","product_name",
    "zone_id","aisle_id","quantity","unit_price_npr","line_total_npr",
    "scan_timestamp","scan_method","scan_duration_ms","rescans","scan_success",
])
item_df["scan_timestamp"] = pd.to_datetime(item_df["scan_timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
item_df.to_csv(DATA / "transaction_items.csv", index=False)

app_df = pd.DataFrame(app_event_rows, columns=[
    "event_id","transaction_id","customer_id","store_id","event_timestamp",
    "event_type","search_query","target_aisle_id",
])
app_df["event_timestamp"] = pd.to_datetime(app_df["event_timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
app_df.to_csv(DATA / "app_events.csv", index=False)

pay_df = pd.DataFrame(payment_rows, columns=[
    "payment_event_id","transaction_id","attempt_number","payment_method",
    "attempt_timestamp","latency_ms","status","amount_npr",
])
pay_df["attempt_timestamp"] = pd.to_datetime(pay_df["attempt_timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
pay_df.to_csv(DATA / "payment_events.csv", index=False)

print("All CSVs written.")
