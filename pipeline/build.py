"""Build the chain dataset for the dashboard.

Reads the raw archive + hand-verified figures, assembles the FY2023-24 national
chain per chain-specification-v0.2.md, enforces invariants, writes
site/data/chain.json. Any invariant violation exits non-zero and fails CI.

Usage: python -m pipeline.build
"""

import json
import sys
from pathlib import Path

from . import parse_cea, parse_grid_india

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "data" / "chain.json"
OUT_SERIES = ROOT / "site" / "data" / "series.json"

FY24_HOURS = 8784  # FY2023-24 (Apr 2023 - Mar 2024) contains 29 Feb 2024


def build() -> dict:
    s1 = parse_cea.installed_capacity_fy24()
    s4 = parse_cea.gross_generation_fy24()
    captive = parse_cea.captive_generation_fy24()
    peak = parse_grid_india.peak_demand_met_fy24()
    aux = parse_cea.aux_consumption_fy24()

    # S5 identity: conventional gross (Growth-Book basis) x (1 - actual aux
    # rate) + RES (net~gross by CEA convention). Bhutan imports excluded on
    # both sides - they enter at S6 as a side flow.
    conv_gross = s4["breakdown_GWh"]["coal_lignite"] + s4["breakdown_GWh"]["gas"] + \
        s4["breakdown_GWh"]["diesel"] + s4["breakdown_GWh"]["hydro_large"] + s4["breakdown_GWh"]["nuclear"]
    s5_value = round(conv_gross * (1 - aux["aux_rate"]) + s4["breakdown_GWh"]["res"], 0)
    pfc = json.loads((ROOT / "data/verified/pfc_fy2024.json").read_text())

    atc = json.loads(json.dumps(pfc))  # copy

    # Implied utilisation vs INSTALLED capacity. Deliberately labeled: the true
    # bridge divides by DISPATCHED capacity (S3), which has no parser yet.
    # Using installed here and saying so is the P-06 lesson made visible.
    implied_utilisation = s4["value_GWh"] * 1000 / (s1["value_MW"] * FY24_HOURS)

    stages = [
        {"id": "S0", "name": "Pipeline", "unit": "MW", "status": "pending",
         "note": "Needs GEM + PARIVESH + CEA Broad Status fusion (fuzzy-match spike first)."},
        {"id": "S1", "name": "Installed capacity", "unit": "MW", "status": "populated",
         "value": s1["value_MW"], "breakdown": s1["breakdown_MW"], "grade": "A",
         "as_of": s1["as_of"], "source": "SRC-1", "source_file": s1["source_file"]},
        {"id": "S2", "name": "Available capacity", "unit": "MW", "status": "pending",
         "note": "Needs NPP daily outage parsing (PDF at scale)."},
        {"id": "S3", "name": "Dispatched", "unit": "MW", "status": "partial",
         "metrics": {"peak_met_MW": peak["peak_met_MW"], "peak_met_on": peak["on"]},
         "grade": "A", "period": "FY2023-24", "source": "SRC-4",
         "source_file": peak["source_file"],
         "note": "Peak demand MET (unmet shortage excluded; CEA's peak-demand figure comes with the S2-S3 gap). Average dispatch and monthly resolution need the full monthly-report archive (2012-13 onward, now API-reachable)."},
        {"id": "S4", "name": "Gross generation", "unit": "GWh", "status": "populated",
         "value": s4["value_GWh"], "breakdown": s4["breakdown_GWh"], "grade": "A",
         "period": s4["period"], "source": "SRC-1", "source_file": s4["source_file"]},
        {"id": "S5", "name": "Net generation", "unit": "GWh", "status": "populated",
         "value": s5_value, "grade": "A", "period": "FY2023-24", "source": "SRC-1",
         "source_file": aux["source_file"],
         "metrics": {"aux_rate_conventional": aux["aux_rate"],
                     "aux_energy_GWh": round(conv_gross * aux["aux_rate"], 0)},
         "note": "Derived: conventional gross x (1 - actual aux rate from the CO2 Baseline DB) + RES (net~gross, CEA convention). Aux rate is a fleet aggregate - fuel-wise split not published."},
        {"id": "S6", "name": "Delivered to distribution", "unit": "GWh", "status": "pending",
         "note": "Needs NLDC applicable-ISTS-loss series; commercial vs physical basis must be labeled."},
        {"id": "S7", "name": "Billed & collected", "unit": "%", "status": "populated",
         "metrics": {"atc_loss_pct": atc["atc_loss_pct"],
                     "billing_efficiency_pct": atc["billing_efficiency_pct"],
                     "collection_efficiency_pct": atc["collection_efficiency_pct"]},
         "grade": atc["grade"], "period": atc["period"], "source": atc["source"],
         "hand_verified": atc["hand_verified"]},
        {"id": "S8", "name": "Service received", "unit": "mixed", "status": "partial",
         "metrics": {"per_capita_kwh": parse_cea.per_capita_series()[-1]["kwh"]},
         "grade": "B", "period": "FY2023-24", "source": "SRC-1",
         "source_file": "data/raw/SRC-1/growth-book/Growth_Book_2024.pdf",
         "note": "Per-capita consumption is measurable (utilities + non-utilities basis). Supply hours and reliability still have no live public feed (ESMI discontinued) - annual PIB statements only."},
    ]

    edges = [
        {"kind": "bridge", "from": "S1", "to": "S4", "status": "partial",
         "factor": round(implied_utilisation, 4),
         "factor_label": "Implied fleet utilisation vs INSTALLED capacity (not dispatched — S3 has no parser yet). Denominator choice changes this number; that is pitfall P-06, shown rather than hidden.",
         "citizen_note": "Megawatts measure what could be produced at any instant; units of electricity measure what actually was - a solar farm and a coal plant of the same size produce very different amounts over a year."},
        {"kind": "side_flow", "from": "bypass", "to": "S8", "status": "populated",
         "gap_value": captive["value_GWh"], "gap_unit": "GWh",
         "provisional": captive["provisional"], "grade": "B", "source": "SRC-1",
         "source_file": captive["source_file"],
         "label": "Captive generation (plants >=0.5 MW) - bypasses S6-S7",
         "citizen_note": "A large slice of India's electricity never touches the public grid's books - factories generating for themselves, rooftop solar, direct purchases - which is why national totals and your electricity bill never quite reconcile."},
        {"kind": "gap", "from": "S6", "to": "S7", "status": "partial",
         "metrics_only": True,
         "atc_identity_check": {"lhs_atc_pct": atc["atc_loss_pct"],
                                "rhs_from_efficiencies_pct": round(100 * (1 - (atc["billing_efficiency_pct"] / 100) * (atc["collection_efficiency_pct"] / 100)), 2)},
         "citizen_note": "Of the electricity handed to distribution companies, a share is lost in local wires, never billed, or billed but never paid for."},
        {"kind": "feedback", "from": "S7", "to": "S3", "status": "pending",
         "citizen_note": "When distribution companies cannot collect what they bill, they cannot pay power plants - so they buy less, and plants that could run sit idle."},
    ]

    return {
        "title": "India Electricity Dashboard - walking skeleton",
        "spec": "chain-specification-v0.2.md",
        "period": "FY2023-24",
        "period_basis": "fiscal year (April-March)",
        "scope": "national, annual",
        "stages": stages,
        "edges": edges,
    }


