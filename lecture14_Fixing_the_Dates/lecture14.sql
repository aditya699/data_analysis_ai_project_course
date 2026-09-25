USE WAREHOUSE ORDERIQ_WH;
USE DATABASE  ORDERIQ_DB;
USE SCHEMA    STAGING;

----------------------------------------------------------------------
-- 1. Helper: parse a VARCHAR date that may be in any of four formats
--    Returns NULL if none match (TRY_TO_DATE never errors).
----------------------------------------------------------------------
-- Formats:
--   2025-06-05      → YYYY-MM-DD
--   17/12/2024      → DD/MM/YYYY
--   Jun 05 2025     → MON DD YYYY
--   2025/06/05      → YYYY/MM/DD

----------------------------------------------------------------------
-- 2. Recreate STG_ORDERS – cast ORDER_DATE to DATE
----------------------------------------------------------------------
CREATE OR REPLACE VIEW STAGING.STG_ORDERS AS
SELECT
    ORDER_ID,
    CUSTOMER_ID,
    COALESCE(
        TRY_TO_DATE(ORDER_DATE, 'YYYY-MM-DD'),
        TRY_TO_DATE(ORDER_DATE, 'DD/MM/YYYY'),
        TRY_TO_DATE(ORDER_DATE, 'MON DD YYYY'),
        TRY_TO_DATE(ORDER_DATE, 'YYYY/MM/DD')
    ) AS ORDER_DATE,
    STATUS,
    CHANNEL
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY ORDER_ID ORDER BY ORDER_ID) AS RN
    FROM RAW.ORDERS
)
WHERE RN = 1;

----------------------------------------------------------------------
-- 3. Recreate STG_CUSTOMERS – cast SIGNUP_DATE to DATE
----------------------------------------------------------------------
CREATE OR REPLACE VIEW STAGING.STG_CUSTOMERS AS
SELECT
    CUSTOMER_ID,
    CUSTOMER_NAME,
    EMAIL,
    CITY,
    COALESCE(
        TRY_TO_DATE(SIGNUP_DATE, 'YYYY-MM-DD'),
        TRY_TO_DATE(SIGNUP_DATE, 'DD/MM/YYYY'),
        TRY_TO_DATE(SIGNUP_DATE, 'MON DD YYYY'),
        TRY_TO_DATE(SIGNUP_DATE, 'YYYY/MM/DD')
    ) AS SIGNUP_DATE
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY CUSTOMER_ID ORDER BY CUSTOMER_ID) AS RN
    FROM RAW.CUSTOMERS
)
WHERE RN = 1;

----------------------------------------------------------------------
-- 4. Verification
----------------------------------------------------------------------

-- 4a. Failed conversions (NULL date but non-empty source text)
SELECT 'STG_ORDERS' AS view_name,
       COUNT(*) AS failed_rows
FROM (
    SELECT o.ORDER_DATE AS converted,
           r.ORDER_DATE AS raw_text
    FROM STAGING.STG_ORDERS o
    JOIN (
        SELECT ORDER_ID, ORDER_DATE,
               ROW_NUMBER() OVER (PARTITION BY ORDER_ID ORDER BY ORDER_ID) AS RN
        FROM RAW.ORDERS
    ) r ON o.ORDER_ID = r.ORDER_ID AND r.RN = 1
    WHERE o.ORDER_DATE IS NULL AND r.ORDER_DATE IS NOT NULL
)
UNION ALL
SELECT 'STG_CUSTOMERS',
       COUNT(*)
FROM (
    SELECT c.SIGNUP_DATE AS converted,
           r.SIGNUP_DATE AS raw_text
    FROM STAGING.STG_CUSTOMERS c
    JOIN (
        SELECT CUSTOMER_ID, SIGNUP_DATE,
               ROW_NUMBER() OVER (PARTITION BY CUSTOMER_ID ORDER BY CUSTOMER_ID) AS RN
        FROM RAW.CUSTOMERS
    ) r ON c.CUSTOMER_ID = r.CUSTOMER_ID AND r.RN = 1
    WHERE c.SIGNUP_DATE IS NULL AND r.SIGNUP_DATE IS NOT NULL
);

-- 4b. Min / Max dates per column
SELECT 'ORDER_DATE'  AS col, MIN(ORDER_DATE) AS min_date, MAX(ORDER_DATE) AS max_date FROM STAGING.STG_ORDERS
UNION ALL
SELECT 'SIGNUP_DATE', MIN(SIGNUP_DATE), MAX(SIGNUP_DATE) FROM STAGING.STG_CUSTOMERS;

-- 4c. 5 sample rows: original text alongside converted date (ORDERS)
SELECT r.ORDER_ID,
       r.ORDER_DATE  AS original_text,
       o.ORDER_DATE  AS converted_date
FROM STAGING.STG_ORDERS o
JOIN (
    SELECT ORDER_ID, ORDER_DATE,
           ROW_NUMBER() OVER (PARTITION BY ORDER_ID ORDER BY ORDER_ID) AS RN
    FROM RAW.ORDERS
) r ON o.ORDER_ID = r.ORDER_ID AND r.RN = 1
LIMIT 5;

-- 4d. 5 sample rows: original text alongside converted date (CUSTOMERS)
SELECT r.CUSTOMER_ID,
       r.SIGNUP_DATE  AS original_text,
       c.SIGNUP_DATE  AS converted_date
FROM STAGING.STG_CUSTOMERS c
JOIN (
    SELECT CUSTOMER_ID, SIGNUP_DATE,
           ROW_NUMBER() OVER (PARTITION BY CUSTOMER_ID ORDER BY CUSTOMER_ID) AS RN
    FROM RAW.CUSTOMERS
) r ON c.CUSTOMER_ID = r.CUSTOMER_ID AND r.RN = 1
LIMIT 5;
