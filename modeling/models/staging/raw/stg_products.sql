with source as (
    select * from {{ source('raw', 'products') }}
),

renamed as (
    select
        product_id::integer                   as product_id,
        product_name,
        category,
        {{ cast_currency('unit_cost') }}      as unit_cost,
        {{ cast_currency('unit_price') }}     as unit_price,
        is_active::boolean                    as is_active,
        price_updated_at::timestamp           as price_updated_at
    from source
)

select * from renamed