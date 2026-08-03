-- grain: one row per product_id

select
    product_id,
    product_name,
    category,
    unit_cost,
    unit_price,
    unit_price - unit_cost as unit_margin,
    case when unit_price > 0
         then (unit_price - unit_cost) / unit_price
         else null
    end                     as unit_margin_pct,
    is_active
from {{ ref('stg_products') }}