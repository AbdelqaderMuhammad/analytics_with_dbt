WITH source AS (
    SELECT * FROM {{ source('raw', 'customers') }}
),
modified_source AS (
    SELECT
    CUSTOMER_ID, 
    FIRST_NAME,
    LAST_NAME,
    EMAIL,
    SIGNUP_DATE::DATE AS SIGNUP_DATE,
    ACQUISITION_CHANNEL,
    REGION,
    TIER,
    UPDATED_AT::TIMESTAMP AS UPDATED_AT
    FROM source
)

SELECT * 
FROM modified_source