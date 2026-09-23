-- ============================================================
-- OrderIQ | Lecture 11 - Using AI to Build the ER Diagram
-- We pull the STRUCTURE out of Snowflake, hand it to AI,
-- and let AI draw the diagram AND write the SQL that checks it.
-- ============================================================

-- Where am I?
USE WAREHOUSE ORDERIQ_WH;
USE DATABASE  ORDERIQ_DB;
USE SCHEMA    RAW;

-- ------------------------------------------------------------
-- STEP 1: the structure.
-- INFORMATION_SCHEMA is a built-in catalogue in every database.
-- It stores data ABOUT your tables (names, columns, types), not the data itself.
-- ------------------------------------------------------------
SELECT table_name,
       column_name,
       data_type,
       ordinal_position              -- column order, as in the CSV
FROM ORDERIQ_DB.INFORMATION_SCHEMA.COLUMNS
WHERE table_schema = 'RAW'           -- only our raw layer
ORDER BY table_name, ordinal_position;
-- Download this result as CSV (download icon in the results panel).

-- ------------------------------------------------------------
-- STEP 1b: a few sample rows from each table.
-- Column names alone can mislead AI. Real values show it what the data looks like.
-- ------------------------------------------------------------
SELECT * FROM CUSTOMERS   LIMIT 5;
SELECT * FROM PRODUCTS    LIMIT 5;
SELECT * FROM ORDERS      LIMIT 5;
SELECT * FROM ORDER_ITEMS LIMIT 5;
-- Copy these too. Structure + samples = everything the AI needs.

-- ============================================================
-- DATA DICTIONARY  |  ORDERIQ_DB.RAW
-- Generated from INFORMATION_SCHEMA + sample data inspection
-- ============================================================

-- ┌──────────────────────────────────────────────────────────┐
-- │  TABLE: CUSTOMERS                                        │
-- │  Grain: one row per customer                             │
-- │  Rows:  8,160  (8,000 distinct CUSTOMER_ID)              │
-- ├────────────┬──────┬───┬──────────────────────────────────┤
-- │ COLUMN     │ TYPE │KEY│ DESCRIPTION                      │
-- ├────────────┼──────┼───┼──────────────────────────────────┤
-- │CUSTOMER_ID │ TEXT │PK │ Unique customer identifier       │
-- │            │      │   │ Format: C##### (e.g. C07667)     │
-- │CUSTOMER_NAME TEXT │   │ Full name of the customer        │
-- │            │      │   │ (e.g. Aditya Khan)               │
-- │EMAIL       │ TEXT │   │ Email address                    │
-- │            │      │   │ Pattern: first.last####@         │
-- │            │      │   │ example.com                      │
-- │CITY        │ TEXT │   │ City of residence                │
-- │            │      │   │ Values include: Mumbai, Delhi,   │
-- │            │      │   │ Bangalore, Chennai, Kolkata,     │
-- │            │      │   │ Pune, Hyderabad, Jaipur,         │
-- │            │      │   │ Lucknow, Ahmedabad               │
-- │            │      │   │ ⚠ Dirty: mixed case & aliases   │
-- │            │      │   │ (delhi/DELHI/Delhi, BLR/Bangalore│
-- │            │      │   │ /Bengaluru, Bombay/Mumbai/MUMBAI)│
-- │SIGNUP_DATE │ TEXT │   │ Date the customer signed up      │
-- │            │      │   │ ⚠ Stored as TEXT, mixed formats: │
-- │            │      │   │ YYYY-MM-DD, DD/MM/YYYY,          │
-- │            │      │   │ Mon DD YYYY                      │
-- └────────────┴──────┴───┴──────────────────────────────────┘

-- ┌──────────────────────────────────────────────────────────┐
-- │  TABLE: ORDERS                                           │
-- │  Grain: one row per order                                │
-- │  Rows:  60,900  (60,000 distinct ORDER_ID)               │
-- ├────────────┬──────┬───┬──────────────────────────────────┤
-- │ COLUMN     │ TYPE │KEY│ DESCRIPTION                      │
-- ├────────────┼──────┼───┼──────────────────────────────────┤
-- │ORDER_ID    │ TEXT │PK │ Unique order identifier          │
-- │            │      │   │ Format: ORD###### (e.g.          │
-- │            │      │   │ ORD035944)                       │
-- │CUSTOMER_ID │ TEXT │FK │ References CUSTOMERS.CUSTOMER_ID │
-- │            │      │   │ ✔ 0 orphan rows (fully valid)   │
-- │ORDER_DATE  │ TEXT │   │ Date the order was placed        │
-- │            │      │   │ Format: YYYY-MM-DD               │
-- │STATUS      │ TEXT │   │ Current order status             │
-- │            │      │   │ Values: COMPLETED, RETURNED,     │
-- │            │      │   │ PENDING, CANCELLED               │
-- │            │      │   │ ⚠ Dirty: lowercase "completed"  │
-- │CHANNEL     │ TEXT │   │ Sales channel through which the  │
-- │            │      │   │ order was placed                 │
-- │            │      │   │ Values: Web, App, Marketplace    │
-- └────────────┴──────┴───┴──────────────────────────────────┘

