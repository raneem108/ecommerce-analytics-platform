-- Staging model for orders
-- Cleans raw orders data and casts correct types
-- This model creates a VIEW in the analytics schema

with raw_orders as (
    select
        order_id,
        customer_id,
        order_date::date                    as order_date,
        status,
        shipping_country,
        -- Standardize status to lowercase
        lower(status)                       as status_clean
    from public.orders
),

orders_with_items as (
    select
        o.order_id,
        o.customer_id,
        o.order_date,
        o.status_clean                      as status,
        o.shipping_country,
        count(oi.item_id)                   as item_count,
        round(sum(oi.subtotal)::numeric, 2) as order_total
    from raw_orders o
    left join public.order_items oi
        on o.order_id = oi.order_id
    group by
        o.order_id,
        o.customer_id,
        o.order_date,
        o.status_clean,
        o.shipping_country
)

select * from orders_with_items