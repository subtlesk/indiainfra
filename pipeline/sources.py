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
        "files": {
            # Monthly operational report March 2024 - daily national peak-met and
            # energy-met tables + "All Time Highest" (FY24 peak demand met).
            "monthly_2024_03": {
                "url": "https://webcdn.grid-india.in/files/grdw/uploads/download-manager-files/Monthly_Report_Mar_2024.pdf",
                "path": "data/raw/SRC-4/monthly/Monthly_Report_Mar_2024.pdf",
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
