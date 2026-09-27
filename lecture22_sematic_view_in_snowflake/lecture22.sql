-- Lecture 22: OrderIQ semantic view
USE WAREHOUSE ORDERIQ_WH;

-- ============ 0. DISCOVERY ============
DESC TABLE ORDERIQ_DB.ANALYTICS.FACT_ORDER_ITEMS;
DESC TABLE ORDERIQ_DB.ANALYTICS.DIM_CUSTOMER;
DESC TABLE ORDERIQ_DB.ANALYTICS.DIM_PRODUCT;
DESC TABLE ORDERIQ_DB.ANALYTICS.DIM_DATE;
SELECT DISTINCT status   FROM ORDERIQ_DB.ANALYTICS.FACT_ORDER_ITEMS ORDER BY 1;
SELECT DISTINCT channel  FROM ORDERIQ_DB.ANALYTICS.FACT_ORDER_ITEMS ORDER BY 1;
SELECT DISTINCT category FROM ORDERIQ_DB.ANALYTICS.DIM_PRODUCT ORDER BY 1;
SELECT DISTINCT city     FROM ORDERIQ_DB.ANALYTICS.DIM_CUSTOMER ORDER BY 1;

-- ============ 1. SEMANTIC VIEW ============
CREATE OR REPLACE SEMANTIC VIEW ORDERIQ_DB.ANALYTICS.ORDERIQ_SV
  TABLES (
    order_items AS ORDERIQ_DB.ANALYTICS.FACT_ORDER_ITEMS
      PRIMARY KEY (ORDER_ITEM_ID)
      WITH SYNONYMS ('sales', 'order lines', 'transactions')
      COMMENT = 'Fact table: one row per order line. LINE_REVENUE is signed (returns negative).',
    customers AS ORDERIQ_DB.ANALYTICS.DIM_CUSTOMER
      PRIMARY KEY (CUSTOMER_KEY)
      WITH SYNONYMS ('customer', 'clients')
      COMMENT = 'Customer dimension: one row per customer, with city.',
    products AS ORDERIQ_DB.ANALYTICS.DIM_PRODUCT
      PRIMARY KEY (PRODUCT_KEY)
      WITH SYNONYMS ('product', 'items', 'catalog')
      COMMENT = 'Product dimension: one row per product, with category.',
    dates AS ORDERIQ_DB.ANALYTICS.DIM_DATE
      PRIMARY KEY (DATE_KEY)
      WITH SYNONYMS ('calendar')
      COMMENT = 'Calendar dimension: one row per day.'
  )
  RELATIONSHIPS (
    order_items_to_customer AS order_items (CUSTOMER_KEY) REFERENCES customers,
    order_items_to_product  AS order_items (PRODUCT_KEY)  REFERENCES products,
    order_items_to_date     AS order_items (DATE_KEY)     REFERENCES dates
  )
  FACTS (
    order_items.quantity AS QUANTITY
      COMMENT = 'Units on the order line.',
    order_items.unit_price AS UNIT_PRICE
      COMMENT = 'Price per unit on the order line.',
    order_items.line_revenue AS LINE_REVENUE
      COMMENT = 'Signed revenue of the order line; returns are negative.',
    order_items.is_return AS IS_RETURN
      COMMENT = 'TRUE when the order line is a return.'
  )
  DIMENSIONS (
    customers.city AS CITY
      WITH SYNONYMS ('location', 'town')
      COMMENT = 'Customer city.'
      SAMPLE_VALUES ('Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Pune'),
    products.category AS CATEGORY
      WITH SYNONYMS ('product category', 'department')
      COMMENT = 'Product category.'
      SAMPLE_VALUES ('Beauty', 'Books', 'Electronics', 'Fashion', 'Home & Kitchen', 'Sports') IS_ENUM,
    order_items.channel AS CHANNEL
      WITH SYNONYMS ('sales channel', 'platform')
      COMMENT = 'Channel the order was placed through.'
      SAMPLE_VALUES ('App', 'Marketplace', 'Web') IS_ENUM,
    order_items.status AS STATUS
      WITH SYNONYMS ('order status', 'line status')
      COMMENT = 'Order line status. Values are uppercase.'
      SAMPLE_VALUES ('CANCELLED', 'COMPLETED', 'PENDING', 'RETURNED') IS_ENUM,
    dates.order_date AS FULL_DATE
      WITH SYNONYMS ('order day', 'day')
      COMMENT = 'Calendar date the order was placed.',
    dates.order_month AS MONTH
      WITH SYNONYMS ('month')
      COMMENT = 'Month number (1-12) of the order date.',
    dates.order_quarter AS QUARTER
      WITH SYNONYMS ('quarter', 'qtr')
      COMMENT = 'Quarter number (1-4) of the order date.',
    dates.order_year AS YEAR
      WITH SYNONYMS ('year')
      COMMENT = 'Calendar year of the order date.'
  )
  METRICS (
    order_items.total_revenue AS SUM(IFF(order_items.STATUS NOT IN ('CANCELLED','PENDING'), order_items.LINE_REVENUE, NULL))
      WITH SYNONYMS ('revenue', 'sales', 'net sales')
      COMMENT = 'Sum of LINE_REVENUE for lines that are not CANCELLED and not PENDING. Returns are negative so they subtract.',
    order_items.order_count AS COUNT(DISTINCT IFF(order_items.STATUS NOT IN ('CANCELLED','PENDING'), order_items.ORDER_ID, NULL))
      WITH SYNONYMS ('orders', 'number of orders')
      COMMENT = 'Count of distinct order IDs, excluding CANCELLED and PENDING lines.',
    order_items.return_rate AS DIV0(
        COUNT_IF(order_items.STATUS NOT IN ('CANCELLED','PENDING') AND order_items.IS_RETURN = TRUE),
        COUNT_IF(order_items.STATUS NOT IN ('CANCELLED','PENDING')))
      WITH SYNONYMS ('returns rate')
      COMMENT = 'Return lines (IS_RETURN = TRUE) divided by all lines, by line count. CANCELLED and PENDING lines are excluded from both.',
    order_items.active_customers AS COUNT(DISTINCT IFF(order_items.STATUS NOT IN ('CANCELLED','PENDING'), order_items.CUSTOMER_KEY, NULL))
      WITH SYNONYMS ('customers', 'buyers')
      COMMENT = 'Count of distinct customers with at least one order line that is not CANCELLED and not PENDING.',
    avg_order_value AS DIV0(order_items.total_revenue, order_items.order_count)
      WITH SYNONYMS ('AOV', 'average basket')
      COMMENT = 'Average order value = total_revenue / order_count (DIV0: 0 when no orders).'
  )
  COMMENT = 'OrderIQ sales semantic view. Course business rules for revenue, orders, returns and customers.'
  AI_SQL_GENERATION 'Order data ends on 2025-12-31. Interpret relative time phrases like last month, last quarter or this year relative to the latest order date in the data, never relative to the current date.'
  AI_QUESTION_CATEGORIZATION 'If a question asks about dates after 2025-12-31, reply that OrderIQ data ends on 2025-12-31.';

