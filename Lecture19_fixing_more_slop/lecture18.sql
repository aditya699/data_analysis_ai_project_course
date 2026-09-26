USE WAREHOUSE ORDERIQ_WH;

SELECT status,
       COUNT(*)                AS row_count,
       COUNT_IF(is_return)     AS lines_with_negative_qty,
       COUNT_IF(NOT is_return) AS lines_with_positive_qty
FROM ORDERIQ_DB.ANALYTICS.FACT_ORDER_ITEMS
GROUP BY status
ORDER BY status;