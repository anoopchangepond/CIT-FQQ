"""CLI entry point for the CSV header-comparison tool (Part B).

Usage:
    python compare_headers.py <expected_csv_path> <actual_csv_path>

Reads only the first line of each file (no CSV parsing library), trims
whitespace on each header, and reports headers only in the first file,
only in the second file, common headers, and whether the common headers
appear in the same relative order in both files.

Exit codes:
    0 - ran successfully (the report is printed regardless of whether the
        headers matched — a mismatch is a normal result, not an error)
    1 - one of the handled error cases: missing/wrong number of arguments,
        file not found, empty file, or a header row with no usable column
        names. A clear message is printed to stderr; no stack trace.
"""

import sys

from .comparator import compare_headers, format_report
from .constants import EXIT_ERROR, EXIT_OK, USAGE
from .csv_reader import read_first_line, split_header
from .validator import HeaderReadError, validate_header


def load_header(path):
    line = read_first_line(path)
    header = split_header(line)
    validate_header(header, source=path)
    return header


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv

    if len(argv) != 2:
        print(f"Error: expected 2 file path arguments, got {len(argv)}.", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        return EXIT_ERROR

    expected_path, actual_path = argv

    try:
        first = load_header(expected_path)
        second = load_header(actual_path)
    except HeaderReadError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    result = compare_headers(first, second)
    print(format_report(result, expected_path, actual_path))

    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
