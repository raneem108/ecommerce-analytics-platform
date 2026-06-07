import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# ── Load credentials from .env ────────────────────────────────
# This reads your .env file and makes the variables available
# via os.getenv(). Your password never appears in this code.
load_dotenv()

DB_URL = os.getenv("DB_URL")

if not DB_URL:
    raise ValueError("DB_URL not found in .env file. Check your .env")

# ── Create database engine ────────────────────────────────────
# The engine is the connection manager. It handles opening and
# closing connections automatically. We use it as a context
# manager (with statement) so connections are always cleaned up.
print("Connecting to Supabase...")
engine = create_engine(DB_URL)

# ── Test the connection first ─────────────────────────────────
try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"Connected successfully!")
        print(f"PostgreSQL version: {version[:50]}")
except Exception as e:
    print(f"Connection failed: {e}")
    print("Check your DB_URL in .env file")
    exit(1)

# ── Load CSVs into DataFrames ─────────────────────────────────
print("\nLoading CSV files...")
customers   = pd.read_csv("data/raw/customers.csv")
products    = pd.read_csv("data/raw/products.csv")
orders      = pd.read_csv("data/raw/orders.csv")
order_items = pd.read_csv("data/raw/order_items.csv")

print(f"  customers:   {len(customers):,} rows")
print(f"  products:    {len(products):,} rows")
print(f"  orders:      {len(orders):,} rows")
print(f"  order_items: {len(order_items):,} rows")

# ── Upload to PostgreSQL ──────────────────────────────────────
# if_exists="replace" means: if the table already exists,
# drop it and recreate it. Safe for initial load.
# index=False means don't write the pandas row index as a column.
print("\nUploading to Supabase...")

customers.to_sql(
    "customers", engine,
    if_exists="replace", index=False
)
print("  ✓ customers uploaded")

products.to_sql(
    "products", engine,
    if_exists="replace", index=False
)
print("  ✓ products uploaded")

orders.to_sql(
    "orders", engine,
    if_exists="replace", index=False
)
print("  ✓ orders uploaded")

order_items.to_sql(
    "order_items", engine,
    if_exists="replace", index=False
)
print("  ✓ order_items uploaded")

# ── Verify the upload ─────────────────────────────────────────
print("\nVerifying row counts in database...")
with engine.connect() as conn:
    for table in ["customers", "products", "orders", "order_items"]:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
        print(f"  {table}: {count:,} rows in database")

print("\n✅ All data loaded successfully into Supabase!")
print("You can now view your tables in the Supabase dashboard.")