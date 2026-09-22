-- ============================================================
-- OrderIQ | Lecture 10 - Loading the Other Three Tables
-- Same pattern as Lecture 09: empty table -> COPY INTO. Three more times.
-- ============================================================

-- Where am I?
USE WAREHOUSE ORDERIQ_WH;
USE DATABASE  ORDERIQ_DB;
USE SCHEMA    RAW;

-- ------------------------------------------------------------
-- 1. CUSTOMERS  (who bought)
-- ------------------------------------------------------------
CREATE TABLE CUSTOMERS (
  customer_id    VARCHAR,
  customer_name  VARCHAR,
  email          VARCHAR,
  city           VARCHAR,   -- Delhi / delhi / New Delhi - fixed later
  signup_date    VARCHAR    -- 4 date formats - text for now
);

COPY INTO CUSTOMERS
FROM @ORDERIQ_STAGE
FILES = ('customers.csv');

-- ------------------------------------------------------------
-- 2. PRODUCTS  (what we sell)
-- ------------------------------------------------------------
CREATE TABLE PRODUCTS (
  product_id    VARCHAR,
  product_name  VARCHAR,
  category      VARCHAR,
  unit_price    VARCHAR     -- even prices stay text in RAW; a few are blank or 0
);

COPY INTO PRODUCTS
FROM @ORDERIQ_STAGE
FILES = ('products.csv');

-- ------------------------------------------------------------
-- 3. ORDER_ITEMS  (one row per line in an order - the biggest table)
-- ------------------------------------------------------------
CREATE TABLE ORDER_ITEMS (
  order_item_id  VARCHAR,
  order_id       VARCHAR,   -- joins to ORDERS
  product_id     VARCHAR,   -- joins to PRODUCTS
  quantity       VARCHAR,   -- negative = a return
  unit_price     VARCHAR,   -- price actually paid
  discount_pct   VARCHAR
);

COPY INTO ORDER_ITEMS
FROM @ORDERIQ_STAGE
FILES = ('order_items.csv');

-- ------------------------------------------------------------
-- All four RAW tables, one check.
-- Expected: CUSTOMERS 8,160 | PRODUCTS 400 | ORDERS 60,900 | ORDER_ITEMS 123,963
-- ------------------------------------------------------------
SELECT 'CUSTOMERS'   AS table_name, COUNT(*) AS row_count FROM CUSTOMERS
UNION ALL
SELECT 'PRODUCTS',                  COUNT(*)              FROM PRODUCTS
UNION ALL
SELECT 'ORDERS',                    COUNT(*)              FROM ORDERS
UNION ALL
SELECT 'ORDER_ITEMS',               COUNT(*)              FROM ORDER_ITEMS;

-- Quick peek at each - notice the mess is all still there. RAW is untouched.
SELECT * FROM CUSTOMERS   LIMIT 5;
SELECT * FROM PRODUCTS    LIMIT 5;
SELECT * FROM ORDER_ITEMS LIMIT 5;
