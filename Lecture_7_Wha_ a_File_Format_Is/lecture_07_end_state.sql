-- ============================================================
-- OrderIQ | Lecture 07 - What a File Format Is
-- Teaching Snowflake how to READ our CSVs. Define once, reuse for all four.
-- ============================================================

-- Always know where you are before you create anything.
USE WAREHOUSE ORDERIQ_WH;
USE DATABASE  ORDERIQ_DB;
USE SCHEMA    RAW;

-- A FILE FORMAT is a saved object that answers:
-- "what separates the columns, is there a header, what counts as empty?"
CREATE FILE FORMAT FF_CSV
  TYPE = 'CSV'                            -- could also be JSON, PARQUET, AVRO
  FIELD_DELIMITER = ','                   -- comma separates our columns
  SKIP_HEADER = 1                         -- row 1 is column NAMES, not data.
                                          -- Forget this and 'order_id' loads as a row.
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'      -- so "Delhi, India" stays ONE value
  NULL_IF = ('', 'NA', 'null', 'NULL')    -- our messy cities literally say NA and null.
                                          -- This turns them into real NULLs at load time.
  EMPTY_FIELD_AS_NULL = TRUE              -- empty value -> NULL, not an empty string
  TRIM_SPACE = TRUE;                      -- kills the stray spaces in ' Delhi '

-- Confirm it exists.
SHOW FILE FORMATS IN SCHEMA RAW;

-- See every setting we just defined, including the defaults we didn't touch.
DESC FILE FORMAT FF_CSV;
