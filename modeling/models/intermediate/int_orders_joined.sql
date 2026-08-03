-- grain: one row per order_id

with orders as (
    select * from {{ ref('stg_orders') }}
),

order_economics as (
    select * from {{ ref('int_order_item_economics') }}
),

payments as (
    select * from {{ ref('stg_payments') }}
),

tickets as (
    select
        order_id,
        count(*)                                              as ticket_count,
        sum(case when resolved_at is null then 1 else 0 end)  as unresolved_ticket_count
    from {{ ref('stg_support_tickets') }}
    group by order_id
),

joined as (
    select
        orders.order_id,
        orders.customer_id,
        orders.order_at,
        orders.order_status,
        orders.channel,
        order_economics.item_count,
        order_economics.gross_revenue,
        order_economics.total_cost,
        order_economics.gross_margin,
        case when order_economics.gross_revenue > 0
             then order_economics.gross_margin / order_economics.gross_revenue
             else null
        end                                          as margin_pct,
        payments.payment_status,
        payments.is_late                              as is_late_payment,
        coalesce(tickets.ticket_count, 0)              as ticket_count,
        coalesce(tickets.unresolved_ticket_count, 0)   as unresolved_ticket_count
    from orders
    left join order_economics on orders.order_id = order_economics.order_id
    left join payments        on orders.order_id = payments.order_id
    left join tickets         on orders.order_id = tickets.order_id
)

select * from joined