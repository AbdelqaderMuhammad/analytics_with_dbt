-- grain: one row per customer_id

with customers as (
    select * from {{ ref('stg_customers') }}
),

order_history as (
    select * from {{ ref('int_customer_order_history') }}
),

tier_benefits as (
    select * from {{ ref('tier_benefits') }}
),

final as (
    select
        customers.customer_id,
        customers.first_name,
        customers.last_name,
        customers.email,
        customers.signup_date,
        date_trunc('month', customers.signup_date)     as signup_cohort_month,
        customers.acquisition_channel,
        customers.region,
        customers.tier,
        tier_benefits.discount_pct,
        tier_benefits.free_shipping_threshold,
        coalesce(order_history.completed_order_count, 0) as completed_order_count,
        coalesce(order_history.lifetime_revenue, 0)       as lifetime_revenue,
        coalesce(order_history.lifetime_margin, 0)        as lifetime_margin,
        order_history.first_order_at,
        order_history.most_recent_order_at
    from customers
    left join order_history on customers.customer_id = order_history.customer_id
    left join tier_benefits on customers.tier = tier_benefits.tier
)

select * from final