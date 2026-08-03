-- grain: one row per order_id

select
    order_id,
    customer_id,
    order_at,
    order_status,
    channel,
    item_count,
    gross_revenue,
    total_cost,
    gross_margin,
    margin_pct,
    payment_status,
    is_late_payment,
    ticket_count,
    unresolved_ticket_count
from {{ ref('int_orders_joined') }}