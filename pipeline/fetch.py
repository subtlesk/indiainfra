"""Archive-first fetcher.

Rule (chain-specification-v0.2.md, "Data access reality"): every raw file is
stored verbatim and versioned BEFORE any parsing. Sources in this ecosystem
demonstrably die (ESMI, UDAY, Saubhagya, MERIT) — the raw archive is a project
asset. A failed fetch must never destroy an existing archived copy.

Usage: python -m pipeline.fetch          # fetch anything missing
       python -m pipeline.fetch --force  # re-download even if present
"""

import sys
import time
import urllib.request
import ssl
from pathlib import Path

from .sources import SOURCES

ROOT = Path(__file__).resolve().parent.parent


def fetch_one(url: str, dest: Path, insecure: bool = False, retries: int = 3) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    ctx = ssl._create_unverified_context() if insecure else None
    req = urllib.request.Request(url, headers={"User-Agent": "indiainfra-archiver/0.1"})
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
                body = resp.read()
            if not body:
                raise IOError("empty response")
            tmp = dest.with_suffix(dest.suffix + ".part")
            tmp.write_bytes(body)
            tmp.replace(dest)  # never leave a truncated file at the real path
            print(f"  fetched {len(body):>10,} B  {dest.relative_to(ROOT)}")
            return True
        except Exception as e:
            print(f"  attempt {attempt}/{retries} failed for {url}: {e}")
            time.sleep(5 * attempt)
    return False


def main(force: bool = False) -> int:
    failures = []
    for src_id, src in SOURCES.items():
        insecure = "insecure_tls" in src.get("quirks", [])
        for key, f in src.get("files", {}).items():
            dest = ROOT / f["path"]
            if dest.exists() and not force:
                continue
            print(f"{src_id}/{key}:")
            ok = fetch_one(f["url"], dest, insecure=insecure)
            if not ok and not f.get("optional"):
                failures.append(f"{src_id}/{key}")
    if failures:
        print("FAILED (and required):", ", ".join(failures))
        # Only fail if the archive doesn't already hold the file.
        return 1
    print("archive complete")
    return 0


if __name__ == "__main__":
    sys.exit(main(force="--force" in sys.argv))
