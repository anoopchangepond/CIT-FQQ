"""Part B tests: CSV header-comparison tool.

10 tests, matching the coverage the exercise calls for:
  - identical headers                              (1)
  - mismatched headers on both sides                (1)
  - reordered headers                                (1)
  - whitespace around headers                        (1)
  - Windows \\r\\n line endings                       (1)
  - all four error cases                             (4)
  - end-to-end test against the sample files         (1)
"""

import subprocess
import sys
from pathlib import Path

from src.comparator import compare_headers
from src.csv_reader import read_first_line, split_header

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "src.compare_headers", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# Comparison logic
# ---------------------------------------------------------------------------

def test_identical_headers_are_fully_common_and_in_order():
    header = ["order_id", "customer_id", "amount", "status"]

    result = compare_headers(header, list(header))

    assert result["only_in_first"] == []
    assert result["only_in_second"] == []
    assert result["common"] == header
    assert result["same_order"] is True


def test_mismatched_headers_on_both_sides_are_reported():
    first = ["order_id", "customer_id", "amount", "created_at", "country"]
    second = ["order_id", "customer_id", "total_amount", "processed_at", "country_code"]

    result = compare_headers(first, second)

    assert result["only_in_first"] == ["amount", "created_at", "country"]
    assert result["only_in_second"] == ["total_amount", "processed_at", "country_code"]
    assert result["common"] == ["order_id", "customer_id"]


def test_reordered_common_headers_are_flagged_as_not_same_order():
    first = ["order_id", "customer_id", "currency", "status"]
    second = ["order_id", "status", "customer_id", "currency"]

    result = compare_headers(first, second)

    assert result["only_in_first"] == []
    assert result["only_in_second"] == []
    assert result["same_order"] is False


# ---------------------------------------------------------------------------
# Header-line parsing
# ---------------------------------------------------------------------------

def test_whitespace_around_headers_is_trimmed():
    line = "  order_id ,customer_id,  amount ,currency  "

    assert split_header(line) == ["order_id", "customer_id", "amount", "currency"]


def test_windows_crlf_line_ending_does_not_leak_into_header(tmp_path):
    csv_file = tmp_path / "crlf.csv"
    csv_file.write_bytes(b"order_id,customer_id,amount\r\n1,C001,100.50\r\n")

    line = read_first_line(str(csv_file))
    header = split_header(line)

    assert header == ["order_id", "customer_id", "amount"]
    assert "\r" not in header[-1]


# ---------------------------------------------------------------------------
# Error handling (Coding Task 3) -- exercised through the real CLI
# ---------------------------------------------------------------------------

def test_cli_errors_with_missing_file_path_argument():
    proc = run_cli(str(DATA_DIR / "expected_orders.csv"))  # only 1 of 2 required args

    assert proc.returncode == 1
    assert "Error" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_cli_errors_when_file_does_not_exist():
    proc = run_cli(str(DATA_DIR / "does_not_exist.csv"), str(DATA_DIR / "actual_orders.csv"))

    assert proc.returncode == 1
    assert "not found" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_cli_errors_on_empty_csv_file(tmp_path):
    empty_file = tmp_path / "empty.csv"
    empty_file.write_bytes(b"")

    proc = run_cli(str(empty_file), str(DATA_DIR / "actual_orders.csv"))

    assert proc.returncode == 1
    assert "empty" in proc.stderr
    assert "Traceback" not in proc.stderr


def test_cli_errors_when_header_row_has_no_usable_headers(tmp_path):
    blank_header_file = tmp_path / "blank_header.csv"
    blank_header_file.write_bytes(b" , ,  \r\n1,2,3\r\n")

    proc = run_cli(str(blank_header_file), str(DATA_DIR / "actual_orders.csv"))

    assert proc.returncode == 1
    assert "no usable column names" in proc.stderr
    assert "Traceback" not in proc.stderr


# ---------------------------------------------------------------------------
# End-to-end against the real sample fixtures
# ---------------------------------------------------------------------------

def test_cli_end_to_end_against_sample_files():
    proc = run_cli(str(DATA_DIR / "expected_orders.csv"), str(DATA_DIR / "actual_orders.csv"))

    assert proc.returncode == 0
    assert "amount" in proc.stdout and "created_at" in proc.stdout and "country" in proc.stdout
    assert "total_amount" in proc.stdout and "processed_at" in proc.stdout and "country_code" in proc.stdout
    assert "order_id" in proc.stdout and "customer_id" in proc.stdout
    assert "currency" in proc.stdout and "status" in proc.stdout
    assert "Common headers in same relative order:" in proc.stdout
    assert "true" in proc.stdout
