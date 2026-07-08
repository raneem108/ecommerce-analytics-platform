# ecommerce-analytics-platform
 


\# E-Commerce Revenue Intelligence Platform



A production-grade analytics platform that transforms raw e-commerce data into actionable business insights using PostgreSQL, dbt, Python, and machine learning.





\## What This Project Does



This platform answers real business questions:

\- Which customers are about to stop buying from us?

\- Which products generate the most profit?

\- Which markets are growing and which are declining?

\- What does next month's revenue look like?



\##  Architecture
Raw Data (CSV)

↓

PostgreSQL Database (Supabase)

↓

dbt Transformation Models

↓

ML Churn Prediction (Random Forest)

↓

Streamlit Dashboard (Live)







## Tech Stack



| Layer | Technology |

|---|---|

| Database | PostgreSQL (Supabase) |

| Transformation | dbt |

| ML Model | Scikit-learn Random Forest |

| Dashboard | Streamlit + Plotly |

| Language | Python 3.14 |

| Version Control | Git + GitHub |



\## Key Results



\- \*\*$1.6M\*\* total revenue analyzed across 2 years

\- \*\*10\*\* production SQL queries with window functions and CTEs

\- \*\*82.8% ROC-AUC\*\* churn prediction model

\- \*\*44.4%\*\* churn rate identified across 946 customers

\- \*\*3 dbt models\*\* transforming raw data into analytics-ready tables







\##  Business Insights Discovered



1\. \*\*Electronics drives 53% of revenue\*\* despite similar order volume to other categories

2\. \*\*Repeat customers spend 3x more\*\* than one-time buyers ($1,969 vs $633)

3\. \*\*Regular segment outperforms Premium\*\* — segmentation labels don't reflect actual spending

4\. \*\*Jordan represents 41% of revenue\*\* — largest single market

5\. \*\*Customer lifetime and order frequency\*\* are the strongest churn predictors



