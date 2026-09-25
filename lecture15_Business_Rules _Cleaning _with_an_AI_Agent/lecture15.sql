USE WAREHOUSE ORDERIQ_WH;
USE DATABASE  ORDERIQ_DB;
USE SCHEMA    STAGING;

----------------------------------------------------------------------
-- 1. STG_CUSTOMERS – city standardisation
----------------------------------------------------------------------
-- Rules:
--   Delhi / delhi / DELHI / New Delhi  -> 'Delhi'
--   Bombay                             -> 'Mumbai'
--   BLR / Bengaluru                    -> 'Bangalore'
--   Blank / 'NA' / 'null' / None      -> NULL
--   Everything else                    -> INITCAP + TRIM
----------------------------------------------------------------------
CREATE OR REPLACE VIEW STAGING.STG_CUSTOMERS AS
SELECT
    CUSTOMER_ID,
    CUSTOMER_NAME,
    EMAIL,
    CASE
        WHEN TRIM(CITY) IN ('', 'NA', 'null', 'None', 'NULL')
            THEN NULL
        WHEN UPPER(TRIM(CITY)) IN ('DELHI', 'NEW DELHI')
            THEN 'Delhi'
        WHEN UPPER(TRIM(CITY)) IN ('BOMBAY')
            THEN 'Mumbai'
        WHEN UPPER(TRIM(CITY)) IN ('BLR', 'BENGALURU')
            THEN 'Bangalore'
        ELSE INITCAP(TRIM(CITY))
    END AS CITY,
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
-- 2. STG_ORDERS – uppercase STATUS
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
    UPPER(TRIM(STATUS)) AS STATUS,
    CHANNEL
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY ORDER_ID ORDER BY ORDER_ID) AS RN
    FROM RAW.ORDERS
)
WHERE RN = 1;

----------------------------------------------------------------------
-- 3. STG_PRODUCTS – title-case CATEGORY, cast UNIT_PRICE
----------------------------------------------------------------------
CREATE OR REPLACE VIEW STAGING.STG_PRODUCTS AS
SELECT
    PRODUCT_ID,
    PRODUCT_NAME,
    INITCAP(TRIM(CATEGORY)) AS CATEGORY,
    NULLIF(TRY_TO_NUMBER(UNIT_PRICE, 10, 2), 0) AS UNIT_PRICE
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY PRODUCT_ID ORDER BY PRODUCT_ID) AS RN
    FROM RAW.PRODUCTS
)
WHERE RN = 1;

----------------------------------------------------------------------
-- 4. STG_ORDER_ITEMS – cast types, IS_RETURN, ABS_QUANTITY,
--    LINE_REVENUE
----------------------------------------------------------------------
CREATE OR REPLACE VIEW STAGING.STG_ORDER_ITEMS AS
SELECT
    ORDER_ITEM_ID,
    ORDER_ID,
    PRODUCT_ID,
    TRY_TO_NUMBER(QUANTITY)                       AS QUANTITY,
    (TRY_TO_NUMBER(QUANTITY) < 0)                 AS IS_RETURN,
    ABS(TRY_TO_NUMBER(QUANTITY))                  AS ABS_QUANTITY,
    NULLIF(TRY_TO_NUMBER(UNIT_PRICE, 10, 2), 0)  AS UNIT_PRICE,
    TRY_TO_NUMBER(DISCOUNT_PCT, 10, 2)            AS DISCOUNT_PCT,
    ABS(TRY_TO_NUMBER(QUANTITY))
        * NULLIF(TRY_TO_NUMBER(UNIT_PRICE, 10, 2), 0)
        * (1 - TRY_TO_NUMBER(DISCOUNT_PCT, 10, 2) / 100)
                                                  AS LINE_REVENUE
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY ORDER_ITEM_ID ORDER BY ORDER_ITEM_ID) AS RN
    FROM RAW.ORDER_ITEMS
)
WHERE RN = 1;

----------------------------------------------------------------------
-- 5. Verification
----------------------------------------------------------------------

-- 5a. Distinct CITY values after cleaning, with row counts
SELECT CITY, COUNT(*) AS cnt
FROM STAGING.STG_CUSTOMERS
GROUP BY CITY
ORDER BY CITY;

-- 5b. Distinct STATUS values after cleaning
SELECT STATUS, COUNT(*) AS cnt
FROM STAGING.STG_ORDERS
GROUP BY STATUS
ORDER BY STATUS;

-- 5c. Distinct CATEGORY values after cleaning
SELECT CATEGORY, COUNT(*) AS cnt
FROM STAGING.STG_PRODUCTS
GROUP BY CATEGORY
ORDER BY CATEGORY;

-- 5d. Return count and return rate
SELECT
    COUNT(*)                                          AS total_rows,
    COUNT_IF(IS_RETURN)                               AS return_rows,
    ROUND(COUNT_IF(IS_RETURN) * 100.0 / COUNT(*), 2) AS return_rate_pct
FROM STAGING.STG_ORDER_ITEMS;

-- 5e. Count of NULL unit_price rows
SELECT COUNT(*) AS null_unit_price_rows
FROM STAGING.STG_ORDER_ITEMS
WHERE UNIT_PRICE IS NULL;

-- 5f. 5 sample rows from STG_ORDER_ITEMS showing LINE_REVENUE
SELECT ORDER_ITEM_ID, ORDER_ID, QUANTITY, IS_RETURN, ABS_QUANTITY,
       UNIT_PRICE, DISCOUNT_PCT, LINE_REVENUE
FROM STAGING.STG_ORDER_ITEMS
LIMIT 5;
