-- grain: one row per customer_id

with completed_orders as (
    select * from {{ ref('int_orders_joined') }}
    where order_status = 'completed'
),

aggregated as (
    select
        customer_id,
        count(*)              as completed_order_count,
        sum(gross_revenue)    as lifetime_revenue,
        sum(gross_margin)     as lifetime_margin,
        min(order_at)         as first_order_at,
        max(order_at)         as most_recent_order_at
    from completed_orders
    group by customer_id
)

select * from aggregated