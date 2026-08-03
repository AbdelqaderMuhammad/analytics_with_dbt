-- grain: one row per order_id

with order_items as (
    select * from {{ ref('stg_order_items') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

item_economics as (
    select
        order_items.order_id,
        order_items.product_id,
        order_items.quantity,
        order_items.quantity * order_items.unit_price_at_order as line_revenue,
        order_items.quantity * products.unit_cost              as line_cost
    from order_items
    left join products on order_items.product_id = products.product_id
),

aggregated as (
    select
        order_id,
        sum(quantity)                     as item_count,
        sum(line_revenue)                 as gross_revenue,
        sum(line_cost)                    as total_cost,
        sum(line_revenue) - sum(line_cost) as gross_margin
    from item_economics
    group by order_id
)

select * from aggregated