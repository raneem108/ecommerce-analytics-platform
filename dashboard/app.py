import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="E-Commerce Revenue Intelligence",
    page_icon="📊",
    layout="wide"
)

# ── Connect to database ───────────────────────────────────────
load_dotenv()

@st.cache_resource
def get_engine():
    return create_engine(os.getenv("DB_URL"))

engine = get_engine()

# ── Load data functions ───────────────────────────────────────
# @st.cache_data means Streamlit remembers the result
# and doesn't re-query the database on every page refresh
@st.cache_data
def load_revenue_summary():
    with engine.connect() as conn:
        return pd.read_sql(
            text("SELECT * FROM analytics.mart_revenue_summary ORDER BY month"),
            conn
        )

@st.cache_data
def load_category_revenue():
    with engine.connect() as conn:
        return pd.read_sql(text("""
            SELECT 
                p.category,
                ROUND(SUM(oi.subtotal)::numeric, 2) AS revenue,
                COUNT(DISTINCT o.order_id)          AS orders
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p     ON oi.product_id = p.product_id
            WHERE o.status = 'completed'
            GROUP BY p.category
            ORDER BY revenue DESC
        """), conn)

@st.cache_data
def load_country_revenue():
    with engine.connect() as conn:
        return pd.read_sql(text("""
            SELECT 
                c.country,
                ROUND(SUM(oi.subtotal)::numeric, 2) AS revenue,
                COUNT(DISTINCT o.order_id)          AS orders
            FROM orders o
            JOIN customers c    ON o.customer_id = c.customer_id
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.status = 'completed'
            GROUP BY c.country
            ORDER BY revenue DESC
        """), conn)

@st.cache_data
def load_churn_predictions():
    with engine.connect() as conn:
        return pd.read_sql(
            text("SELECT * FROM public.churn_predictions"),
            conn
        )

@st.cache_data
def load_segment_revenue():
    with engine.connect() as conn:
        return pd.read_sql(text("""
            SELECT 
                c.segment,
                ROUND(SUM(oi.subtotal)::numeric, 2) AS revenue,
                COUNT(DISTINCT c.customer_id)       AS customers
            FROM customers c
            JOIN orders o       ON c.customer_id = o.customer_id
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.status = 'completed'
            GROUP BY c.segment
            ORDER BY revenue DESC
        """), conn)

# ── Load all data ─────────────────────────────────────────────
revenue_df   = load_revenue_summary()
category_df  = load_category_revenue()
country_df   = load_country_revenue()
churn_df     = load_churn_predictions()
segment_df   = load_segment_revenue()

# ── Header ────────────────────────────────────────────────────
st.title("📊 E-Commerce Revenue Intelligence Platform")
st.markdown("Real-time analytics dashboard powered by PostgreSQL, dbt, and ML")
st.divider()

# ── KPI Cards ─────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

total_revenue  = revenue_df['revenue'].sum()
total_orders   = revenue_df['total_orders'].sum()
total_customers = revenue_df['unique_customers'].max()
churn_rate     = (churn_df['churned'].sum() / len(churn_df) * 100)

col1.metric("Total Revenue",    f"${total_revenue:,.0f}")
col2.metric("Total Orders",     f"{total_orders:,}")
col3.metric("Active Customers", f"{total_customers:,}")
col4.metric("Churn Rate",       f"{churn_rate:.1f}%")

st.divider()

# ── Row 1: Revenue Trend + Category Breakdown ─────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📈 Monthly Revenue Trend")
    fig = px.line(
        revenue_df,
        x='month',
        y='revenue',
        markers=True,
        labels={'month': 'Month', 'revenue': 'Revenue ($)'},
    )
    fig.update_traces(line_color='#1f77b4', line_width=2)
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🏷️ Revenue by Category")
    fig = px.pie(
        category_df,
        values='revenue',
        names='category',
        hole=0.4,
    )
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

# ── Row 2: Country Revenue + Segment Revenue ──────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("🌍 Revenue by Country")
    fig = px.bar(
        country_df,
        x='country',
        y='revenue',
        color='revenue',
        color_continuous_scale='Blues',
        labels={'revenue': 'Revenue ($)', 'country': 'Country'},
    )
    fig.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("👥 Revenue by Segment")
    fig = px.bar(
        segment_df,
        x='segment',
        y='revenue',
        color='segment',
        labels={'revenue': 'Revenue ($)', 'segment': 'Segment'},
    )
    fig.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ── Row 3: Churn Analysis ─────────────────────────────────────
st.subheader("🚨 Churn Risk Analysis")

col1, col2 = st.columns(2)

with col1:
    # Churn probability distribution
    fig = px.histogram(
        churn_df,
        x='churn_probability',
        nbins=20,
        labels={'churn_probability': 'Churn Probability'},
        color_discrete_sequence=['#e74c3c']
    )
    fig.update_layout(height=300, title="Churn Probability Distribution")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # High risk customers table
    high_risk = churn_df[churn_df['churn_probability'] > 0.7]\
        .sort_values('churn_probability', ascending=False)\
        .head(10)[['customer_id', 'total_spent',
                   'days_since_last_order', 'churn_probability']]
    st.markdown("**Top 10 High-Risk Customers**")
    st.dataframe(high_risk, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────
st.divider()
st.markdown(
    "Built by **Raneem Abujabal** · "
    "PostgreSQL + dbt + Scikit-learn + Streamlit · "
    "[GitHub](https://github.com/raneem108/ecommerce-analytics-platform)"
)