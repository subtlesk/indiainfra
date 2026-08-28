"""Parsers for archived Grid-India (SRC-4) files.

Grid-India's website is an SPA backed by an undocumented JSON API — see
docs/kickoffs/2026-08-11-dig-deeper-2.md for the endpoint map (monthly report
archive reaches back to 2012-13). Parsers here read only the raw archive.
"""

import re
from datetime import date
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent


FY24_MONTH_FILES = [
    ("2023-04", "Monthly_Report_Apr_2023.pdf", 30),
    ("2023-05", "Monthly_Report_May_2023.pdf", 31),
    ("2023-06", "Monthly_Report_Jun_2023.pdf", 30),
    ("2023-07", "Monthly_Report_Jul_2023.pdf", 31),
    ("2023-08", "Monthly_Report_Aug_2023.pdf", 31),
    ("2023-09", "Monthly_Report_Sep_2023.pdf", 30),
    ("2023-10", "Monthly_Report_Oct_2023.pdf", 31),
    ("2023-11", "Monthly_Report_Nov_2023.pdf", 30),
    ("2023-12", "Monthly_Report_Dec_2023.pdf", 31),
    ("2024-01", "Monthly_Report_January_2024.pdf", 31),
    ("2024-02", "Monthly_Report_February_2024.pdf", 29),  # 2024 is a leap year
    ("2024-03", "Monthly_Report_Mar_2024.pdf", 31),
]

# separator varies across editions: ASCII hyphen, en-dash, unicode hyphens
_DATE_ROW = re.compile(r"^\s*(\d{1,2})\W[A-Za-z]{3}\W\d{2}\b(.*)$")


def _monthly_energy_met(path: Path, expected_days: int) -> float:
    """Sum the all-India daily TOTAL column (MU) of the 'ENERGY MET AT
    NATIONAL LEVEL' table in one monthly report."""
    def date_rows(text):
        out = {}
        for line in text.splitlines():
            m = _DATE_ROW.match(line)
            if m:
                nums = re.findall(r"\d+(?:\.\d+)?", m.group(2))
                if len(nums) >= 6:  # NR WR SR ER NER TOTAL
                    out[int(m.group(1))] = float(nums[-1])
        return out

    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages[:40]):
            t = page.extract_text() or ""
            if "ENERGY MET AT NATIONAL LEVEL" not in t:
                continue
            rows = date_rows(t)
            if len(rows) < expected_days and i + 1 < len(pdf.pages):
                # table may spill onto the next page (no repeated heading)
                rows.update(date_rows(pdf.pages[i + 1].extract_text() or ""))
            if not rows:
                continue
            assert len(rows) == expected_days, \
                f"{path.name}: {len(rows)} day rows, expected {expected_days}"
            total = sum(rows.values())
            assert 90_000 < total < 170_000, f"{path.name}: monthly total {total} MU implausible"
            return total
    raise ValueError(f"energy-met table not found or incomplete in {path.name}")


def energy_met_fy24() -> dict:
    """All-India energy met (MU), FY2023-24 = sum of 366 daily values across
    the 12 monthly reports. This is energy met at the state periphery -
    the working proxy for 'delivered to distribution' (basis labeled; it is
    not a physical transmission-loss measurement)."""
    monthly, total = {}, 0.0
    for ym, fname, days in FY24_MONTH_FILES:
        path = ROOT / "data/raw/SRC-4/monthly" / fname
        v = _monthly_energy_met(path, days)
        monthly[ym] = round(v)
        total += v
    return {"energy_met_MU": round(total), "monthly_MU": monthly,
            "period": "FY2023-24",
            "source_file": "data/raw/SRC-4/monthly/ (12 monthly reports)"}


def peak_demand_met_fy24() -> dict:
    """All-India maximum demand met (MW) with date, from the 'All Time Highest'
    table of the Monthly Report for March 2024.

    As of 31-03-2024 the all-time record was set on 01-09-2023, i.e. inside
    FY2023-24, so it doubles as the fiscal-year peak. The parser asserts that.
    Note: this is demand MET — unmet shortage is not included.
    """
    path = ROOT / "data/raw/SRC-4/monthly/Monthly_Report_Mar_2024.pdf"
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            if "ALL TIME HIGHEST" not in t:
                continue
            lines = t.splitlines()
            for j, line in enumerate(lines):
                if line.strip() == "All India" and j > 0:
                    nums = re.findall(r"\d{4,6}", lines[j - 1])
                    dm = re.match(r"\s*(\d{2})-(\d{2})-(\d{4})", lines[j + 1])
                    if nums and dm:
                        peak = float(nums[0])
                        d = date(int(dm.group(3)), int(dm.group(2)), int(dm.group(1)))
                        assert date(2023, 4, 1) <= d <= date(2024, 3, 31), \
                            f"record date {d} outside FY2023-24 - fiscal-year peak logic no longer holds"
                        return {"peak_met_MW": peak, "on": d.isoformat(),
                                "source_file": path.relative_to(ROOT).as_posix()}
    raise ValueError("All India row not found in All Time Highest table")