-- ┌──────────────────────────────────────────────────────────┐
-- │  TABLE: ORDER_ITEMS                                      │
-- │  Grain: one row per line item in an order                │
-- │  Rows:  123,963  (122,736 distinct ORDER_ITEM_ID)        │
-- ├────────────┬──────┬───┬──────────────────────────────────┤
-- │ COLUMN     │ TYPE │KEY│ DESCRIPTION                      │
-- ├────────────┼──────┼───┼──────────────────────────────────┤
-- │ORDER_ITEM_ID TEXT │PK │ Unique line-item identifier      │
-- │            │      │   │ Format: ITM####### (e.g.         │
-- │            │      │   │ ITM0109797)                      │
-- │ORDER_ID    │ TEXT │FK │ References ORDERS.ORDER_ID       │
-- │            │      │   │ ✔ 0 orphan rows (fully valid)   │
-- │PRODUCT_ID  │ TEXT │FK │ References PRODUCTS.PRODUCT_ID   │
-- │            │      │   │ ✔ 0 orphan rows (fully valid)   │
-- │QUANTITY    │ TEXT │   │ Number of units ordered           │
-- │            │      │   │ ⚠ Stored as TEXT, cast to INT   │
-- │            │      │   │ ⚠ Negative values exist (-3)    │
-- │UNIT_PRICE  │ TEXT │   │ Price per unit at time of order  │
-- │            │      │   │ ⚠ Stored as TEXT, cast to NUMBER│
-- │            │      │   │ (e.g. 20110.11)                  │
-- │DISCOUNT_PCT│ TEXT │   │ Discount percentage applied      │
-- │            │      │   │ ⚠ Stored as TEXT, cast to NUMBER│
-- │            │      │   │ Values seen: 0, 5, 10, 15       │
-- └────────────┴──────┴───┴──────────────────────────────────┘

-- ┌──────────────────────────────────────────────────────────┐
-- │  TABLE: PRODUCTS                                         │
-- │  Grain: one row per product (SKU)                        │
-- │  Rows:  400  (400 distinct — fully unique ✔)            │
-- ├────────────┬──────┬───┬──────────────────────────────────┤
-- │ COLUMN     │ TYPE │KEY│ DESCRIPTION                      │
-- ├────────────┼──────┼───┼──────────────────────────────────┤
-- │PRODUCT_ID  │ TEXT │PK │ Unique product identifier        │
-- │            │      │   │ Format: SKU#### (e.g. SKU0001)   │
-- │PRODUCT_NAME│ TEXT │   │ Descriptive product name         │
-- │            │      │   │ (e.g. Sunscreen Pro, Comic Max)  │
-- │CATEGORY    │ TEXT │   │ Product category                 │
-- │            │      │   │ Values: Beauty, Books, Sports,   │
-- │            │      │   │ Home & Kitchen, Fashion,         │
-- │            │      │   │ Electronics                      │
-- │            │      │   │ ⚠ Dirty: mixed case (Books/books,│
-- │            │      │   │ Beauty/beauty, etc.)             │
-- │UNIT_PRICE  │ TEXT │   │ List price of the product        │
-- │            │      │   │ ⚠ Stored as TEXT, cast to NUMBER│
-- └────────────┴──────┴───┴──────────────────────────────────┘

-- ============================================================
-- RELATIONSHIPS (validated with 0 orphan rows each)
--
--   CUSTOMERS  ──< 1:M >──  ORDERS        on CUSTOMER_ID
--   ORDERS     ──< 1:M >──  ORDER_ITEMS   on ORDER_ID
--   PRODUCTS   ──< 1:M >──  ORDER_ITEMS   on PRODUCT_ID
--
-- DATA QUALITY NOTES
--   • Duplicate PKs in CUSTOMERS (160), ORDERS (900),
--     ORDER_ITEMS (1,227) — needs dedup before analytics
--   • All columns are TEXT — numeric & date columns need
--     casting (QUANTITY, UNIT_PRICE, DISCOUNT_PCT, dates)
--   • Inconsistent casing in CITY, STATUS, CATEGORY
--   • Mixed date formats in SIGNUP_DATE
--   • Negative QUANTITY values in ORDER_ITEMS
-- ============================================================
