with source as (
    select * from {{ source('raw', 'payments') }}
),

renamed as (
    select
        payment_id::integer     as payment_id,
        order_id::integer       as order_id,
        payment_date::timestamp as paid_at,
        amount::number(10,2)    as amount,
        payment_method,
        status                  as payment_status,
        is_late::boolean        as is_late
    from source
)

select * from renamed