def build_series() -> dict:
    """Historical mode-wise series for the time-series view (Growth Book)."""
    cap = parse_cea.capacity_series()
    gen = parse_cea.generation_series()
    for rows in (cap, gen):
        for r in rows:
            # CEA's own printed totals for 1950-1969 generation exclude gas and
            # diesel. Publish the residual; never force the identity.
            r["residual"] = round(r["total"] - (r["thermal"] + r["hydro"] + r["nuclear"] + r["res"]), 1)
    return {
        "source": "SRC-1",
        "source_file": "data/raw/SRC-1/growth-book/Growth_Book_2024.pdf",
        "note": "Utilities only (captive/bypass excluded). Rows before 1992 are plan-end years - irregular spacing. 'residual' = printed CEA total minus sum of modes; non-zero 1950-1969 because CEA's printed generation totals there exclude gas and diesel.",
        "capacity_MW": cap,
        "generation_GWh": gen,
        "per_capita_kWh": parse_cea.per_capita_series(),
        "consumption_GWh": parse_cea.consumption_series(),
    }


def check_series_invariants(series: dict) -> list[str]:
    errors = []
    for key in ("capacity_MW", "generation_GWh"):
        for r in series[key]:
            if abs(r["residual"]) > r["total"] * 0.05:
                errors.append(f"{key} {r['year']}: residual {r['residual']} exceeds 5% of total")
            if r["year"] >= 1970 and abs(r["residual"]) > max(3, r["total"] * 2e-4):
                errors.append(f"{key} {r['year']}: unexplained residual {r['residual']} after 1970")
    for r in series["consumption_GWh"]:
        parts = sum(r[k] for k in ("domestic", "commercial", "industrial", "traction", "agriculture", "misc"))
        if abs(parts - r["total"]) > max(3, r["total"] * 2e-3):
            errors.append(f"consumption {r['year']}: categories sum {parts} vs printed total {r['total']}")
    pc = series["per_capita_kWh"]
    if pc[0] != {"year": 1947, "kwh": 16.0} or not (1200 < pc[-1]["kwh"] < 1700):
        errors.append("per-capita series endpoints out of expected range")
    # FY24 endpoints must agree with the chain's independently parsed values.
    if abs(series["capacity_MW"][-1]["total"] - 441_969.5) > 2:
        errors.append("capacity series 2024 endpoint disagrees with IC xlsx")
    if abs(series["generation_GWh"][-1]["total"] - 1_734_375) > 2:
        errors.append("generation series 2024 endpoint disagrees with chain S4")
    return errors


