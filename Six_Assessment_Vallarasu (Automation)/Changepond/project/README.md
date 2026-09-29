# SDET Take-Home

A four-part SDET exercise: a SQL data-comparison task, a CSV header-comparison
CLI tool with its test suite, an API test-design exercise, and this
documentation.

## Project structure

```
├── README.md
├── AI_TRANSCRIPT.md
├── requirements.txt
├── pytest.ini
├── sql/
│   ├── answer.sql           # Part A: SQL queries + written explanation
│   └── verify_sql.py        # Part A: SQLite sanity-check for the queries
├── data/
│   ├── expected_orders.csv  # sample "expected" header/rows for Part B
│   └── actual_orders.csv    # sample "actual" header/rows for Part B
├── src/
│   ├── compare_headers.py   # CLI entry point (main())
│   ├── csv_reader.py        # reads/parses the header row of a CSV file
│   ├── comparator.py        # compare_headers() + format_report()
│   ├── validator.py         # HeaderReadError + header-row validation
│   └── constants.py         # shared constants (encoding, delimiter, exit codes)
└── tests/
    ├── test_compare_headers.py  # Part B: 10 unit/error-handling/e2e tests
    └── test_api_orders.py       # Part C: 5 designed test cases + 1 automated test
```

---

## 1. Language used

Python 3 (developed/tested on Python 3.13). Part B's tool uses only the
standard library (deliberately no CSV parsing library — see Assumptions).
Part C's test uses `requests` + `pytest`.

## 2. How to run the CSV comparison tool (Part B)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -r requirements.txt

python -m src.compare_headers data/expected_orders.csv data/actual_orders.csv
```

It reads only the first line of each file and compares the two header rows,
reporting headers only in the first file, only in the second, the common
headers, and whether the common headers appear in the same relative order.
Whitespace is trimmed on every header, and Windows `\r\n` line endings / a
UTF-8 BOM are handled transparently.

Exit codes: `0` = ran successfully (a header mismatch is a normal result,
not an error); `1` = a handled error — missing/wrong number of arguments,
file not found, empty file, or a header row with no usable column names.
Errors print a clear message to stderr, never a stack trace.

Sample run against the two fixtures in `data/`:

```
Only in data/expected_orders.csv:
amount
created_at
country

Only in data/actual_orders.csv:
total_amount
processed_at
country_code

Common headers:
order_id
customer_id
currency
status

Common headers in same relative order:
true
```

## 3. How to run the tests

```bash
pytest                                  # everything (11 tests)
pytest tests/test_compare_headers.py -v # Part B only (10 tests)
pytest tests/test_api_orders.py -v      # Part C only (1 automated test)
python sql/verify_sql.py                # Part A: SQL sanity-check (not pytest)
```

## 4. SQL answers (Part A)

Full queries and the written explanation (join vs. `NOT EXISTS` rationale,
what changes if `product_id` isn't unique, and the NULL-comparison trap) are
in [`sql/answer.sql`](sql/answer.sql). The four queries:

```sql
-- Task 1: Price Changes
SELECT t.product_id, t.product_name, y.price AS old_price, t.price AS new_price
FROM products_today t
JOIN products_yesterday y ON y.product_id = t.product_id
WHERE t.price != y.price;

-- Task 2: New Products
SELECT t.product_id, t.product_name, t.price, t.status
FROM products_today t
WHERE NOT EXISTS (
    SELECT 1 FROM products_yesterday y WHERE y.product_id = t.product_id
);

-- Task 3: Missing Products
SELECT y.product_id, y.product_name, y.price, y.status
FROM products_yesterday y
WHERE NOT EXISTS (
    SELECT 1 FROM products_today t WHERE t.product_id = y.product_id
);

-- Task 4: Status Changes
SELECT y.product_id, y.product_name, y.status AS old_status, t.status AS new_status
FROM products_yesterday y
JOIN products_today t ON y.product_id = t.product_id
WHERE y.status != t.status;
```

**Verified sample output** (`python sql/verify_sql.py`, run against the
sample data given in the exercise, loaded into an in-memory SQLite DB):

```
[PASS] Task 1: Price Changes
  expected: [(1002, 'Laptop Stand', 38.0, 35.0), (1003, 'Wireless Mouse', 19.99, 21.99)]
  actual:   [(1002, 'Laptop Stand', 38.0, 35.0), (1003, 'Wireless Mouse', 19.99, 21.99)]
[PASS] Task 2: New Products
  expected: [(1006, 'Webcam', 59.0, 'ACTIVE'), (1007, 'USB Cable', 7.99, 'ACTIVE')]
  actual:   [(1006, 'Webcam', 59.0, 'ACTIVE'), (1007, 'USB Cable', 7.99, 'ACTIVE')]
