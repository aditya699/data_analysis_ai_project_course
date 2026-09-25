-- ============================================================
-- Lecture 13: Deduplication & Staging Views
-- RAW tables are NOT modified. Each STG_ view deduplicates
-- by primary key, keeping the first occurrence (by row order).
-- ============================================================

USE DATABASE ORDERIQ_DB;
USE WAREHOUSE ORDERIQ_WH;

-- ============================================================
-- 1. Before counts (RAW tables with duplicates)
-- ============================================================
SELECT 'BEFORE — RAW ROW COUNTS' AS STEP;

SELECT 'CUSTOMERS'   AS TABLE_NAME, COUNT(*) AS ROW_COUNT, COUNT(DISTINCT CUSTOMER_ID)   AS DISTINCT_KEYS, COUNT(*) - COUNT(DISTINCT CUSTOMER_ID)   AS DUPLICATE_ROWS FROM RAW.CUSTOMERS
UNION ALL
SELECT 'PRODUCTS',                  COUNT(*),              COUNT(DISTINCT PRODUCT_ID),                   COUNT(*) - COUNT(DISTINCT PRODUCT_ID)                   FROM RAW.PRODUCTS
UNION ALL
SELECT 'ORDERS',                    COUNT(*),              COUNT(DISTINCT ORDER_ID),                     COUNT(*) - COUNT(DISTINCT ORDER_ID)                     FROM RAW.ORDERS
UNION ALL
SELECT 'ORDER_ITEMS',               COUNT(*),              COUNT(DISTINCT ORDER_ITEM_ID),                COUNT(*) - COUNT(DISTINCT ORDER_ITEM_ID)                FROM RAW.ORDER_ITEMS;

-- ============================================================
-- 2. Create deduplicated staging views
-- ============================================================

CREATE OR REPLACE VIEW STAGING.STG_CUSTOMERS AS
SELECT CUSTOMER_ID, CUSTOMER_NAME, EMAIL, CITY, SIGNUP_DATE
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY CUSTOMER_ID ORDER BY CUSTOMER_ID) AS RN
    FROM RAW.CUSTOMERS
)
WHERE RN = 1;

CREATE OR REPLACE VIEW STAGING.STG_PRODUCTS AS
SELECT PRODUCT_ID, PRODUCT_NAME, CATEGORY, UNIT_PRICE
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY PRODUCT_ID ORDER BY PRODUCT_ID) AS RN
    FROM RAW.PRODUCTS
)
WHERE RN = 1;

CREATE OR REPLACE VIEW STAGING.STG_ORDERS AS
SELECT ORDER_ID, CUSTOMER_ID, ORDER_DATE, STATUS, CHANNEL
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY ORDER_ID ORDER BY ORDER_ID) AS RN
    FROM RAW.ORDERS
)
WHERE RN = 1;

CREATE OR REPLACE VIEW STAGING.STG_ORDER_ITEMS AS
SELECT ORDER_ITEM_ID, ORDER_ID, PRODUCT_ID, QUANTITY, UNIT_PRICE, DISCOUNT_PCT
FROM (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY ORDER_ITEM_ID ORDER BY ORDER_ITEM_ID) AS RN
    FROM RAW.ORDER_ITEMS
)
WHERE RN = 1;

-- ============================================================
-- 3. After counts (staging views, deduplicated)
-- ============================================================
SELECT 'AFTER — STAGING VIEW ROW COUNTS' AS STEP;

SELECT 'STG_CUSTOMERS'   AS VIEW_NAME, COUNT(*) AS ROW_COUNT FROM STAGING.STG_CUSTOMERS
UNION ALL
SELECT 'STG_PRODUCTS',                  COUNT(*)              FROM STAGING.STG_PRODUCTS
UNION ALL
SELECT 'STG_ORDERS',                    COUNT(*)              FROM STAGING.STG_ORDERS
UNION ALL
SELECT 'STG_ORDER_ITEMS',               COUNT(*)              FROM STAGING.STG_ORDER_ITEMS;

-- ============================================================
-- 4. Side-by-side comparison
-- ============================================================
SELECT 'CUSTOMERS'   AS TABLE_NAME, r.CNT AS RAW_ROWS, s.CNT AS STG_ROWS, r.CNT - s.CNT AS REMOVED
FROM (SELECT COUNT(*) CNT FROM RAW.CUSTOMERS) r, (SELECT COUNT(*) CNT FROM STAGING.STG_CUSTOMERS) s
UNION ALL
SELECT 'PRODUCTS',                  r.CNT,          s.CNT,          r.CNT - s.CNT
FROM (SELECT COUNT(*) CNT FROM RAW.PRODUCTS) r, (SELECT COUNT(*) CNT FROM STAGING.STG_PRODUCTS) s
UNION ALL
SELECT 'ORDERS',                    r.CNT,          s.CNT,          r.CNT - s.CNT
FROM (SELECT COUNT(*) CNT FROM RAW.ORDERS) r, (SELECT COUNT(*) CNT FROM STAGING.STG_ORDERS) s
UNION ALL
SELECT 'ORDER_ITEMS',               r.CNT,          s.CNT,          r.CNT - s.CNT
FROM (SELECT COUNT(*) CNT FROM RAW.ORDER_ITEMS) r, (SELECT COUNT(*) CNT FROM STAGING.STG_ORDER_ITEMS) s;
