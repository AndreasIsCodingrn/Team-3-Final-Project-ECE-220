#!/usr/bin/env python3
"""Collect Team 3's public GitHub JSON files and assemble a traceable master dataset.

Python 3.9+, standard library only. Does not modify the repository.
"""
import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

DEFAULT_REPO = "AndreasIsCodingrn/Team-3-Final-Project-ECE-220"
DEFAULT_BRANCH = "main"
SKIP_NAMES = {"master_dataset.json", "team3_master_dataset.json", "merged_dataset.json"}
USER_AGENT = "Team3-CubaNM-Energy-Research-Collector/1.0"


def fetch_bytes(url, retries=2):
    for attempt in range(retries + 1):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
            with urlopen(request, timeout=25) as res:
                return res.read()
        except HTTPError as exc:
            if exc.code in (429, 500, 502, 503, 504) and attempt < retries:
                time.sleep(attempt + 1)
                continue
            details = exc.read(350).decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code} for {url}: {details}") from exc
        except (URLError, TimeoutError) as exc:
            if attempt < retries:
                time.sleep(attempt + 1)
                continue
            raise RuntimeError(f"Cannot reach {url}: {exc}") from exc


def get_repo_files(repo, branch):
    """Discover JSON paths using GitHub's tree API (including nested folders)."""
    endpoint = f"https://api.github.com/repos/{repo}/git/trees/{quote(branch, safe='')}?recursive=1"
    tree_doc = json.loads(fetch_bytes(endpoint))
    if tree_doc.get("truncated"):
        raise RuntimeError("GitHub tree listing was truncated; cannot guarantee complete collection.")
    tree = tree_doc.get("tree")
    if not isinstance(tree, list):
        raise RuntimeError("GitHub did not return a file tree. Check repo name, branch and visibility.")
    paths = [node["path"] for node in tree
             if node.get("type") == "blob" and node.get("path", "").lower().endswith(".json")
             and Path(node["path"]).name.lower() not in SKIP_NAMES
             and not node["path"].startswith(".github/")]
    return sorted(paths)


def github_raw_url(repo, branch, path):
    return f"https://raw.githubusercontent.com/{repo}/{quote(branch, safe='')}/{quote(path, safe='/')}"


def read_json_file(path):
    raw = Path(path).read_bytes()
    return json.loads(raw.decode("utf-8-sig")), raw


def read_repo_json(repo, branch, path):
    raw = fetch_bytes(github_raw_url(repo, branch, path))
    return json.loads(raw.decode("utf-8-sig")), raw


def normalize_member2(data, path, warnings):
    """Normalize known EIA-861 sector data without changing source observations."""
    if not isinstance(data, dict) or not isinstance(data.get("eia_861"), dict):
        return []
    entries = data["eia_861"].get("annual_sales_by_sector", [])
    if not isinstance(entries, list):
        warnings.append(f"{path}: eia_861.annual_sales_by_sector is not a list")
        return []
    output = []
    for i, annual in enumerate(entries):
        if not isinstance(annual, dict):
            warnings.append(f"{path}: year entry {i} is not an object")
            continue
        yr, sectors = annual.get("year"), annual.get("sectors")
        state = annual.get("state")
        utility_id = annual.get("utility_id")
        if not isinstance(yr, int) or not isinstance(sectors, dict):
            warnings.append(f"{path}: invalid year or sectors at index {i}")
            continue
        if state != "NM" or utility_id != 9699:
            warnings.append(f"{path}: skipped {yr} due to unexpected state or utility ID: {state}/{utility_id}")
            continue
        for sector, row in sectors.items():
            if not isinstance(row, dict):
                warnings.append(f"{path}: sector {sector} for {yr} is not an object")
                continue
            output.append({
                "year": yr, "state": state, "utility_eia_id": utility_id,
                "utility_name": annual.get("utility_name"), "sector": sector,
                "sales_mwh": row.get("sales_mwh"),
                "revenue_usd": row.get("revenue_usd"),
                "customers": row.get("customers"),
                "average_price_cents_per_kwh": row.get("average_price_cents_per_kwh"),
                "source_file": annual.get("source", {}).get("file") if isinstance(annual.get("source"), dict) else None,
                "verification_status": annual.get("source", {}).get("status") if isinstance(annual.get("source"), dict) else None,
                "source_dataset_path": path,
            })
    return output


