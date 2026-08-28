"""Source registry — mirrors the SRC-n table in chain-specification-v0.2.md.

Every fetched file must be attributable to exactly one SRC code. URLs here are
the ones verified live in August 2026; when one dies, add its replacement and
keep the old one commented, never delete history.
"""

SOURCES = {
    "SRC-1": {
        "name": "CEA (Central Electricity Authority)",
        "quirks": [],
        "files": {
            # Installed capacity as on 31.03.2024 (FY2023-24 year end). Excel.
            "ic_2024_03": {
                "url": "https://cea.nic.in/wp-content/uploads/installed/2024/03/IC_Mar_2024_allocation_wise.xlsx",
                "path": "data/raw/SRC-1/2024-03/IC_Mar_2024_allocation_wise.xlsx",
            },
            # Growth of Electricity Sector in India 1947-2024. Full historical
            # series: IC (Table 2), gross generation (Table 3), consumption
            # (Table 4), captive capacity/generation (Tables 6/7).
            "growth_book_2024": {
                "url": "https://cea.nic.in/wp-content/uploads/pdm/2024/08/Growth_Book_2024.pdf",
                "path": "data/raw/SRC-1/growth-book/Growth_Book_2024.pdf",
            },
            # Executive Summary April 2024 — cross-validates FY24 RES total.
            "exec_summary_2024_04": {
                "url": "https://cea.nic.in/wp-content/uploads/executive/2024/04/Executive_Summary_April_2024.pdf",
                "path": "data/raw/SRC-1/2024-04/Executive_Summary_April_2024.pdf",
            },
            # Broad Status Report April 2024 (as on 30.04.2024): unit-level
            # thermal under-construction (S0), incl. on-hold section 1.3.
            "broad_status_2024_04": {
                "url": "https://cea.nic.in/wp-content/uploads/thermal_broad/2024/03/BS_APR_2024.pdf",
                "path": "data/raw/SRC-1/broad-status/BS_APR_2024.pdf",
            },
            # Hydro Project Monitoring annex (as on 31.12.2023): >25 MW hydro
            # under active construction, sector-wise (S0).
            "hydro_uc_2023_12": {
                "url": "https://cea.nic.in/wp-content/uploads/hydro/2024/01/Annex__Sector_wise_31.12.2023.xlsx",
                "path": "data/raw/SRC-1/hydro/Annex__Sector_wise_31.12.2023.xlsx",
            },
            # CO2 Baseline Database v20.0 (Dec 2024): station-wise net generation
            # for the conventional fleet + 5-year gross/net series (Results
            # sheet). Source of the ACTUAL FY24 auxiliary-consumption rate.
            "co2_baseline_v20": {
                "url": "https://cea.nic.in/wp-content/uploads/2021/03/CO2_Database_Version_20.0_2023_24.xlsx",
                "path": "data/raw/SRC-1/co2-baseline/CO2_Database_Version_20.0_2023_24.xlsx",
            },
            # Annual Report 2023-24 (archived while hunting aux data; no aux
            # table inside - kept because sources die).
            "annual_report_2023_24": {
                "url": "https://cea.nic.in/wp-content/uploads/annual_reports/2024/Final_Approved_Annual_Report_2023_24_05032025_1.pdf",
                "path": "data/raw/SRC-1/annual-report/Final_Approved_Annual_Report_2023_24_05032025_1.pdf",
            },
            # Latest monthly IC snapshot (June 2026) — freshness probe.
            "ic_latest": {
                "url": "https://cea.nic.in/wp-content/uploads/installed/2026/06/Website_June.xlsx",
                "path": "data/raw/SRC-1/2026-06/Website_June.xlsx",
            },
        },
    },
    "SRC-4": {
        "name": "Grid-India / POSOCO / NLDC",
        # grid-india.in serves a broken TLS chain; posoco.in intermittently 502s.
        # The website is an SPA over a clean undocumented JSON API:
        #   POST webapi.grid-india.in/api/v1/file/get-period {_source:"grdw", _fileType:"REPORTS_MONTHLY_REPORT"}
        #   POST webapi.grid-india.in/api/v1/file {_source:"grdw", _type:"REPORTS_MONTHLY_REPORT", _fileDate:"2023-24", _month:"03"}
        # Files are served from webcdn.grid-india.in/<FilePath>. Archive: 2012-13 onward.
        "quirks": ["insecure_tls", "retry"],
        # All 12 FY2023-24 monthly reports are archived (daily national
        # energy-met and peak-met tables; the March edition also carries the
        # "All Time Highest" table). Names follow the CDN's own inconsistent
        # convention (Apr_2023 ... January_2024).
        "files": {
            f"monthly_{name.split('_')[-2]}_{name.split('_')[-1]}": {
                "url": f"https://webcdn.grid-india.in/files/grdw/uploads/download-manager-files/{name}.pdf",
                "path": f"data/raw/SRC-4/monthly/{name}.pdf",
            }
            for name in [
                "Monthly_Report_Apr_2023", "Monthly_Report_May_2023",
                "Monthly_Report_Jun_2023", "Monthly_Report_Jul_2023",
                "Monthly_Report_Aug_2023", "Monthly_Report_Sep_2023",
                "Monthly_Report_Oct_2023", "Monthly_Report_Nov_2023",
                "Monthly_Report_Dec_2023", "Monthly_Report_January_2024",
                "Monthly_Report_February_2024", "Monthly_Report_Mar_2024",
            ]
        },
    },
    "SRC-12": {
        "name": "PIB / MoP statements (and archived snapshots of dead pages)",
        "quirks": [],
        "files": {
            # MoP "Power Sector at a Glance" - frozen since 27/06/2023, page
            # dropped in the site's Next.js migration. Wayback snapshot kept as
            # evidence + for its 2009-10..2022-23 requirement/availability table.
            "powermin_glance_frozen": {
                "url": "http://web.archive.org/web/20260301072112/https://powermin.gov.in/en/content/power-sector-glance-all-india",
                "path": "data/raw/SRC-12/powermin_glance_wayback_20260301.html",
            },
        },
    },
    "SRC-5": {
        "name": "PFC — Report on Performance of Power Utilities",
        # pfcindia.com cert is for *.pfcindia.co.in — always use .co.in.
        "quirks": ["retry"],
        "files": {
            "pfc_2023_24": {
                "url": "https://www.pfcindia.co.in/ensite/DocumentRepository/ckfinder/files/Operations/Performance_Reports_of_State_Power_Utilities/Report%20on%20Performance%20of%20Power%20Utilities%202023-24.pdf",
                "path": "data/raw/SRC-5/Report_on_Performance_of_Power_Utilities_2023-24.pdf",
                "optional": True,  # large; S7 figures are hand-verified meanwhile
            },
        },
    },
}
