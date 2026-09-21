-- ============================================================
-- OrderIQ | Lecture 09 - COPY INTO: Your First Table
-- File in the stage -> rows in a real table.
-- ============================================================

-- Where am I?
USE WAREHOUSE ORDERIQ_WH;
USE DATABASE  ORDERIQ_DB;
USE SCHEMA    RAW;

-- STEP 1: an empty table, same columns as orders.csv.
-- Everything is VARCHAR (text). Our dates come in 4 formats -
-- declare DATE here and '17/12/2024' would break the load.
-- Load as text now, fix types later in STAGING.
CREATE TABLE ORDERS (
  order_id     VARCHAR,
  customer_id  VARCHAR,
  order_date   VARCHAR,
  status       VARCHAR,
  channel      VARCHAR
);

-- Empty for now - just the headers.
SELECT * FROM ORDERS;

-- STEP 2: pour the file from the stage into the table.
-- No file format options needed: the stage already has FF_CSV attached.
COPY INTO ORDERS
FROM @ORDERIQ_STAGE
FILES = ('orders.csv');
-- The result shows: file name, status (LOADED), rows parsed, rows loaded, errors.

-- A real table now. Query it like any other.
SELECT * FROM ORDERS LIMIT 10;

-- How many rows landed? Should be 60,900.
SELECT COUNT(*) AS total_rows FROM ORDERS;

-- Run the SAME COPY again. Watch: nothing loads.
-- Snowflake remembers this file was already loaded, so no duplicates by accident.
COPY INTO ORDERS
FROM @ORDERIQ_STAGE
FILES = ('orders.csv');

-- Still 60,900. Proof.
SELECT COUNT(*) AS total_rows FROM ORDERS;
