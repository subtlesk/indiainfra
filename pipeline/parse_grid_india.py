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
