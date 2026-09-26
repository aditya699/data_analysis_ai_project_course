# OrderIQ — Modern Data Analyst Course Project

Course materials for building **OrderIQ**, an end-to-end analytics project on Snowflake. You start with four messy e-commerce CSVs and work up to clean, business-ready tables using the medallion architecture (RAW → STAGING → ANALYTICS).

Each lecture folder holds its slides (`.pptx`) and, where there's hands-on work, an **end-state SQL file** — the finished worksheet for that lecture. Lecture videos are not tracked in this repo.

## Repository layout

| Folder | Topic | Contents |
| --- | --- | --- |
| `lecture-3_How_Snowflake_Works_Storage,_Compute_and_Credits` | Storage, compute and credits | Slides |
| `lecture-4_Meet_the_Dataset_(The_Messy_E-commerce_Data)` | Meet the dataset | Slides + `datasets/` CSVs |
| `lecture-5_How_to_create_warehouse` | Creating your first warehouse | `lecture_05_end_state.sql` |
| `lecture-6_Creating_the_Database_and_Schemas` | Database and schemas | Slides + `lecture_06_end_state.sql` |
| `Lecture_7_Wha_ a_File_Format_Is` | What a file format is | Slides + `lecture_07_end_state.sql` |
| `lecture-8_Snowflake's_Drop_Zone` | Stages: Snowflake's drop zone | Slides + `lecture8.sql` |
| `Lecture_9_copy_into_table` | COPY INTO: your first table | Slides + `lecture_09_end_state.sql` |
| `Lecture_10_Loading_the_Other_Three _Tables` | Loading the other three tables | `lecture_10_end_state.sql` |
| `Lecture11_Using_AI_to_Build_the_ER _Diagram` | Using AI to build the ER diagram | Slides + `lecture_11_end_state.sql` |
| `Lecture12_Using_AI_to_Build_the Data_Dictionary` | Using AI to build the data dictionary | `lecture_12_end_state.sql` |
| `Lecture13_Cleaning_Data _ Removing _Duplicates` | Cleaning data: removing duplicates | Slides + `prompt.txt` (AI prompt) + `lecture13.sql` |
| `lecture14_Fixing_the_Dates` | Fixing the dates | Slides + `lecture_14_prompt.txt` (AI prompt) + `lecture14.sql` |
| `lecture15_Business_Rules _Cleaning _with_an_AI_Agent` | Business-rules cleaning with an AI agent | Slides + `prompt.txt` (AI prompt) + `lecture15.sql` |
| `Lecture16_Fixing_Agent_Slop` | Fixing agent slop | `lecture15_ai_slop_fixed.sql` |
| `Lecture17_Designing_the_Star_Schema` | Designing the star schema | Slides + `star_schema.JPG` (diagram) + `prompt.txt` (AI prompt) + `lecture17.sql` |
| `Lecture18_fixing_lecture17_ai_slop` | Fixing Lecture 17's AI slop | `prompt.txt` (AI prompt) |
| `Lecture19_fixing_more_slop` | Fixing more slop | `prompt.txt` (AI prompt) + `lecture18.sql` (status check) + `lecture17_fixed_code.sql` (final star schema) |
| `lecture_20_revision` | Revision | Slides |

`OrderIQ-Day-by-Day-Plan.pdf` is the full course plan.

## The dataset

Four intentionally messy CSVs in `lecture-4_.../datasets/` — inconsistent city casing, `NA`/`null` placeholder strings, stray whitespace and duplicates are all deliberate, so there's something real to clean.

| File | Rows | Columns |
| --- | --- | --- |
| `customers.csv` | ~8,160 | `customer_id`, `customer_name`, `email`, `city`, `signup_date` |
| `orders.csv` | ~60,900 | `order_id`, `customer_id`, `order_date`, `status`, `channel` |
| `order_items.csv` | ~123,960 | `order_item_id`, `order_id`, `product_id`, `quantity`, `unit_price`, `discount_pct` |
| `products.csv` | ~400 | `product_id`, `product_name`, `category`, `unit_price` |

## Getting started