-- ============ 2. VERIFICATION ============
-- 2a. All 5 metrics: semantic view vs plain SQL (expect match = TRUE on every row)
WITH sv AS (
  SELECT * FROM SEMANTIC_VIEW(ORDERIQ_DB.ANALYTICS.ORDERIQ_SV
    METRICS order_items.total_revenue, order_items.order_count, order_items.return_rate,
            order_items.active_customers, avg_order_value)
), raw AS (
  SELECT SUM(line_revenue)                                 AS total_revenue,
         COUNT(DISTINCT order_id)                          AS order_count,
         DIV0(COUNT_IF(is_return = TRUE), COUNT(*))        AS return_rate,
         COUNT(DISTINCT customer_key)                      AS active_customers,
         DIV0(SUM(line_revenue), COUNT(DISTINCT order_id)) AS avg_order_value
  FROM ORDERIQ_DB.ANALYTICS.FACT_ORDER_ITEMS
  WHERE status NOT IN ('CANCELLED', 'PENDING')
)
SELECT 'total_revenue' AS metric, sv.total_revenue::STRING AS sv_value, raw.total_revenue::STRING AS sql_value, sv.total_revenue = raw.total_revenue AS match FROM sv, raw
UNION ALL SELECT 'order_count',      sv.order_count::STRING,      raw.order_count::STRING,      sv.order_count = raw.order_count           FROM sv, raw
UNION ALL SELECT 'return_rate',      sv.return_rate::STRING,      raw.return_rate::STRING,      sv.return_rate = raw.return_rate           FROM sv, raw
UNION ALL SELECT 'active_customers', sv.active_customers::STRING, raw.active_customers::STRING, sv.active_customers = raw.active_customers FROM sv, raw
UNION ALL SELECT 'avg_order_value',  sv.avg_order_value::STRING,  raw.avg_order_value::STRING,  sv.avg_order_value = raw.avg_order_value   FROM sv, raw;

-- 2b. total_revenue by year: semantic view vs plain SQL
WITH sv AS (
  SELECT * FROM SEMANTIC_VIEW(ORDERIQ_DB.ANALYTICS.ORDERIQ_SV
    DIMENSIONS dates.order_year METRICS order_items.total_revenue)
), raw AS (
  SELECT d.year, SUM(f.line_revenue) AS total_revenue
  FROM ORDERIQ_DB.ANALYTICS.FACT_ORDER_ITEMS f
  JOIN ORDERIQ_DB.ANALYTICS.DIM_DATE d ON f.date_key = d.date_key
  WHERE f.status NOT IN ('CANCELLED', 'PENDING')
  GROUP BY d.year
)
SELECT COALESCE(sv.order_year, raw.year) AS year, sv.total_revenue AS sv_revenue,
       raw.total_revenue AS sql_revenue, sv.total_revenue = raw.total_revenue AS match
FROM sv FULL OUTER JOIN raw ON sv.order_year = raw.year
ORDER BY 1;

-- 2c. Structure and comments
DESCRIBE SEMANTIC VIEW ORDERIQ_DB.ANALYTICS.ORDERIQ_SV;
