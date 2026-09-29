"""Compares two CSV header rows and formats the console report (Part B)."""


def compare_headers(first, second):
    """Compare two header lists.

    Returns a dict:
      only_in_first  - headers in `first` but not in `second`
      only_in_second - headers in `second` but not in `first`
      common         - headers present in both, in `first`'s order
      same_order     - True if the common headers appear in the same
                       relative order in both lists
    """
    first_set = set(first)
    second_set = set(second)

    only_in_first = [h for h in first if h not in second_set]
    only_in_second = [h for h in second if h not in first_set]

    common_in_first_order = [h for h in first if h in second_set]
    common_in_second_order = [h for h in second if h in first_set]
    same_order = common_in_first_order == common_in_second_order

    return {
        "only_in_first": only_in_first,
        "only_in_second": only_in_second,
        "common": common_in_first_order,
        "same_order": same_order,
    }


def format_report(result, first_label, second_label):
    """Render a compare_headers() result as the console report."""
    lines = []

    lines.append(f"Only in {first_label}:")
    lines.extend(result["only_in_first"] or ["(none)"])
    lines.append("")

    lines.append(f"Only in {second_label}:")
    lines.extend(result["only_in_second"] or ["(none)"])
    lines.append("")

    lines.append("Common headers:")
    lines.extend(result["common"] or ["(none)"])
    lines.append("")

    lines.append("Common headers in same relative order:")
    lines.append("true" if result["same_order"] else "false")

    return "\n".join(lines)
