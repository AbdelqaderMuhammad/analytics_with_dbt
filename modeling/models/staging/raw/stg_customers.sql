-- explicit casting 
-- explicit selection of columns


with source as (
    select * from {{ source('raw', 'customers') }}
),

renamed as (
    select
        customer_id::integer         as customer_id,
        first_name,
        last_name,
        email,
        signup_date::date            as signup_date,
        acquisition_channel,
        region,
        tier,
        updated_at::timestamp        as updated_at
    from source
)

select * from renamed