1. Sign up for a [Snowflake trial account](https://signup.snowflake.com/) — no credit card needed, and the trial credits cover this course.
2. Open a worksheet and run the end-state SQL files in order: Lecture 05, 06, 07, 08, 09, 10, 11, then 12. Each one builds on the last.
3. In Lecture 08, upload the four CSVs to the stage through the Snowsight UI (Catalog → `ORDERIQ_DB` → `RAW` → Stages → `ORDERIQ_STAGE` → **+ Files**) before running the `LIST` and `SELECT` queries.
4. From Lecture 13 on, the cleanup is done with AI. Give it each lecture's prompt file in order (13, 14, then 15) and let it write and run the SQL. The `lecture13.sql`, `lecture14.sql` and `lecture15.sql` files hold the SQL the AI produced, so you can compare your results or run them directly. In Lecture 16 you review the Lecture 15 output and fix what the AI got wrong; `lecture15_ai_slop_fixed.sql` is the corrected version. Lectures 17–19 follow the same loop for the ANALYTICS layer: build the star schema from the prompt and diagram, then review and fix it. `Lecture19_fixing_more_slop/lecture17_fixed_code.sql` is the final version to run.

That sequence gives you:

- **Warehouse** `ORDERIQ_WH` — XSMALL, auto-suspends after 60s so you don't burn credits
- **Database** `ORDERIQ_DB` with schemas `RAW`, `STAGING`, `ANALYTICS`
- **File format** `FF_CSV` in `RAW`, configured to handle the messiness in the source files
- **Named stage** `ORDERIQ_STAGE` in `RAW`, with `FF_CSV` attached and a directory table enabled — the landing zone for the raw CSVs, queryable before any table exists
- **Four RAW tables**, each loaded from the stage with `COPY INTO` — every column is `VARCHAR`, and the mess is left as-is to be fixed later in `STAGING`:
  - `RAW.ORDERS` — 60,900 rows
  - `RAW.CUSTOMERS` — 8,160 rows
  - `RAW.PRODUCTS` — 400 rows
  - `RAW.ORDER_ITEMS` — 123,963 rows
- **An ER diagram of the RAW layer**: in Lecture 11 you pull the table structure from `INFORMATION_SCHEMA.COLUMNS`, add a few sample rows from each table, and give both to an AI. It returns a Mermaid ER diagram and SQL that checks the relationships. You run that SQL and judge whether the AI got it right.
- **A data dictionary of the RAW layer**, built with AI in Lecture 12. For each table it records the grain, row counts, keys, what each column means and any known data problems. It also confirms the three relationships have no orphan rows and lists the cleanup `STAGING` will need: duplicate keys, text columns to cast, inconsistent casing, mixed date formats and negative quantities.
- **Four STAGING views** — `STG_CUSTOMERS`, `STG_PRODUCTS`, `STG_ORDERS`, `STG_ORDER_ITEMS` — which are the RAW tables with duplicate rows removed. In Lecture 13 an AI builds them from the prompt in `prompt.txt` and shows row counts before and after. RAW is not changed.
- **Real dates in STAGING**: in Lecture 14 an AI updates `STG_ORDERS.ORDER_DATE` and `STG_CUSTOMERS.SIGNUP_DATE` from text to `DATE`. It parses all four formats in the data, turns anything it can't parse into `NULL`, and keeps the deduplication logic unchanged. It then reports how many rows failed to convert and each column's date range, which should be 2024-01-01 to 2025-12-31.
- **Business rules applied in STAGING**: in Lecture 15 an AI adds the remaining cleanup to the views:
  - City names are standardised (Delhi, Mumbai, Bangalore), and blank, `NA` and `null` become `NULL`.
  - Order status is uppercased and product categories are title-cased.
  - Prices become `NUMBER(10,2)`, and blank or zero prices become `NULL`.
  - `STG_ORDER_ITEMS` gets three new columns: `IS_RETURN` (true when the quantity is negative), `ABS_QUANTITY` and `LINE_REVENUE`. Returns are kept so the return rate can be calculated later.
- **Reviewing the AI's work**: Lecture 16 checks the Lecture 15 SQL against the prompt and fixes what the AI got wrong. The AI had used `ABS(quantity)` in `LINE_REVENUE`, which counted returns as sales. The fixed version uses the signed quantity, so returns come out negative and `SUM(LINE_REVENUE)` is net revenue.
- **A star schema in ANALYTICS** (Lecture 17), built by AI from the diagram in `star_schema.JPG` and loaded from the STAGING views:
  - `DIM_DATE` — one row per day across the order-date range, keyed `YYYYMMDD`.
  - `DIM_CUSTOMER` and `DIM_PRODUCT` — one row each, with surrogate keys.
  - `FACT_ORDER_ITEMS` — one row per order line, holding the keys to the three dimensions plus quantity, price, discount, revenue, return flag, status and channel.

  The script ends with checks that the row count and revenue match staging, that every key is unique and has a matching dimension row, and that `DIM_DATE` has no missing days.
- **A `NET_REVENUE` column, and what happened to it** (Lectures 18–19): Lecture 18's prompt tries to leave cancelled and pending orders out of revenue by looking at order status. The check in `lecture18.sql` shows that status doesn't line up with the quantities, so it can't be trusted. The business then agrees on a simpler rule: the sign of the quantity decides whether a line is a sale (positive) or a return (negative), and status is ignored.

Run the SQL yourself rather than pasting it wholesale — the comments in each file explain *why* every option is set the way it is.

## Course progress

- [x] Lecture 3 — How Snowflake works: storage, compute and credits
- [x] Lecture 4 — Meet the dataset
- [x] Lecture 5 — Creating your first warehouse
- [x] Lecture 6 — Creating the database and schemas
- [x] Lecture 7 — What a file format is
- [x] Lecture 8 — Stages: Snowflake's drop zone
- [x] Lecture 9 — COPY INTO: your first table
- [x] Lecture 10 — Loading the other three tables
- [x] Lecture 11 — Using AI to build the ER diagram
- [x] Lecture 12 — Using AI to build the data dictionary
- [x] Lecture 13 — Cleaning data: removing duplicates
- [x] Lecture 14 — Fixing the dates
- [x] Lecture 15 — Business-rules cleaning with an AI agent
- [x] Lecture 16 — Fixing agent slop
- [x] Lecture 17 — Designing the star schema
- [x] Lecture 18 — Fixing Lecture 17's AI slop
- [x] Lecture 19 — Fixing more slop
- [x] Lecture 20 — Revision

## License

[MIT](LICENSE) © 2026 Aditya Bhatt
