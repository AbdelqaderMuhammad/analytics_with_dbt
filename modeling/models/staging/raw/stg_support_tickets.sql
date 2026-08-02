with source as (
    select * from {{ source('raw', 'support_tickets') }}
),

renamed as (
    select
        ticket_id::integer      as ticket_id,
        customer_id::integer    as customer_id,
        order_id::integer       as order_id,
        created_at::timestamp   as created_at,
        resolved_at::timestamp  as resolved_at,
        category                as ticket_category
    from source
)

select * from renamed