def build_master(documents, repo, branch, errors, extra_warnings):
    warnings = list(extra_warnings)
    datasets, normalized = [], []
    for item in documents:
        path, doc, raw = item["path"], item["json"], item["raw"]
        source_url = github_raw_url(repo, branch, path) if repo else None
        datasets.append({
            "source_path": path, "source_url": source_url,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "top_level_type": type(doc).__name__,
            "dataset_id": doc.get("dataset_id") if isinstance(doc, dict) else None,
            "data": doc,
        })
        normalized.extend(normalize_member2(doc, path, warnings))
    # Exact duplicate rows can arise if a teammate re-uploads copies. Retain both
    # source documents, but avoid duplicating exact same normalized observations.
    unique = {}
    for row in normalized:
        key = (row["year"], row["utility_eia_id"], row["state"], row["sector"])
        if key in unique:
            previous = unique[key]
            values = ("sales_mwh", "revenue_usd", "customers", "average_price_cents_per_kwh")
            if any(previous[k] != row[k] for k in values):
                warnings.append(f"CONFLICT for {key}: {previous['source_dataset_path']} vs {row['source_dataset_path']}; kept both in source_datasets, first normalized row only")
            else:
                warnings.append(f"Repeated normalized row for {key}; retained first occurrence")
        else:
            unique[key] = row
    return {
        "master_schema_version": "1.0.0",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "project": "Team 3 - Cuba, New Mexico energy dashboard",
        "github_repository": f"https://github.com/{repo}" if repo else None,
        "github_branch": branch if repo else None,
        "collection_status": "complete" if not errors else "partial_with_errors",
        "source_dataset_count": len(datasets),
        "source_dataset_paths": [x["source_path"] for x in datasets],
        "source_datasets": datasets,
        "normalized_tables": {"eia861_jmec_sales_by_sector": sorted(unique.values(), key=lambda r:(r["year"],r["sector"]))},
        "data_dictionary": {
            "eia861_jmec_sales_by_sector": {
                "sales_mwh": "Annual sales to ultimate customers, MWh",
                "revenue_usd": "Annual retail sales revenue, USD",
                "customers": "Average customer accounts during year, count",
                "average_price_cents_per_kwh": "Reported or derived revenue-weighted price, cents/kWh; NOT tariff price",
                "geographic_scope": "JMEC service territory in NM; NOT the municipal boundaries of Cuba, NM"
            }
        },
        "collection_errors": errors,
        "validation_warnings": warnings,
        "integration_notes": [
            "Teammates' original JSON objects are preserved in source_datasets without altering fields or units.",
            "Only known EIA-861 fields are normalized automatically; other members require team-approved field mapping.",
            "Different geographies and units must not be merged into a single flat table without explicit keys and conversions.",
            "Historical OpenEI tariffs must not be interpreted as currently effective rates.",
            "Repository publication does not verify the scientific accuracy of any submitted observations."
        ]
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub owner/repository")
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    parser.add_argument("--output", default="team3_master_dataset.json")
    parser.add_argument("--local-dir", help="Offline test: read JSON files recursively from this local directory instead of GitHub")
    parser.add_argument("--require-all", action="store_true", help="Exit nonzero if any source failed to load")
    args = parser.parse_args(argv)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repo):
        parser.error("--repo must look like OWNER/REPOSITORY")
    errors = []
    documents = []
    if args.local_dir:
        base = Path(args.local_dir)
        if not base.is_dir():
            parser.error(f"Directory does not exist: {base}")
        paths = [p for p in base.rglob("*.json") if p.name.lower() not in SKIP_NAMES and p.resolve() != Path(args.output).resolve()]
        for file_path in sorted(paths):
            rel = file_path.relative_to(base).as_posix()
            try:
                doc, raw = read_json_file(file_path)
                documents.append({"path": rel, "json": doc, "raw": raw})
                print(f"OK  {rel}")
            except (ValueError, OSError, UnicodeDecodeError) as exc:
                errors.append(f"{rel}: {exc}")
                print(f"ERR {rel}: {exc}", file=sys.stderr)
        source_repo = None
    else:
        try:
            paths = get_repo_files(args.repo, args.branch)
        except (RuntimeError, ValueError) as exc:
            print(f"Could not list repository JSON files: {exc}", file=sys.stderr)
            return 2
        for path in paths:
            try:
                doc, raw = read_repo_json(args.repo, args.branch, path)
                documents.append({"path": path, "json": doc, "raw": raw})
                print(f"OK  {path}")
            except (RuntimeError, ValueError, UnicodeDecodeError) as exc:
                errors.append(f"{path}: {exc}")
                print(f"ERR {path}: {exc}", file=sys.stderr)
        source_repo = args.repo
    if not documents:
        print("No valid JSON source datasets available. No master file written.", file=sys.stderr)
        return 2
    master = build_master(documents, source_repo, args.branch, errors, [])
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(master, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"\nCreated: {output} | source datasets: {len(documents)} | EIA normalized rows: {len(master['normalized_tables']['eia861_jmec_sales_by_sector'])} | errors: {len(errors)} | warnings: {len(master['validation_warnings'])}")
    return 1 if args.require_all and errors else 0

if __name__ == "__main__":
    sys.exit(main())
