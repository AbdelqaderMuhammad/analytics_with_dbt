with source as (
    select * from {{ source('raw', 'marketing_spend') }}
),

renamed as (
    select
        date::date            as spend_date,
        channel,
        spend::number(10,2)   as spend_amount
    from source
)

select * from renamed