[PASS] Task 3: Missing Products
  expected: [(1004, 'Old Keyboard', 29.99, 'DISCONTINUED')]
  actual:   [(1004, 'Old Keyboard', 29.99, 'DISCONTINUED')]
[PASS] Task 4: Status Changes
  expected: [(1005, 'Notebook', 'ACTIVE', 'INACTIVE')]
  actual:   [(1005, 'Notebook', 'ACTIVE', 'INACTIVE')]

ALL QUERIES VERIFIED OK
```

## 5. API test cases (Part C — `GET /api/orders/{order_id}`)

5 test cases designed for this endpoint (full detail, including exact
input/expected-result/why-useful text, in the [`tests/test_api_orders.py`](tests/test_api_orders.py)
module docstring):

| # | Test name | Input | Expected result | Why useful |
|---|---|---|---|---|
| 1 | `test_get_order_success_returns_200_and_correct_fields` | `GET /api/orders/ORD-1001` (existing order) | HTTP 200; all documented fields present, `status` reflects real state | Covers the everyday path — if this breaks, every consumer breaks |
| 2 | `test_get_order_unknown_id_returns_404` | `GET /api/orders/ORD-9999` (valid format, doesn't exist) | HTTP 404 with a structured error body, not 200/500 | Missing-resource is one of the most common real-world cases |
| 3 | `test_get_order_malformed_or_malicious_id_returns_400_safely` | `GET /api/orders/<bad id>` — empty, path traversal, or SQL-injection-style payload | HTTP 400, generic error body, no stack trace/DB error leaked | Security-relevant: checks input validation actually rejects hostile input |
| 4 | `test_get_order_response_matches_schema_and_types` | `GET /api/orders/ORD-1001` (existing order) | Exactly the documented fields, correct types (`amount` positive number, `currency` 3-letter, `status` in enum, `created_at` ISO-8601 UTC) | Catches consumer-breaking contract changes that a single-field check misses |
| 5 | `test_get_order_responds_within_sla` | `GET /api/orders/ORD-1001` (normal request) | Responds within the agreed SLA (e.g. p95 < 300ms server-side) | A correct-but-slow response still breaks UX/downstream timeouts |

**Implemented as real automated code** (Task 2 of the brief — the only case
required to be coded): `test_get_order_returns_200_and_status_paid` asserts
`GET /api/orders/ORD-1001` returns HTTP 200 and `status == "PAID"`, using
`requests` with `requests.get` monkeypatched to a fake response (no real API
is called, per the brief).

## 6. Assumptions made

- Part B treats the CSV **header row only** — no row-level data diffing is
  in scope, and only the first line of each file is ever read.
- Part B deliberately avoids the `csv` module — the input is simple,
  unquoted comma-separated values, so a plain `str.split(",")` plus a
  per-field `.strip()` is enough, per the exercise's instructions.
- CSV reads default to `utf-8-sig` so a BOM from an Excel export doesn't get
  treated as part of the first column name; opening in text mode with
  universal newlines normalizes `\r\n` to `\n` without extra code.
- A header mismatch in Part B is a normal, successful result (exit `0`), not
  an error — exit code `1` is reserved for the four handled error cases.
- Part C's automated test is written against the documented contract in the
  prompt; no assumptions are made about a live service, so a real base URL
  could be substituted later, replacing the monkeypatched `requests.get`
  with an actual call against a test environment.
- SQL Part A assumes `product_id` is unique per snapshot table (see
  `sql/answer.sql` for what changes if that doesn't hold) and that `price`/
  `status` are non-NULL in the sample data (see the same file for the
  NULL-comparison risk if they aren't).

## 7. AI usage statement

AI (Claude Code, running Claude Sonnet 5) was used for this exercise, for
Part B's implementation/tests, Part C's implementation/tests, `sql/verify_sql.py`,
and this documentation. **The full relevant conversation — actual prompts
and actual AI responses relied on — is in [`AI_TRANSCRIPT.md`](AI_TRANSCRIPT.md).**
Part A's SQL queries and written explanation were authored independently of
the AI session.

---

## Candidate acknowledgement

By submitting this exercise, I confirm that:

1. I have followed the AI usage rules.
2. If I used AI, I have included the full relevant AI transcript or
   equivalent usage record.
3. I understand the submitted solution.
4. I am able to explain, modify, and debug the solution during the
   interview.
5. I understand that failure to disclose AI use, or inability to explain
   the submitted work, may result in rejection.
