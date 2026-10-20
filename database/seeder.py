"""
database/seeder.py

Seeds the local hash database from MalwareBazaar (abuse.ch).

MalwareBazaar provides a free CSV dump of recent malware SHA-256 hashes.
Download URL: https://bazaar.abuse.ch/export/csv/recent/

Usage
-----
    # From terminal:
    python -m database.seeder

    # From code:
    from database.seeder import seed_from_csv, seed_from_url
    seed_from_url()          # downloads latest feed and seeds DB
    seed_from_csv("my.csv")  # seeds from a local CSV file
"""

import csv
import io
import os
import sys
import urllib.request
from typing import Optional

# Add project root to path when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import HashDatabase

MALWAREBAZAAR_URL = "https://bazaar.abuse.ch/export/csv/recent/"

# MalwareBazaar CSV columns (row 0 after stripping comments):
# first_seen, sha256_hash, md5_hash, sha1_hash, reporter, file_name,
# file_type_guess, mime_type, signature, clamav, vtpercent, imphash,
# ssdeep, tlsh
SHA256_COL    = 1
NAME_COL      = 7   # mime_type used as rough name; signature is better
SIGNATURE_COL = 8   # malware family name (e.g. "AgentTesla")


def seed_from_url(
    url: str = MALWAREBAZAAR_URL,
    db_path: Optional[str] = None,
    verbose: bool = True,
) -> int:
    """
    Download the MalwareBazaar CSV feed and seed the database.
    Returns the number of hashes inserted.
    """
    if verbose:
        print(f"[seeder] Downloading feed from {url} ...")

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SentinelAI/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        raw = data.decode("utf-8", errors="ignore")
        print(raw[:2000])   # Print the first 2000 bytes
    except Exception as e:
        print(f"[seeder] Download failed: {e}")
        return 0

    return _parse_and_insert(raw, source="MalwareBazaar", db_path=db_path, verbose=verbose)


def seed_from_csv(
    csv_path: str,
    db_path: Optional[str] = None,
    verbose: bool = True,
) -> int:
    """
    Seed the database from a locally saved MalwareBazaar CSV file.
    Returns the number of hashes inserted.
    """
    if verbose:
        print(f"[seeder] Reading {csv_path} ...")
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        raw = f.read()
    return _parse_and_insert(raw, source="MalwareBazaar", db_path=db_path, verbose=verbose)


def seed_from_list(
    hashes: list[dict],
    db_path: Optional[str] = None,
    verbose: bool = True,
) -> int:
    """
    Seed from a plain Python list:
      [{"sha256": "abc...", "malware_name": "Trojan.X", "source": "custom"}, ...]
    """
    kwargs = {"db_path": db_path} if db_path else {}
    db = HashDatabase(**kwargs)
    db.setup()
    before = db.total_hashes()
    db.insert_many(hashes)
    inserted = db.total_hashes() - before
    if verbose:
        print(f"[seeder] Inserted {inserted} hashes from list.")
    return inserted


# ── Internal ──────────────────────────────────────────────────────────────────

def _parse_and_insert(
    raw_csv: str,
    source: str,
    db_path: Optional[str],
    verbose: bool,
) -> int:
    records = []
    reader = csv.reader(io.StringIO(raw_csv))

    def clean(value):
        return value.strip().strip('"')

    for row in reader:
       
        if not row or row[0].startswith("#"):
            continue
        if len(row) <= max(SHA256_COL, SIGNATURE_COL):
            continue

        sha256 = clean(row[SHA256_COL]).strip().lower()
        if len(sha256) != 64:   # basic sanity check
            continue

        malware_name = (
            clean(row[SIGNATURE_COL])
            or clean(row[NAME_COL])
        )
        records.append({
            "sha256":       sha256,
            "malware_name": malware_name,
            "source":       source,
        })
    reader = csv.reader(io.StringIO(raw_csv))

    count = 0
    for row in csv.reader(io.StringIO(raw_csv)):
        print(row)
        count += 1
        if count == 20:
            break
    if not records:
        if verbose:
            print("[seeder] No valid records found in CSV.")
        return 0

    kwargs = {"db_path": db_path} if db_path else {}
    db = HashDatabase(**kwargs)
    db.setup()
    before = db.total_hashes()
    db.insert_many(records)
    inserted = db.total_hashes() - before

    if verbose:
        print(f"[seeder] Parsed {len(records)} records → inserted {inserted} new hashes.")
        print(f"[seeder] Total hashes in DB: {db.total_hashes():,}")

    return inserted


# ── CLI entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed Sentinel AI hash database")
    parser.add_argument("--csv",  help="Path to local MalwareBazaar CSV file")
    parser.add_argument("--url",  default=MALWAREBAZAAR_URL, help="Feed URL")
    args = parser.parse_args()

    if args.csv:
        seed_from_csv(args.csv)
    else:
        seed_from_url(args.url)