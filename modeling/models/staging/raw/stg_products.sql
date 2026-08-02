with source as (
    select * from {{ source('raw', 'products') }}
),

renamed as (
    select
        product_id::integer          as product_id,
        product_name,
        category,
        unit_cost::number(10,2)      as unit_cost,
        unit_price::number(10,2)     as unit_price,
        is_active::boolean           as is_active,
        price_updated_at::timestamp  as price_updated_at
    from source
)

select * from renamed