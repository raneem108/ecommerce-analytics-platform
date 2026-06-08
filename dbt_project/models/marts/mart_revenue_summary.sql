-- Revenue summary mart
-- This is the final table that powers the Metabase dashboard
-- Materialized as a TABLE for fast dashboard queries

with monthly_revenue as (
    select
        to_char(order_date, 'YYYY-MM')          as month,
        count(distinct order_id)                as total_orders,
        count(distinct customer_id)             as unique_customers,
        round(sum(order_total)::numeric, 2)     as revenue
    from {{ ref('stg_orders') }}
    where status = 'completed'
    group by to_char(order_date, 'YYYY-MM')
),

with_growth as (
    select
        month,
        total_orders,
        unique_customers,
        revenue,
        lag(revenue) over (
            order by month
        )                                       as prev_month_revenue,
        round(
            (revenue - lag(revenue) over (order by month))
            / nullif(lag(revenue) over (order by month), 0)
            * 100
        ::numeric, 1)                           as mom_growth_pct
    from monthly_revenue
)

select * from with_growth
order by month