"""Shared constants for the CSV header-comparison tool (Part B)."""

ENCODING = "utf-8-sig"  # strips a leading UTF-8 BOM if present
DELIMITER = ","

USAGE = "Usage: python compare_headers.py <expected_csv_path> <actual_csv_path>"

EXIT_OK = 0
EXIT_ERROR = 1
