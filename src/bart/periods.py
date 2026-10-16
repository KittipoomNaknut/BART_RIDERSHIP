PERIODS = {
    "Jan-Apr 2019": ("2019-01-01", "2019-04-30"),
    "Jan-Apr 2023": ("2023-01-01", "2023-04-30"),
}
BEFORE = "Jan-Apr 2019"
AFTER = "Jan-Apr 2023"


def period_case(column="date"):
    lines = ["CASE"]
    for label, (start, end) in PERIODS.items():
        lines.append(f"    WHEN {column} BETWEEN DATE '{start}' AND DATE '{end}' THEN '{label}'")
    lines.append("END")
    return "\n".join(lines)
