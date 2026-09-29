---
name: sql-review
description: Review SQL queries for correctness, safety and readability before they run. Use when the user shares a SQL query, asks to check, review or optimise SQL, or before running any SQL that changes or deletes data.
---

# SQL Review

Review the query against this checklist, in this order.

## 1. Correctness
- Joins use the right keys. Compare row counts before and after each join to catch duplicates (fan-out).
- Filters match the business rule the user stated. If no rule was stated, ask instead of assuming.
- NULLs are handled on purpose (COUNT(col) vs COUNT(*), NULLs in WHERE and joins).

## 2. Safety
- Never run DELETE, UPDATE, DROP or TRUNCATE without showing the statement and asking first.
- Add LIMIT to exploratory queries on large tables.

## 3. Readability
- Uppercase keywords, one clause per line, meaningful aliases.
- Prefer CTEs over deeply nested subqueries.

## 4. Performance
- Select only the columns needed. Filter as early as possible.
- Avoid wrapping filtered columns in functions.

## Output format
- Verdict: OK or Needs changes
- Issues: numbered, most serious first
- Fixed query
- One line on how to verify the result
