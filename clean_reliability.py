"""
clean_reliability.py
Owner: Jadon Giron (Team Member 1)

Reads every EIA-861 Reliability_YYYY.xlsx file in a folder, keeps New Mexico
utilities, merges the "IEEE Standard" and "Other Standard" column blocks into
one set of columns, and writes a single tidy CSV (one row per utility per year).

Usage (run from the project root):
    python src/clean_reliability.py
    python src/clean_reliability.py --input data/raw --output data/clean/reliability_nm.csv
    python src/clean_reliability.py --state NM

Input files: Reliability_2023.xlsx, Reliability_2024.xlsx, ...
(put them all in one folder, e.g. data/raw/; the year must be in the file name)
"""

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd

SHEET = "Reliability_States"
HEADER_ROWS = 3  # the Excel header spans 3 rows; data starts on row 4

# Column names in the order they appear in the EIA file (28 columns).
# The IEEE block and the "Other standard" block each hold their own copy of the metrics.
RAW_COLUMNS = [
    "data_year", "utility_number", "utility_name", "state", "ownership",
    "ieee_saidi_all", "ieee_saifi_all", "ieee_caidi_all",
    "ieee_saidi_noMED", "ieee_saifi_noMED", "ieee_caidi_noMED",
    "ieee_saidi_LOS", "ieee_saifi_LOS", "ieee_caidi_LOS",
    "ieee_customers", "ieee_voltage", "ieee_auto",
    "oth_saidi_all", "oth_saifi_all", "oth_caidi_all",
    "oth_saidi_noMED", "oth_saifi_noMED", "oth_caidi_noMED",
    "oth_customers", "oth_inactive_included", "oth_momentary_included",
    "oth_voltage", "oth_auto",
]

METRICS = [
    "saidi_all", "saifi_all", "caidi_all",
    "saidi_noMED", "saifi_noMED", "caidi_noMED",
    "customers", "voltage", "auto",
]

NUMERIC_COLS = [c for c in RAW_COLUMNS if c.endswith(
    ("saidi_all", "saifi_all", "caidi_all", "saidi_noMED", "saifi_noMED",
     "caidi_noMED", "saidi_LOS", "saifi_LOS", "caidi_LOS", "customers", "voltage"))]

FINAL_COLUMNS = [
    "data_year", "utility_number", "utility_name", "state", "ownership",
    "reporting_standard",
    "saidi_with_med", "saifi_with_med", "caidi_with_med",
    "saidi_without_med", "saifi_without_med", "caidi_without_med",
    "saidi_loss_of_supply_removed", "saifi_loss_of_supply_removed",
    "customers", "highest_dist_voltage", "outages_recorded_automatically",
    "is_jmec",
]


def read_one_year(path: Path) -> pd.DataFrame:
    """Read one Reliability_YYYY.xlsx and return it with clean column names."""
    df = pd.read_excel(path, sheet_name=SHEET, header=None, skiprows=HEADER_ROWS)
    if df.shape[1] != len(RAW_COLUMNS):
        raise ValueError(
            f"{path.name}: expected {len(RAW_COLUMNS)} columns but found {df.shape[1]}. "
            "The EIA layout may have changed for this year; check the header rows."
        )
    df.columns = RAW_COLUMNS

    # EIA uses "." (and sometimes blanks/spaces) for "not reported".
    df = df.replace({".": np.nan, " ": np.nan, "": np.nan})
    for col in NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["state"] = df["state"].astype("string").str.strip()
    df["utility_name"] = df["utility_name"].astype("string").str.strip()
    return df


