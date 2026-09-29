"""Reads and splits the header row (first line only) of a CSV file (Part B).

Deliberately does not use Python's `csv` module — the input format is
simple (comma-separated, no quoting), and only the first line is ever read.
"""

import os

from .constants import DELIMITER, ENCODING
from .validator import HeaderReadError


def read_first_line(path):
    """Return the raw first line of `path`, without the trailing newline.

    Opening in text mode with universal newlines (the default) means
    both "\\n" and Windows "\\r\\n" line endings are normalized to "\\n"
    automatically. The "utf-8-sig" encoding strips a leading UTF-8 BOM,
    if present, automatically as well.

    Raises HeaderReadError if the file does not exist or contains no
    lines at all (a truly empty file).
    """
    if not os.path.isfile(path):
        raise HeaderReadError(f"file not found: {path}")

    try:
        with open(path, encoding=ENCODING, newline=None) as f:
            raw_line = f.readline()
    except UnicodeDecodeError as exc:
        raise HeaderReadError(f"could not decode file as {ENCODING}: {path} ({exc})") from exc

    if raw_line == "":
        raise HeaderReadError(f"file is empty: {path}")

    return raw_line.rstrip("\n")


def split_header(line):
    """Split a raw header line into trimmed column names."""
    return [field.strip() for field in line.split(DELIMITER)]
