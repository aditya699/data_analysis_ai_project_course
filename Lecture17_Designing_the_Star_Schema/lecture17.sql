-- =====================================================================
-- Lecture 17: ANALYTICS star schema
-- Reads only from ORDERIQ_DB.STAGING; writes only to ORDERIQ_DB.ANALYTICS
-- =====================================================================
USE WAREHOUSE ORDERIQ_WH;
USE DATABASE ORDERIQ_DB;
CREATE SCHEMA IF NOT EXISTS ORDERIQ_DB.ANALYTICS;

-- ---------------------------------------------------------------------
-- 1. DIM_DATE: one row per calendar day across the full order-date range
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE ORDERIQ_DB.ANALYTICS.DIM_DATE AS
WITH bounds AS (
    SELECT MIN(order_date) AS min_d, MAX(order_date) AS max_d
    FROM ORDERIQ_DB.STAGING.STG_ORDERS
),
days AS (
    SELECT DATEADD(day, ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1, b.min_d) AS full_date, b.max_d
    FROM bounds b, TABLE(GENERATOR(ROWCOUNT => 10000))
)
SELECT
    TO_NUMBER(TO_CHAR(full_date, 'YYYYMMDD'))  AS date_key,
    full_date,
    DAY(full_date)                             AS day,
    MONTH(full_date)                           AS month,
    MONTHNAME(full_date)                       AS month_name,
    QUARTER(full_date)                         AS quarter,
    YEAR(full_date)                            AS year,
    DAYOFWEEKISO(full_date)                    AS day_of_week,   -- 1=Mon .. 7=Sun
    DAYNAME(full_date)                         AS day_name,
    DAYOFWEEKISO(full_date) IN (6, 7)          AS is_weekend
FROM days
WHERE full_date <= max_d
ORDER BY full_date;

-- ---------------------------------------------------------------------
-- 2. DIM_CUSTOMER: one row per customer, surrogate key
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE ORDERIQ_DB.ANALYTICS.DIM_CUSTOMER AS
SELECT
    ROW_NUMBER() OVER (ORDER BY customer_id) AS customer_key,
    customer_id,
    customer_name,
    email,
    city,
    signup_date
FROM ORDERIQ_DB.STAGING.STG_CUSTOMERS;

-- ---------------------------------------------------------------------
-- 3. DIM_PRODUCT: one row per product, surrogate key
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE ORDERIQ_DB.ANALYTICS.DIM_PRODUCT AS
SELECT
    ROW_NUMBER() OVER (ORDER BY product_id) AS product_key,
    product_id,
    product_name,
    category,
    unit_price AS list_price
FROM ORDERIQ_DB.STAGING.STG_PRODUCTS;

-- ---------------------------------------------------------------------
-- 4. FACT_ORDER_ITEMS: one row per order line
--    line_revenue kept as signed in staging (returns negative)
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE ORDERIQ_DB.ANALYTICS.FACT_ORDER_ITEMS AS
SELECT
    i.order_item_id,
    i.order_id,
    d.date_key,
    c.customer_key,
    p.product_key,
    i.quantity,
    i.unit_price,
    i.discount_pct,
    i.line_revenue,
    i.is_return,
    o.status,
    o.channel
FROM ORDERIQ_DB.STAGING.STG_ORDER_ITEMS i
LEFT JOIN ORDERIQ_DB.STAGING.STG_ORDERS      o ON o.order_id    = i.order_id
LEFT JOIN ORDERIQ_DB.ANALYTICS.DIM_DATE      d ON d.full_date   = o.order_date
LEFT JOIN ORDERIQ_DB.ANALYTICS.DIM_CUSTOMER  c ON c.customer_id = o.customer_id
LEFT JOIN ORDERIQ_DB.ANALYTICS.DIM_PRODUCT   p ON p.product_id  = i.product_id;

-- =====================================================================
-- VERIFICATION (every *_ok column should be TRUE)
-- =====================================================================
SELECT
    -- row count matches staging
    (SELECT COUNT(*) FROM ORDERIQ_DB.ANALYTICS.FACT_ORDER_ITEMS)
      = (SELECT COUNT(*) FROM ORDERIQ_DB.STAGING.STG_ORDER_ITEMS)                    AS rowcount_ok,
    -- zero orphans (also catches NULL FKs)
    (SELECT COUNT(*) FROM ORDERIQ_DB.ANALYTICS.FACT_ORDER_ITEMS f
       LEFT JOIN ORDERIQ_DB.ANALYTICS.DIM_DATE d ON d.date_key = f.date_key
      WHERE d.date_key IS NULL) = 0                                                  AS date_fk_ok,
    (SELECT COUNT(*) FROM ORDERIQ_DB.ANALYTICS.FACT_ORDER_ITEMS f
       LEFT JOIN ORDERIQ_DB.ANALYTICS.DIM_CUSTOMER c ON c.customer_key = f.customer_key
      WHERE c.customer_key IS NULL) = 0                                              AS customer_fk_ok,
    (SELECT COUNT(*) FROM ORDERIQ_DB.ANALYTICS.FACT_ORDER_ITEMS f
       LEFT JOIN ORDERIQ_DB.ANALYTICS.DIM_PRODUCT p ON p.product_key = f.product_key
      WHERE p.product_key IS NULL) = 0                                               AS product_fk_ok,
    -- revenue reconciles
    (SELECT SUM(line_revenue) FROM ORDERIQ_DB.ANALYTICS.FACT_ORDER_ITEMS)
      = (SELECT SUM(line_revenue) FROM ORDERIQ_DB.STAGING.STG_ORDER_ITEMS)           AS revenue_ok,
    -- surrogate keys unique and not null
    (SELECT COUNT(*) = COUNT(DISTINCT date_key) AND COUNT(*) = COUNT(date_key)
       FROM ORDERIQ_DB.ANALYTICS.DIM_DATE)                                           AS date_key_ok,
    (SELECT COUNT(*) = COUNT(DISTINCT customer_key) AND COUNT(*) = COUNT(customer_key)
       FROM ORDERIQ_DB.ANALYTICS.DIM_CUSTOMER)                                       AS customer_key_ok,
    (SELECT COUNT(*) = COUNT(DISTINCT product_key) AND COUNT(*) = COUNT(product_key)
       FROM ORDERIQ_DB.ANALYTICS.DIM_PRODUCT)                                        AS product_key_ok,
    -- no missing days: row count equals span of days
    (SELECT COUNT(*) = DATEDIFF(day, MIN(full_date), MAX(full_date)) + 1
       FROM ORDERIQ_DB.ANALYTICS.DIM_DATE)                                           AS date_no_gaps_ok,
    (SELECT MIN(full_date) = (SELECT MIN(order_date) FROM ORDERIQ_DB.STAGING.STG_ORDERS)
        AND MAX(full_date) = (SELECT MAX(order_date) FROM ORDERIQ_DB.STAGING.STG_ORDERS)
       FROM ORDERIQ_DB.ANALYTICS.DIM_DATE)                                           AS date_range_ok;
