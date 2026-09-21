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
2. Open a worksheet and run the end-state SQL files in order: Lecture 05, 06, 07, then 08. Each one builds on the last.
3. In Lecture 08, upload the four CSVs to the stage through the Snowsight UI (Catalog → `ORDERIQ_DB` → `RAW` → Stages → `ORDERIQ_STAGE` → **+ Files**) before running the `LIST` and `SELECT` queries.

That sequence gives you:

- **Warehouse** `ORDERIQ_WH` — XSMALL, auto-suspends after 60s so you don't burn credits
- **Database** `ORDERIQ_DB` with schemas `RAW`, `STAGING`, `ANALYTICS`
- **File format** `FF_CSV` in `RAW`, configured to handle the messiness in the source files
- **Named stage** `ORDERIQ_STAGE` in `RAW`, with `FF_CSV` attached and a directory table enabled — the landing zone for the raw CSVs, queryable before any table exists

Run the SQL yourself rather than pasting it wholesale — the comments in each file explain *why* every option is set the way it is.

## Course progress

- [x] Lecture 3 — How Snowflake works: storage, compute and credits
- [x] Lecture 4 — Meet the dataset
- [x] Lecture 5 — Creating your first warehouse
- [x] Lecture 6 — Creating the database and schemas
- [x] Lecture 7 — What a file format is
- [x] Lecture 8 — Stages: Snowflake's drop zone

## License

[MIT](LICENSE) © 2026 Aditya Bhatt
