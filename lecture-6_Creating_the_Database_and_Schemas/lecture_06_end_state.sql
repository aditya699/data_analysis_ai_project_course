-- ============================================================
-- OrderIQ | Lecture 06 - Creating the Database and Schemas
-- One database (the cabinet), three schemas (the drawers).
-- ============================================================

-- Make sure we are running on our own engine from Lecture 05.
USE WAREHOUSE ORDERIQ_WH;

-- The cabinet: everything for this project lives inside it.
CREATE DATABASE ORDERIQ_DB;

-- Work inside it, so we don't have to type the full name every time.
USE DATABASE ORDERIQ_DB;

-- Drawer 1: data exactly as it arrives from the CSVs. Mess included.
-- We never edit this layer - it is our safety net.
CREATE SCHEMA RAW;

-- Drawer 2: the cleaned version. Duplicates gone, dates parsed, cities fixed.
-- This is a workspace, not a final answer.
CREATE SCHEMA STAGING;

-- Drawer 3: business-ready tables. The dashboard and the AI read only from here.
CREATE SCHEMA ANALYTICS;

-- Check all three exist (you will also see PUBLIC and INFORMATION_SCHEMA,
-- which Snowflake creates for every database automatically).
SHOW SCHEMAS IN DATABASE ORDERIQ_DB;

-- Point this worksheet at RAW - that is where we load data next lecture.
USE SCHEMA RAW;

-- Where am I right now? Good habit before running anything.
SELECT CURRENT_DATABASE() AS db,
       CURRENT_SCHEMA()   AS schema,
       CURRENT_WAREHOUSE() AS warehouse;
