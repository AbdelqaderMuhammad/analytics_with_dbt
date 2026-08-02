with source as (
    select * from {{ source('raw', 'orders') }}
),

renamed as (
    select
        order_id::integer      as order_id,
        customer_id::integer   as customer_id,
        order_date::timestamp  as order_at,
        status                 as order_status,
        channel
    from source
)

select * from renamed