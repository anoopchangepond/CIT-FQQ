"""Loads the sample data from answer.sql's header comment into an in-memory
SQLite database and runs the four Part A queries, so the queries can be
sanity-checked without a real database.

Usage:
    python sql/verify_sql.py
"""

import sqlite3

PRODUCTS_YESTERDAY = [
    (1001, "Coffee Mug", 12.50, "ACTIVE"),
    (1002, "Laptop Stand", 38.00, "ACTIVE"),
    (1003, "Wireless Mouse", 19.99, "ACTIVE"),
    (1004, "Old Keyboard", 29.99, "DISCONTINUED"),
    (1005, "Notebook", 4.50, "ACTIVE"),
    (1008, "Desk Lamp", 24.00, "ACTIVE"),
]

PRODUCTS_TODAY = [
    (1001, "Coffee Mug", 12.50, "ACTIVE"),
    (1002, "Laptop Stand", 35.00, "ACTIVE"),
    (1003, "Wireless Mouse", 21.99, "ACTIVE"),
    (1005, "Notebook", 4.50, "INACTIVE"),
    (1006, "Webcam", 59.00, "ACTIVE"),
    (1007, "USB Cable", 7.99, "ACTIVE"),
    (1008, "Desk Lamp", 24.00, "ACTIVE"),
]

SCHEMA = """
CREATE TABLE products_yesterday (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT,
    price REAL,
    status TEXT
);
CREATE TABLE products_today (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT,
    price REAL,
    status TEXT
);
"""

QUERIES = {
    "Task 1: Price Changes": """
        SELECT t.product_id, t.product_name, y.price AS old_price, t.price AS new_price
        FROM products_today t
        JOIN products_yesterday y ON y.product_id = t.product_id
        WHERE t.price != y.price;
    """,
    "Task 2: New Products": """
        SELECT t.product_id, t.product_name, t.price, t.status
        FROM products_today t
        WHERE NOT EXISTS (
            SELECT 1 FROM products_yesterday y WHERE y.product_id = t.product_id
        );
    """,
    "Task 3: Missing Products": """
        SELECT y.product_id, y.product_name, y.price, y.status
        FROM products_yesterday y
        WHERE NOT EXISTS (
            SELECT 1 FROM products_today t WHERE t.product_id = y.product_id
        );
    """,
    "Task 4: Status Changes": """
        SELECT y.product_id, y.product_name, y.status AS old_status, t.status AS new_status
        FROM products_yesterday y
        JOIN products_today t ON y.product_id = t.product_id
        WHERE y.status != t.status;
    """,
}

# Expected result sets, hand-derived from the sample data above, used to
# self-check that the queries produce the right answer.
EXPECTED = {
    "Task 1: Price Changes": [
        (1002, "Laptop Stand", 38.00, 35.00),
        (1003, "Wireless Mouse", 19.99, 21.99),
    ],
    "Task 2: New Products": [
        (1006, "Webcam", 59.00, "ACTIVE"),
        (1007, "USB Cable", 7.99, "ACTIVE"),
    ],
    "Task 3: Missing Products": [
        (1004, "Old Keyboard", 29.99, "DISCONTINUED"),
    ],
    "Task 4: Status Changes": [
        (1005, "Notebook", "ACTIVE", "INACTIVE"),
    ],
}


def main():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO products_yesterday VALUES (?, ?, ?, ?)", PRODUCTS_YESTERDAY)
    conn.executemany("INSERT INTO products_today VALUES (?, ?, ?, ?)", PRODUCTS_TODAY)

    all_passed = True
    for name, sql in QUERIES.items():
        actual = conn.execute(sql).fetchall()
        expected = EXPECTED[name]
        ok = actual == expected
        all_passed &= ok
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
        print(f"  expected: {expected}")
        print(f"  actual:   {actual}")

    conn.close()
    print()
    print("ALL QUERIES VERIFIED OK" if all_passed else "SOME QUERIES DID NOT MATCH EXPECTED OUTPUT")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
