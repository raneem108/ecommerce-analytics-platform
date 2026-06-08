-- Staging model for customers
-- Enriches customer data with order statistics

with customer_orders as (
    select
        c.customer_id,
        c.name,
        c.email,
        c.country,
        c.segment,
        c.age,
        c.signup_date::date                     as signup_date,
        count(distinct o.order_id)              as total_orders,
        round(sum(oi.subtotal)::numeric, 2)     as total_spent,
        min(o.order_date::date)                 as first_order_date,
        max(o.order_date::date)                 as last_order_date,
        -- Days since last order
        ('2024-12-31'::date - 
            max(o.order_date::date))            as days_since_last_order,
        -- Churn label
        case
            when ('2024-12-31'::date - 
                max(o.order_date::date)) > 180
            then true
            else false
        end                                     as is_churned
    from public.customers c
    left join public.orders o
        on c.customer_id = o.customer_id
        and lower(o.status) = 'completed'
    left join public.order_items oi
        on o.order_id = oi.order_id
    group by
        c.customer_id,
        c.name,
        c.email,
        c.country,
        c.segment,
        c.age,
        c.signup_date
)

select * from customer_orders