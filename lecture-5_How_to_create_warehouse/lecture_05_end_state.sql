-- ============================================================
-- OrderIQ | Lecture 05 - Creating Your First Warehouse
-- ============================================================

-- A warehouse is COMPUTE, not storage.
-- It is the engine that runs your queries. No warehouse = no queries.
CREATE WAREHOUSE ORDERIQ_WH
  WAREHOUSE_SIZE = 'XSMALL'   -- smallest engine, 1 credit/hour. Enough for this whole course.
  AUTO_SUSPEND   = 60         -- switch off after 60 seconds idle. Off = zero credits.
  AUTO_RESUME    = TRUE;      -- switch back on automatically when a query arrives.

A worksheet is just the place where you write and run SQL in Snowflake.

-- Tell this worksheet which engine to use.
USE WAREHOUSE ORDERIQ_WH;


-- Check it exists. Look at the size, state and auto_suspend columns.
SHOW WAREHOUSES;

-- Proof that it is running our queries.
SELECT CURRENT_WAREHOUSE() AS my_warehouse;
