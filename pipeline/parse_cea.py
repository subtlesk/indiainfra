"""Parsers for archived CEA files. Each parser returns values with provenance.

Parsers read ONLY from the raw archive, never from the network.
"""

import re
from pathlib import Path

import openpyxl
import pdfplumber

ROOT = Path(__file__).resolve().parent.parent


def installed_capacity_fy24() -> dict:
    """All-India installed capacity (MW), utilities, as on 31.03.2024.

    Source sheet layout: region x sector matrix; the grand-total row is the
    'Total' row whose grand total exceeds 350 GW (only one such row exists).
    """
    path = ROOT / "data/raw/SRC-1/2024-03/IC_Mar_2024_allocation_wise.xlsx"
    ws = openpyxl.load_workbook(path, data_only=True)["IC (Value)"]
    for row in ws.iter_rows(values_only=True):
        cells = [c for c in row if c is not None]
        nums = [c for c in cells if isinstance(c, (int, float))]
        if "Total" in [str(c).strip() for c in cells] and nums and max(nums) > 350_000:
            coal, lignite, gas, diesel, thermal, nuclear, hydro, res, res_total, grand = nums
            return {
                "value_MW": round(grand, 1),
                "breakdown_MW": {
                    "coal": round(coal, 1),
                    "lignite": round(lignite, 1),
                    "gas": round(gas, 1),
                    "diesel": round(diesel, 1),
                    "nuclear": round(nuclear, 1),
                    "hydro_large": round(hydro, 1),
                    "res_incl_small_hydro": round(res, 1),
                },
                "as_of": "2024-03-31",
                "source_file": str(path.relative_to(ROOT)),
            }
    raise ValueError("grand-total row not found — CEA changed the sheet layout")


def _table_rows(pdf_path: Path, page_idx: int) -> list[str]:
    with pdfplumber.open(pdf_path) as pdf:
        return (pdf.pages[page_idx].extract_text() or "").splitlines()


def gross_generation_fy24() -> dict:
    """FY2023-24 gross generation (GWh), utilities, from Growth Book Table 3."""
    path = ROOT / "data/raw/SRC-1/growth-book/Growth_Book_2024.pdf"
    for line in _table_rows(path, 28):  # Table 3 is on pdf page 29
        if "2023-24" in line:
            # strip the year label first: '2023-24' would otherwise tokenise as numbers
            clean = line.replace("2023-24", "")
            nums = [float(n.replace(",", "")) for n in re.findall(r"[\d,]+", clean)]
            coal_lignite, gas, diesel, thermal, hydro, nuclear, res, total = nums[1:9]  # nums[0] is the serial no.
            assert abs((coal_lignite + gas + diesel) - thermal) < 2, "thermal breakdown mismatch"
            return {
                "value_GWh": total,
                "breakdown_GWh": {
                    "coal_lignite": coal_lignite,
                    "gas": gas,
                    "diesel": diesel,
                    "hydro_large": hydro,
                    "nuclear": nuclear,
                    "res": res,
                },
                "period": "FY2023-24",
                "source_file": str(path.relative_to(ROOT)),
            }
    raise ValueError("FY2023-24 row not found in Growth Book Table 3")


def _fy_end_year(label: str) -> int | None:
    """'1955-56 (End of the 1st Plan)' -> 1956; '31.03.61' -> 1961; '1947' -> 1947."""
    m = re.search(r"(\d{4})-(\d{2})", label)
    if m:
        century = int(m.group(1)) // 100 * 100
        end = int(m.group(2))
        return century + end if end >= int(m.group(1)) % 100 else century + 100 + end
    m = re.search(r"31\.(?:03|12)\.(\d{2,4})", label)
    if m:
        y = int(m.group(1))
        return y if y > 1900 else (1900 + y if y >= 40 else 2000 + y)
    m = re.fullmatch(r"\s*(19\d\d|20\d\d)\s*", label)
    return int(m.group(1)) if m else None


def _history_rows(page_idx: int, n_values: int) -> list[tuple[int, list[float]]]:
    """Parse a Growth Book history table: serial, year label, n numeric columns."""
    path = ROOT / "data/raw/SRC-1/growth-book/Growth_Book_2024.pdf"
    out = []
    for line in _table_rows(path, page_idx):
        m = re.match(r"\s*\d{1,2}\s+(.*)", line)
        if not m:
            continue
        rest = m.group(1)
        label = re.split(r"\s{1,}(?=[\d,]+(?:\.\d+)?(?:\s|$))", rest, maxsplit=1)[0]
        nums = [float(n.replace(",", "")) for n in re.findall(r"[\d,]+(?:\.\d+)?", rest.replace(label, "", 1))]
        year = _fy_end_year(label)
        if year and len(nums) >= n_values:
            out.append((year, nums[-n_values:]))
    years = [y for y, _ in out]
    assert years == sorted(years) and len(set(years)) == len(years), f"year sequence broken: {years}"
    return out


def capacity_series() -> list[dict]:
    """Installed capacity by mode 1947-2024 (MW), Growth Book Table 2 (pdf p17).

    Columns: coal/lignite, gas, diesel, thermal_total, nuclear, hydro,
    res(MNRE), res_total(=hydro+res), grand_total.
    """
    rows = []
    for year, n in _history_rows(16, 9):
        coal, gas, diesel, thermal, nuclear, hydro, res, _res_tot, total = n
        rows.append({"year": year, "thermal": thermal, "hydro": hydro,
                     "nuclear": nuclear, "res": res, "total": total})
    assert rows[0]["year"] == 1947 and rows[-1]["year"] == 2024, [rows[0], rows[-1]]
    return rows


def generation_series() -> list[dict]:
    """Gross generation by mode 1947 to FY2023-24 (GWh), Growth Book Table 3 (pdf p29).

    Columns: coal/lignite, gas, diesel, thermal_total, hydro, nuclear, res, total.
    """
    rows = []
    for year, n in _history_rows(28, 8):
        _cl, _gas, _diesel, thermal, hydro, nuclear, res, total = n
        rows.append({"year": year, "thermal": thermal, "hydro": hydro,
                     "nuclear": nuclear, "res": res, "total": total})
    assert rows[0]["year"] == 1947 and rows[-1]["year"] == 2024, [rows[0], rows[-1]]
    return rows


def captive_generation_fy24() -> dict:
    """FY2023-24 captive generation (GWh, plants >=0.5 MW), Growth Book Table 7.

    Marked provisional by CEA ('@' suffix on the year label).
    """
    path = ROOT / "data/raw/SRC-1/growth-book/Growth_Book_2024.pdf"
    for line in _table_rows(path, 63):  # Table 7 is on pdf page 64
        if "2023-24" in line:
            nums = [float(n.replace(",", "")) for n in re.findall(r"[\d,.]+", line.replace("2023-24@", ""))]
            total = nums[-1]
            return {
                "value_GWh": total,
                "provisional": True,
                "period": "FY2023-24",
                "source_file": str(path.relative_to(ROOT)),
            }
    raise ValueError("FY2023-24 row not found in Growth Book Table 7")