def check_invariants(chain: dict) -> list[str]:
    errors = []
    by_id = {s["id"]: s for s in chain["stages"]}

    # INV: any populated stage with a breakdown must sum to its value exactly
    # (tolerance covers source rounding, not omissions).
    for s in chain["stages"]:
        if s.get("breakdown"):
            total = sum(s["breakdown"].values())
            if abs(total - s["value"]) > max(2.0, s["value"] * 1e-4):
                errors.append(f"{s['id']}: breakdown sums to {total}, value is {s['value']}")

    # INV-18b (bridge): implied utilisation must be physically possible.
    for e in chain["edges"]:
        if e["kind"] == "bridge" and "factor" in e:
            if not (0 < e["factor"] < 1):
                errors.append(f"bridge {e['from']}->{e['to']}: factor {e['factor']} outside (0,1)")

    # S7 internal identity: AT&C = 1 - billing_eff x collection_eff.
    for e in chain["edges"]:
        chk = e.get("atc_identity_check")
        if chk and abs(chk["lhs_atc_pct"] - chk["rhs_from_efficiencies_pct"]) > 0.25:
            errors.append(f"AT&C identity broken: {chk}")

    # S5: aux rate plausibility, cross-source gross agreement, and ordering.
    s5 = by_id.get("S5", {})
    if s5.get("metrics"):
        rate = s5["metrics"]["aux_rate_conventional"]
        if not (0.04 < rate < 0.10):
            errors.append(f"S5 aux rate {rate} outside 4-10% plausibility band")
        if not (s5["value"] < by_id["S4"]["value"]):
            errors.append("S5 net generation not below S4 gross")
    # Cross-validation: CO2-DB conventional gross must agree with Growth Book
    # conventional gross within 0.5% (two independent CEA publications).
    aux_chk = parse_cea.aux_consumption_fy24()
    gb_conv = sum(by_id["S4"]["breakdown"][k] for k in
                  ("coal_lignite", "gas", "diesel", "hydro_large", "nuclear"))
    if abs(aux_chk["conventional_gross_GWh"] - gb_conv) / gb_conv > 0.005:
        errors.append(f"CO2-DB conventional gross {aux_chk['conventional_gross_GWh']} vs Growth Book {gb_conv} disagree >0.5%")

    # Peak demand met must be physically consistent: below installed capacity,
    # above half of it (sanity band for modern India).
    s3 = by_id.get("S3", {})
    if s3.get("metrics"):
        pk = s3["metrics"]["peak_met_MW"]
        ic = by_id["S1"]["value"]
        if not (ic * 0.3 < pk < ic):
            errors.append(f"S3 peak met {pk} MW implausible against installed {ic} MW")

    # Cross-validation: RES generation in S4 breakdown must match the
    # Executive Summary figure (225.83 BU) within rounding.
    if "S4" in by_id and by_id["S4"].get("breakdown"):
        res = by_id["S4"]["breakdown"]["res"]
        if abs(res - 225_835) > 100:
            errors.append(f"S4 RES {res} GWh disagrees with Executive Summary 225,835 GWh")

    return errors


def main() -> int:
    chain = build()
    series = build_series()
    errors = check_invariants(chain) + check_series_invariants(series)
    if errors:
        print("INVARIANT FAILURES:")
        for e in errors:
            print(" -", e)
        return 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(chain, indent=2))
    OUT_SERIES.write_text(json.dumps(series, indent=2))
    populated = sum(1 for s in chain["stages"] if s["status"] == "populated")
    partial = sum(1 for s in chain["stages"] if s["status"] == "partial")
    n = len(series["capacity_MW"])
    print(f"wrote {OUT.relative_to(ROOT)} - {populated} full + {partial} partial of 9 stages, all invariants pass")
    print(f"wrote {OUT_SERIES.relative_to(ROOT)} - {n} rows per series, 1947-2024")
    return 0


if __name__ == "__main__":
    sys.exit(main())
