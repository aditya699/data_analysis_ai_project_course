-- ============================================================
-- OrderIQ | Lecture 08 - Stages: Snowflake's Drop Zone
-- A stage is a folder in the cloud. Files land here before they become tables.
-- ============================================================

-- Where am I?
USE WAREHOUSE ORDERIQ_WH;
USE DATABASE  ORDERIQ_DB;
USE SCHEMA    RAW;

-- Create our NAMED stage: the shared folder we build ourselves.
CREATE STAGE ORDERIQ_STAGE
  FILE_FORMAT = FF_CSV                 -- attach Lecture 07's rules, so every file here
                                       -- is automatically read the right way
  DIRECTORY   = (ENABLE = TRUE);       -- lets you browse the files in the Snowsight UI

-- Confirm it exists.
SHOW STAGES IN SCHEMA RAW;

-- ------------------------------------------------------------
-- NOW UPLOAD THE 4 CSVs (in the UI, not SQL):
--   Catalog -> ORDERIQ_DB -> RAW -> Stages -> ORDERIQ_STAGE -> + Files
--   Select customers.csv, products.csv, orders.csv, order_items.csv -> Upload
-- ------------------------------------------------------------

-- What's in the folder? Name, size, and when it arrived.
LIST @ORDERIQ_STAGE;

-- The magic moment: read a file straight from the stage, BEFORE any table exists.
-- $1, $2, $3 = column 1, 2, 3 of the CSV.
SELECT $1 AS order_id,
       $2 AS customer_id,
       $3 AS order_date,
       $4 AS status
FROM @ORDERIQ_STAGE/orders.csv
LIMIT 10;
-- Notice the mixed date formats already. That's the mess we fix in STAGING.