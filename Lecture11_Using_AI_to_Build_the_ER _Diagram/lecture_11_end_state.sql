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

-- ------------------------------------------------------------
-- STEP 2 happens outside Snowflake:
--   paste the structure + samples into Claude with the prompt,
--   get the Mermaid ER diagram + the verification SQL back.
--
-- STEP 3: paste the AI's verification SQL below and run it.
--   Our only job: read the results and judge - was the AI right?
-- ------------------------------------------------------------
