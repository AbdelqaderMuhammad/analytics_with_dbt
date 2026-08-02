with source as (
    select * from {{ source('raw', 'order_items') }}
),

renamed as (
    select
        order_item_id::integer            as order_item_id,
        order_id::integer                 as order_id,
        product_id::integer                as product_id,
        quantity::integer                  as quantity,
        unit_price_at_order::number(10,2)  as unit_price_at_order
    from source
)

select * from renamed