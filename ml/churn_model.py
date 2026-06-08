import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.preprocessing import LabelEncoder
import os

# ── Load environment and connect ──────────────────────────────
load_dotenv()
engine = create_engine(os.getenv("DB_URL"))

# ── Extract features from database ───────────────────────────
# This query builds one row per customer with all the
# features our model needs to predict churn.
# This is called "feature engineering" — transforming
# raw data into meaningful inputs for the model.
query = """
SELECT 
    c.customer_id,
    c.segment,
    c.country,
    c.age,
    COUNT(DISTINCT o.order_id)                  AS total_orders,
    ROUND(SUM(oi.subtotal)::numeric, 2)         AS total_spent,
    ROUND(AVG(oi.subtotal)::numeric, 2)         AS avg_order_value,
    MAX(o.order_date::date)                     AS last_order_date,
    MIN(o.order_date::date)                     AS first_order_date,
    ('2024-12-31'::date - MAX(o.order_date::date)) AS days_since_last_order,
    -- TARGET VARIABLE: 1 = churned, 0 = active
    CASE 
        WHEN ('2024-12-31'::date - MAX(o.order_date::date)) > 180 
        THEN 1 
        ELSE 0 
    END AS churned
FROM customers c
JOIN orders o       ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'completed'
GROUP BY c.customer_id, c.segment, c.country, c.age
"""

print("Extracting features from database...")
with engine.connect() as conn:
    df = pd.read_sql(text(query), conn)

print(f"Dataset shape: {df.shape}")
print(f"Churn rate: {df['churned'].mean():.1%}")
print(f"\nFeature preview:")
print(df.head())

# ── Feature Engineering ───────────────────────────────────────
# Calculate how long the customer has been with us
df['customer_lifetime_days'] = (
    pd.to_datetime(df['last_order_date']) - 
    pd.to_datetime(df['first_order_date'])
).dt.days

# Orders per month — frequency metric
df['orders_per_month'] = (
    df['total_orders'] / 
    (df['customer_lifetime_days'] / 30).clip(lower=1)
)

# ── Encode categorical variables ──────────────────────────────
# ML models only understand numbers, not text.
# LabelEncoder converts "Jordan" → 0, "Saudi Arabia" → 1 etc.
le_segment = LabelEncoder()
le_country  = LabelEncoder()

df['segment_encoded'] = le_segment.fit_transform(df['segment'])
df['country_encoded']  = le_country.fit_transform(df['country'])

# ── Define features and target ────────────────────────────────
# X = inputs the model learns from
# y = what we're trying to predict (1=churned, 0=active)
features = [
    'age',
    'total_orders',
    'total_spent',
    'avg_order_value',
    'customer_lifetime_days',
    'orders_per_month',
    'segment_encoded',
    'country_encoded'
]

X = df[features]
y = df['churned']

print(f"\nFeatures: {features}")
print(f"Class distribution:\n{y.value_counts()}")

# ── Split data ────────────────────────────────────────────────
# 80% for training, 20% for testing
# test_size=0.2 means 20% held out
# random_state=42 makes split reproducible
# stratify=y ensures both splits have same churn ratio
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print(f"\nTraining samples: {len(X_train)}")
print(f"Test samples:     {len(X_test)}")

# ── Train Random Forest ───────────────────────────────────────
# Random Forest builds many decision trees and combines them.
# n_estimators=100 means 100 trees
# It's robust, handles mixed data types, and rarely overfits
print("\nTraining Random Forest model...")
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    class_weight='balanced'  # handles imbalanced churn data
)
model.fit(X_train, y_train)

# ── Evaluate ──────────────────────────────────────────────────
y_pred  = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

print("\n── Model Performance ──────────────────────────")
print(classification_report(y_test, y_pred,
      target_names=['Active', 'Churned']))
print(f"ROC-AUC Score: {roc_auc_score(y_test, y_proba):.3f}")

# ── Feature Importance ────────────────────────────────────────
# Which features matter most for predicting churn?
importance = pd.DataFrame({
    'feature':   features,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\n── Feature Importance ─────────────────────────")
print(importance.to_string(index=False))

# ── Save predictions back to database ────────────────────────
print("\nSaving churn predictions to database...")
df['churn_probability'] = model.predict_proba(X)[:, 1]
df['churn_prediction']  = model.predict(X)

predictions = df[[
    'customer_id',
    'total_orders',
    'total_spent',
    'days_since_last_order',
    'churn_probability',
    'churn_prediction',
    'churned'
]]

with engine.connect() as conn:
    predictions.to_sql(
        'churn_predictions',
        conn,
        if_exists='replace',
        index=False
    )
    conn.commit()

print("✅ Churn predictions saved to database table: churn_predictions")
print(f"\nHigh-risk customers (>70% churn probability):")
high_risk = df[df['churn_probability'] > 0.7][
    ['customer_id', 'segment', 'total_spent', 'churn_probability']
].sort_values('churn_probability', ascending=False)
print(high_risk.head(10).to_string(index=False))