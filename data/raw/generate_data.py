import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# ── Configuration ─────────────────────────────────────────────
random.seed(42)
np.random.seed(42)

NUM_CUSTOMERS = 1000
NUM_PRODUCTS  = 50
NUM_ORDERS    = 5000
START_DATE    = datetime(2023, 1, 1)
END_DATE      = datetime(2024, 12, 31)

# ── Helpers ───────────────────────────────────────────────────
def random_date(start, end):
    """Return a random datetime between start and end."""
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)

# ── 1. CUSTOMERS ──────────────────────────────────────────────
# We create customer segments because real businesses
# always segment customers — it makes analytics meaningful.
segments = ["Premium", "Regular", "Occasional", "At-Risk"]
segment_weights = [0.15, 0.40, 0.30, 0.15]  # most are Regular

countries = ["Jordan", "Saudi Arabia", "UAE", "Egypt", "Kuwait"]
country_weights = [0.40, 0.25, 0.15, 0.12, 0.08]

customers = pd.DataFrame({
    "customer_id": range(1, NUM_CUSTOMERS + 1),
    "name": [f"Customer_{i}" for i in range(1, NUM_CUSTOMERS + 1)],
    "email": [f"customer_{i}@email.com" for i in range(1, NUM_CUSTOMERS + 1)],
    "country": np.random.choice(countries, NUM_CUSTOMERS, p=country_weights),
    "segment": np.random.choice(segments, NUM_CUSTOMERS, p=segment_weights),
    "signup_date": [random_date(START_DATE, END_DATE).date()
                    for _ in range(NUM_CUSTOMERS)],
    "age": np.random.randint(18, 65, NUM_CUSTOMERS),
})

# ── 2. PRODUCTS ───────────────────────────────────────────────
categories = ["Electronics", "Clothing", "Home & Garden",
              "Sports", "Books", "Beauty"]

product_names = {
    "Electronics": ["Laptop", "Phone", "Tablet", "Headphones",
                    "Smartwatch", "Camera", "Speaker", "Charger"],
    "Clothing":    ["T-Shirt", "Jeans", "Jacket", "Dress",
                    "Shoes", "Hoodie", "Shorts", "Scarf"],
    "Home & Garden":["Lamp", "Pillow", "Vase", "Plant Pot",
                     "Curtains", "Rug", "Mirror", "Clock"],
    "Sports":      ["Yoga Mat", "Dumbbells", "Running Shoes",
                    "Water Bottle", "Resistance Bands", "Jump Rope"],
    "Books":       ["Fiction Novel", "Self Help", "Biography",
                    "Cookbook", "Science Book", "History Book"],
    "Beauty":      ["Moisturizer", "Lipstick", "Perfume",
                    "Shampoo", "Face Mask", "Sunscreen"],
}

# Price ranges by category — electronics cost more than books
price_ranges = {
    "Electronics":   (50,  800),
    "Clothing":      (15,  120),
    "Home & Garden": (10,  150),
    "Sports":        (10,  200),
    "Books":         (5,   40),
    "Beauty":        (8,   80),
}

product_list = []
pid = 1
for category in categories:
    for name in product_names[category]:
        low, high = price_ranges[category]
        price = round(random.uniform(low, high), 2)
        product_list.append({
            "product_id":   pid,
            "name":         name,
            "category":     category,
            "price":        price,
            # cost is 40-70% of selling price — this is gross margin
            "cost":         round(price * random.uniform(0.4, 0.7), 2),
            "stock":        random.randint(10, 500),
        })
        pid += 1

products = pd.DataFrame(product_list)

# ── 3. ORDERS ─────────────────────────────────────────────────
# Premium customers order more often, At-Risk customers less
segment_order_prob = {
    "Premium":    0.35,   # 35% of orders come from 15% of customers
    "Regular":    0.45,
    "Occasional": 0.15,
    "At-Risk":    0.05,
}

statuses = ["completed", "completed", "completed",
            "returned", "cancelled"]  # 60% complete, 20% each other

orders = pd.DataFrame({
    "order_id":   range(1, NUM_ORDERS + 1),
    "customer_id": np.random.choice(
        customers["customer_id"], NUM_ORDERS,
        # weight orders toward premium customers
        p=None
    ),
    "order_date": [random_date(START_DATE, END_DATE).date()
                   for _ in range(NUM_ORDERS)],
    "status": [random.choice(statuses) for _ in range(NUM_ORDERS)],
    "shipping_country": np.random.choice(
        countries, NUM_ORDERS, p=country_weights
    ),
})

# ── 4. ORDER ITEMS ────────────────────────────────────────────
# Each order has 1-4 items — realistic for e-commerce
order_items = []
item_id = 1
for _, order in orders.iterrows():
    num_items = random.randint(1, 4)
    # pick random products without replacement per order
    selected = products.sample(n=num_items)
    for _, product in selected.iterrows():
        quantity = random.randint(1, 3)
        order_items.append({
            "item_id":    item_id,
            "order_id":   order["order_id"],
            "product_id": product["product_id"],
            "quantity":   quantity,
            "unit_price": product["price"],
            # total revenue for this line item
            "subtotal":   round(quantity * product["price"], 2),
        })
        item_id += 1

order_items = pd.DataFrame(order_items)

# ── 5. SAVE TO CSV ────────────────────────────────────────────
os.makedirs("data/raw", exist_ok=True)

customers.to_csv("data/raw/customers.csv",   index=False)
products.to_csv("data/raw/products.csv",     index=False)
orders.to_csv("data/raw/orders.csv",         index=False)
order_items.to_csv("data/raw/order_items.csv", index=False)

print(" Dataset generated successfully")
print(f"   Customers:   {len(customers):,}")
print(f"   Products:    {len(products):,}")
print(f"   Orders:      {len(orders):,}")
print(f"   Order items: {len(order_items):,}")

# ── 6. QUICK SANITY CHECK ─────────────────────────────────────
total_revenue = order_items["subtotal"].sum()
print(f"\n Total revenue in dataset: ${total_revenue:,.2f}")
print(f"   Average order value: ${order_items.groupby('order_id')['subtotal'].sum().mean():,.2f}")
print(f"   Date range: {orders['order_date'].min()} → {orders['order_date'].max()}")