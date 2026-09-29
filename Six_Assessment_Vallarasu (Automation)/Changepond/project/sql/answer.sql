-- Sample data used for verification:
--
-- products_yesterday:
--   1001 | Coffee Mug     | 12.50 | ACTIVE
--   1002 | Laptop Stand   | 38.00 | ACTIVE
--   1003 | Wireless Mouse | 19.99 | ACTIVE
--   1004 | Old Keyboard   | 29.99 | DISCONTINUED
--   1005 | Notebook       |  4.50 | ACTIVE
--   1008 | Desk Lamp      | 24.00 | ACTIVE
--
-- products_today:
--   1001 | Coffee Mug     | 12.50 | ACTIVE
--   1002 | Laptop Stand   | 35.00 | ACTIVE
--   1003 | Wireless Mouse | 21.99 | ACTIVE
--   1005 | Notebook       |  4.50 | INACTIVE
--   1006 | Webcam         | 59.00 | ACTIVE
--   1007 | USB Cable      |  7.99 | ACTIVE
--   1008 | Desk Lamp      | 24.00 | ACTIVE

-- ------------------------------------------------------------
-- Task 1: Price Changes
-- products whose price changed from yesterday to today
-- Columns: product_id, product_name, old_price, new_price
-- ------------------------------------------------------------
SELECT 
    t.product_id,
    t.product_name,
    y.price AS old_price,
    t.price As new_price
FROM 
    products_today t
JOIN
    products_yesterday y ON y.product_id = t.product_id
WHERE t.price != y.price;


-- ------------------------------------------------------------
-- Task 2: New Products
-- Products present in products_today but not in products_yesterday.
-- Columns: product_id, product_name, price, status
-- ------------------------------------------------------------
SELECT
    t.product_id,
    t.product_name,
    t.price,
    t.status
FROM products_today t
WHERE NOT EXISTS (
    SELECT 1
    FROM products_yesterday y
    WHERE y.product_id = t.product_id
);

-- ------------------------------------------------------------
-- Task 3: Missing Products
-- Products present in products_yesterday but not in products_today.
-- Columns: product_id, product_name, price, status
-- ------------------------------------------------------------
SELECT
    y.product_id,
    y.product_name,
    y.price,
    y.status
FROM products_yesterday y
WHERE NOT EXISTS (
    SELECT 1
    FROM products_today t
    WHERE t.product_id = y.product_id
);

-- ------------------------------------------------------------
-- Task 4: Status Changes
-- Products that exist in both tables but whose status differs.
-- Columns: product_id, product_name, old_status, new_status
-- ------------------------------------------------------------
SELECT
    y.product_id,
    y.product_name,
    y.status AS old_status,
    t.status AS new_status
FROM products_yesterday y
JOIN products_today   t ON y.product_id = t.product_id
WHERE y.status != t.status;


-- ============================================================
-- Task 5: Short Explanation
-- ============================================================
--
-- 1) Why INNER JOIN / NOT EXISTS, and not something else?
--    - Tasks 1 and 4 need a row from BOTH tables (to compare old vs new
--      value), so an INNER JOIN on product_id is the natural fit: it
--      only returns product_ids present on both sides, which is exactly
--      the set we need to compare. A LEFT JOIN would also work but would
--      need an extra "IS NOT NULL" filter to drop the unmatched side, so
--      INNER JOIN is simpler and communicates intent more clearly.
--    - Tasks 2 and 3 need rows that exist on ONE side only, so I used
--      NOT EXISTS (an anti-join). NOT EXISTS is preferred over
--      "LEFT JOIN ... WHERE right.id IS NULL" because it reads as "this
--      id has no match" directly, and it also behaves correctly if the
--      other table ever has duplicate product_ids (a LEFT JOIN would
--      fan out duplicate rows before the NULL filter removes them;
--      NOT EXISTS just checks existence, so duplicates on the other side
--      don't affect the result). NOT IN was avoided because NOT IN
--      silently returns zero rows if the subquery contains even a
--      single NULL product_id — a classic SQL trap.
--
-- 2) What would change if product_id was not unique?
--    - The JOINs in Tasks 1 and 4 would produce a cartesian-style fan-out:
--      every yesterday-row for a given product_id would be joined against
--      every today-row with the same product_id, so a product with 2 rows
--      on each side would emit 4 joined rows instead of 1, and price/status
--      "changes" could be reported multiple times or based on the wrong
--      pairing of rows.
--    - The NOT EXISTS queries (Tasks 2/3) would still be functionally
--      correct for existence checks (EXISTS only cares whether at least one
--      match exists), but the query would no longer guarantee "one output
--      row per product" — you'd want to add a surrogate key (e.g. an
--      auto-increment id per snapshot) or aggregate first (e.g. dedupe/
--      pick the latest row per product_id via ROW_NUMBER()) before joining,
--      so each product is represented exactly once in the comparison.
--
-- 3) What issue could happen if price or status can be NULL?
--    - `y.price <> t.price` (and `y.status <> t.status`) uses standard
--      three-valued SQL logic: any comparison involving NULL evaluates to
--      UNKNOWN, not TRUE or FALSE. A row where price went from 12.50 to
--      NULL (or NULL to 12.50) would be silently EXCLUDED from the
--      "changed" result, because `12.50 <> NULL` is UNKNOWN, not TRUE —
--      so a real, meaningful change (a price being cleared/unset) would
--      never be flagged. That's a genuine testing risk: a bug that sets
--      price to NULL instead of updating it would pass this check as "no
--      change detected".
--    - Fix: use a NULL-safe comparison, e.g.
--        WHERE y.price IS DISTINCT FROM t.price   -- Postgres/SQLite
--      or a portable equivalent:
--        WHERE (y.price <> t.price)
--           OR (y.price IS NULL AND t.price IS NOT NULL)
--           OR (y.price IS NOT NULL AND t.price IS NULL)
--      The same applies to the status comparison in Task 4.