def merge_standards(df: pd.DataFrame) -> pd.DataFrame:
    """Combine IEEE and Other-standard columns into one set of columns."""
    out = df[["data_year", "utility_number", "utility_name", "state", "ownership"]].copy()

    ieee_has_data = df[["ieee_saidi_all", "ieee_saidi_noMED", "ieee_saifi_all",
                        "ieee_saifi_noMED"]].notna().any(axis=1)
    oth_has_data = df[["oth_saidi_all", "oth_saidi_noMED", "oth_saifi_all",
                       "oth_saifi_noMED"]].notna().any(axis=1)

    # Prefer IEEE when both are filled in (rare); otherwise use whichever has data.
    out["reporting_standard"] = np.select(
        [ieee_has_data, oth_has_data], ["IEEE", "Other"], default="None reported"
    )
    out["reported_both_standards"] = ieee_has_data & oth_has_data

    use_ieee = ieee_has_data

    def pick(metric):
        return np.where(use_ieee, df[f"ieee_{metric}"], df[f"oth_{metric}"])

    out["saidi_with_med"] = pick("saidi_all")
    out["saifi_with_med"] = pick("saifi_all")
    out["caidi_with_med"] = pick("caidi_all")
    out["saidi_without_med"] = pick("saidi_noMED")
    out["saifi_without_med"] = pick("saifi_noMED")
    out["caidi_without_med"] = pick("caidi_noMED")

    # "Loss of supply removed" only exists in the IEEE block.
    out["saidi_loss_of_supply_removed"] = df["ieee_saidi_LOS"]
    out["saifi_loss_of_supply_removed"] = df["ieee_saifi_LOS"]

    out["customers"] = np.where(use_ieee, df["ieee_customers"], df["oth_customers"])
    out["highest_dist_voltage"] = np.where(use_ieee, df["ieee_voltage"], df["oth_voltage"])
    out["outages_recorded_automatically"] = np.where(
        use_ieee, df["ieee_auto"], df["oth_auto"]
    )
    return out


def main():
    parser = argparse.ArgumentParser(description="Clean EIA-861 reliability data.")
    parser.add_argument("--input", default="data/raw", help="Folder with Reliability_YYYY.xlsx files")
    parser.add_argument("--output", default="data/clean/reliability_nm.csv", help="Output CSV path")
    parser.add_argument("--state", default="NM", help="Two-letter state code to keep (default NM)")
    args = parser.parse_args()

    in_dir = Path(args.input)
    files = sorted(
        p for p in in_dir.rglob("Reliability_*.xlsx")
        if re.search(r"Reliability_(\d{4})\.xlsx$", p.name, re.IGNORECASE)
    )
    if not files:
        raise SystemExit(f"No Reliability_YYYY.xlsx files found in {in_dir.resolve()}")

    frames = []
    for f in files:
        print(f"Reading {f.name} ...")
        raw = read_one_year(f)
        raw = raw[raw["state"] == args.state.upper()]
        frames.append(merge_standards(raw))

    result = pd.concat(frames, ignore_index=True)

    # Tidy names: EIA sometimes appends " - (NM)" to the utility name.
    result["utility_name"] = (
        result["utility_name"].str.replace(r"\s*-\s*\(\w{2}\)\s*$", "", regex=True).str.strip()
    )
    result["is_jmec"] = result["utility_name"].str.contains("Jemez", case=False, na=False)

    result["data_year"] = result["data_year"].astype(int)
    result["utility_number"] = result["utility_number"].astype(int)
    result = result.sort_values(["data_year", "utility_name"]).reset_index(drop=True)

    both = int(result["reported_both_standards"].sum())
    result = result[FINAL_COLUMNS]

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out_path, index=False)

    # ---- quick checks printed to the screen ----
    print(f"\nSaved {len(result)} rows to {out_path}")
    print(f"Years: {sorted(result['data_year'].unique())}")
    print(f"Utilities per year:\n{result.groupby('data_year')['utility_name'].count().to_string()}")
    if both:
        print(f"Note: {both} rows reported under both standards (IEEE values used).")
    jmec = result[result["is_jmec"]]
    print("\nJMEC rows:")
    print(jmec[["data_year", "saidi_with_med", "saidi_without_med",
                "saifi_without_med", "customers", "reporting_standard"]].to_string(index=False))
    missing_years = sorted(set(result["data_year"]) - set(jmec["data_year"]))
    if missing_years:
        print(f"\nWARNING: JMEC not found in: {missing_years}")


if __name__ == "__main__":
    main()
