"""Header-row validation for the CSV header-comparison tool (Part B)."""


class HeaderReadError(Exception):
    """Raised for any error condition Part B must handle with a clear
    message and exit code 1: missing/wrong args, file not found, empty
    file, or a header row with no usable column names.
    """


def validate_header(header, source):
    """Raise HeaderReadError if none of the header fields are usable
    (i.e. the header row exists but every field is blank after trimming).
    """
    if not any(field for field in header):
        raise HeaderReadError(f"header row has no usable column names: {source}")
