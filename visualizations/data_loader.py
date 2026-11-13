"""
data_loader.py
Owner: Julien Werzowa (Team Member 6) - Visualizations

Every teammate saved their data in a slightly different JSON layout, so this
file is the "translator". Each function opens one of the team files, digs out
the part we need, and hands back a tidy pandas DataFrame (one row per thing,
one column per measurement). The chart functions only ever see these clean
tables, so if somebody changes their JSON later we only have to fix it here.

Files this reads (all in the repo root unless noted):
  - cuba_nm_energy_data.json                        (eRedux profiles, me)
  - cuba_nm_energy_research.json                    (solar / EV / eGRID notes, Christian)
  - cuba_nm_energy_burden.json                      (DOE LEAD burden, Andreas)
  - member2_cuba_nm_eia861_openei_consolidated.json (EIA-861 sales + JMEC tariffs, Mike)
  - reliability_nm.json                             (EIA-861 SAIDI/SAIFI, Jadon; CSV fallback)
  - Cuba_Benchmarking.json                          (ACS B19013 income + B25040 heating fuel, Lenny)
  - data/nm_counties.geojson                        (county outlines for the map)
"""

import json
import re
from functools import lru_cache
from pathlib import Path

import pandas as pd

# The repo root is one folder up from this file (visualizations/ -> repo root).
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"

# Labels I reuse everywhere so the same place is always spelled the same way.
CUBA = "Cuba (87013)"
JEMEZ_SPRINGS = "Jemez Springs (87025)"
RIO_RANCHO = "Rio Rancho (87124)"
SANDOVAL = "Sandoval County"
BERNALILLO = "Bernalillo County"
NEW_MEXICO = "New Mexico"
USA = "United States"

# Rough center points for the places we talk about, used to drop pins on the map.
# These are just the town centers (lat, lon), not exact zip boundaries.
PLACE_COORDS = {
    CUBA: (36.0206, -106.9584),
    JEMEZ_SPRINGS: (35.7706, -106.6923),
    RIO_RANCHO: (35.2834, -106.6640),
    "Albuquerque": (35.0844, -106.6504),
}


@lru_cache(maxsize=None)
def _load_json(filename: str) -> dict:
    """Opens a JSON file from the repo root. Cached so we only read each file once."""
    with open(REPO_ROOT / filename, encoding="utf-8") as f:
        return json.load(f)


def _eredux() -> dict:
    """Shortcut to the eRedux block inside the main energy data JSON."""
    return _load_json("cuba_nm_energy_data.json")["sources"]["eredux"]["data"]


def _find_file(name: str) -> Path:
    """
    Looks for a data file in data/ first and then in the repo root.
    Jadon's CSV has bounced between the root and a data folder on different
    branches, so this just checks both instead of crashing.
    """
    for folder in (DATA_DIR, REPO_ROOT):
        candidate = folder / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not find {name} in {DATA_DIR} or {REPO_ROOT}")


# ===========================================================================
# 1) ELECTRICITY RATES
# ===========================================================================

def residential_rate_benchmark() -> pd.DataFrame:
    """
    Residential electricity price (cents/kWh) for Cuba vs. the places we
    benchmark against. This is the core "where does Cuba stand" comparison
    from the proposal.

    Note: eRedux's Cuba number (15.97) is just the plain average of 3 utilities,
    but most of Cuba is actually on JMEC, so I add JMEC as its own bar too.
    """
    er = _eredux()
    counties = er["state_new_mexico"]["counties"]
    rows = [
        (CUBA + " - eRedux zip avg", er["zip_87013_cuba"]["rates"]["residential_cents_kwh"], "Cuba"),
        ("JMEC (serves most of Cuba)", er["zip_87013_cuba"]["rates"]["utilities"][1]["residential_cents_kwh"], "Cuba"),
        (SANDOVAL, er["county_sandoval"]["rates"]["residential_cents_kwh"], "Compare"),
        # The county list in the JSON is [population, residential rate, energy burden]
        (BERNALILLO, counties["Bernalillo"][1], "Compare"),
        (NEW_MEXICO, er["state_new_mexico"]["rates"]["residential_cents_kwh"], "Compare"),
        (USA, er["national"]["rates_2024"]["residential_cents_kwh"], "Compare"),
    ]
    return pd.DataFrame(rows, columns=["place", "cents_per_kwh", "group"])


def sandoval_zip_rates() -> pd.DataFrame:
    """Residential rate for every zip code in Sandoval County (eRedux)."""
    rates = _eredux()["comparison_zips"]["sandoval_zip_residential_rates_cents_kwh"]
    df = pd.DataFrame(list(rates.items()), columns=["zip", "cents_per_kwh"])
    return df.sort_values("cents_per_kwh").reset_index(drop=True)


def _short_utility(name: str) -> str:
    """Shortens the long utility names so chart legends don't run off the edge."""
    for long, short in (("Continental Divide", "Continental Divide Co-op"), ("Jemez", "JMEC"), ("NTUA", "NTUA")):
        if long in name:
            return short
    return name


def zip_utility_rates() -> pd.DataFrame:
    """
    The 3 utilities eRedux lists for zip 87013, broken out by customer sector.
    Long format (one row per utility per sector) so plotly can group the bars.
    """
    rows = []
    for u in _eredux()["zip_87013_cuba"]["rates"]["utilities"]:
        for sector in ("residential", "commercial", "industrial"):
            rows.append({
                "utility": _short_utility(u["utility"]),
                "sector": sector.title(),
                "cents_per_kwh": u[f"{sector}_cents_kwh"],
            })
    return pd.DataFrame(rows)


def jmec_sales_history() -> pd.DataFrame:
    """
    JMEC EIA-861 sales data from Mike's file, one row per year per sector.
    Columns: year, sector, sales_mwh, revenue_usd, customers, avg_price_cents_kwh.

    Only uses the years Mike marked as reconciled to the EIA files (2015-2025).
    2013-2014 are secondary summaries so they come in through a separate
    function and get drawn differently.
    """
    m = _load_json("member2_cuba_nm_eia861_openei_consolidated.json")
    rows = []
    for rec in m["eia_861"]["annual_sales_by_sector"]:
        for sector, vals in rec["sectors"].items():
            rows.append({
                "year": rec["year"],
                "sector": sector.title(),
                "sales_mwh": vals["sales_mwh"],
                "revenue_usd": vals["revenue_usd"],
                "customers": vals["customers"],
                "avg_price_cents_kwh": vals["average_price_cents_per_kwh"],
            })
    df = pd.DataFrame(rows)
    # Transportation is all zeros for JMEC, it just adds a flat line at 0.
    return df[df["sector"] != "Transportation"].reset_index(drop=True)


def jmec_secondary_history() -> pd.DataFrame:
    """2013-2014 residential price from the secondary (not fully verified) summaries."""
    m = _load_json("member2_cuba_nm_eia861_openei_consolidated.json")
    rows = []
    for rec in m["eia_861"]["historical_summaries_pending_primary_reconciliation"]:
        s = rec["historical_summary_not_suitable_as_exact_sector_totals"]
        rows.append({
            "year": rec["year"],
            "avg_price_cents_kwh": s["residential_average_price_cents_per_kwh"],
            "nm_avg_price_cents_kwh": s.get("new_mexico_residential_average_price_cents_per_kwh"),
        })
    return pd.DataFrame(rows)


def jmec_residential_tariffs() -> dict:
    """
    Pulls the residential tariff pieces (monthly facility charge + the two
    energy tiers) for the current 2026 rate and the scheduled 2029 rate.
    Returns a dict like {"2026 (effective Sep 2026)": {...}, "2029 (scheduled)": {...}}.
    """
    t = _load_json("member2_cuba_nm_eia861_openei_consolidated.json")["jmec_published_tariffs"]
    out = {}
    for label, block in (("2026 tariff (effective Sep 2026)", "effective_2026"),
                         ("2029 tariff (scheduled)", "scheduled_2029_not_yet_effective")):
        res = next(r for r in t[block] if r["sector"] == "residential")
        tiers = res["standard_energy_tiers"]
        out[label] = {
            "facility_usd": res["facility_charge_usd_per_month"],
            "tier1_limit_kwh": tiers[0]["max_kwh_inclusive"],
            "tier1_usd_kwh": tiers[0]["usd_per_kwh"],
            "tier2_usd_kwh": tiers[1]["usd_per_kwh"],
        }
    return out


# ===========================================================================
# 2) HOME HEATING
# ===========================================================================

# JSON key -> label I want on the chart
_FUEL_KEYS = {
    "natural_gas_pct": "Natural gas",
    "electricity_pct": "Electricity",
    "propane_pct": "Propane",
    "wood_pct": "Wood",
    "fuel_oil_pct": "Fuel oil",
    "other_pct": "Other / solar",
    "solar_pct": "Other / solar",
}


def heating_fuel_mix() -> pd.DataFrame:
    """
    Share of homes by main heating fuel (percent), long format:
    columns = place, fuel, pct.

    Whatever doesn't add up to 100% goes into "Not reported". This matters a lot
    for Sandoval County because eRedux only shows 3 fuels there (86.9% total),
    so a chunk of the bar is honestly just "we don't know yet". Lenny's ACS
    B25040 numbers (acs_heating_fuel below) only come in 3 grouped categories
    and cover the Cuba *village*, not the zip, so they sit next to this instead
    of replacing it.
    """
    er = _eredux()
    sources = {
        CUBA: er["zip_87013_cuba"]["heating_fuel"],
        JEMEZ_SPRINGS: er["comparison_zips"]["87025_jemez_springs"]["heating_fuel"],
        RIO_RANCHO: er["comparison_zips"]["87124_rio_rancho"]["heating_fuel"],
        SANDOVAL: er["county_sandoval"]["heating_fuel"],
        NEW_MEXICO: er["state_new_mexico"]["heating_fuel"],
        USA: er["national"]["heating_fuel"],
    }
    rows = []
    for place, fuels in sources.items():
        totals = {}
        for key, label in _FUEL_KEYS.items():
            val = fuels.get(key)
            if val is not None:
                totals[label] = totals.get(label, 0) + val
        # whatever is left over to get to 100% is unknown/rounding
        leftover = round(100 - sum(totals.values()), 1)
        if leftover > 0.4:
            totals["Not reported"] = leftover
        for fuel, pct in totals.items():
            rows.append({"place": place, "fuel": fuel, "pct": pct,
                         "housing_units": fuels.get("housing_units")})
    return pd.DataFrame(rows)


def heating_cost_estimates() -> pd.DataFrame:
    """
    eRedux's modeled yearly heating cost for a ~2,000 sq ft home by heating
    system type. Colder places (more heating degree days) cost more to heat,
    which is why Cuba is the most expensive in every column.
    """
    er = _eredux()
    sources = {
        CUBA: er["zip_87013_cuba"]["heating_cost_estimates"],
        JEMEZ_SPRINGS: er["comparison_zips"]["87025_jemez_springs"]["heating_cost_estimates"],
        SANDOVAL: er["county_sandoval"]["heating_cost_estimates"],
        RIO_RANCHO: er["comparison_zips"]["87124_rio_rancho"]["heating_cost_estimates"],
    }
    systems = {
        "natural_gas_furnace_usd_yr": "Natural gas furnace",
        "heat_pump_usd_yr": "Heat pump",
        "propane_furnace_usd_yr": "Propane furnace",
        "electric_resistance_usd_yr": "Electric resistance",
    }
    rows = []
    for place, est in sources.items():
        for key, label in systems.items():
            rows.append({"place": place, "system": label, "usd_per_year": est[key],
                         "heating_degree_days": est["heating_degree_days"]})
    return pd.DataFrame(rows)


# ===========================================================================
# 3) ENERGY BURDEN (DOE LEAD, Andreas's file)
# ===========================================================================

def burden_metadata() -> dict:
    """The threshold (6%) and the caveats list, so charts can quote them."""
    return _load_json("cuba_nm_energy_burden.json")["metadata"]


def burden_by_income() -> pd.DataFrame:
    """
    Energy burden (% of income spent on home energy) by income bracket for
    the Cuba census tract (Tract 109) and for all of New Mexico.
    Columns: area, ami_bracket, households, income, energy_cost, burden_pct,
             electric_pct, gas_pct, other_pct
    """
    b = _load_json("cuba_nm_energy_burden.json")
    rows = []
    for area, key in (("Cuba area (Tract 109)", "cuba_tract_109_income_vs_burden"),
                      (NEW_MEXICO, "statewide_income_vs_burden")):
        for r in b[key]:
            rows.append({
                "area": area,
                "ami_bracket": r["ami_bracket"] + " AMI",
                "households": r["households"],
                "income": r["household_income_usd"],
                "energy_cost": r["avg_annual_energy_cost_usd"],
                "burden_pct": r["computed_burden_pct"],
                "electric_pct": r["lead_electric_burden_pct"],
                "gas_pct": r["lead_gas_burden_pct"],
                "other_pct": r["lead_other_burden_pct"],
            })
    return pd.DataFrame(rows)


def burden_program_impact() -> pd.DataFrame:
    """
    For each income bracket in Tract 109: the burden before any help, after
    each program on its own, and after stacking every program the household
    qualifies for. Long format: ami_bracket, scenario, burden_pct, savings_usd.
    """
    b = _load_json("cuba_nm_energy_burden.json")
    names = {"weatherization": "Weatherization", "solar_for_all": "Solar for All", "liheap": "LIHEAP"}
    rows = []
    for r in b["cuba_tract_109_income_vs_burden"]:
        imp = r["impact"]
        bracket = r["ami_bracket"] + " AMI"
        rows.append({"ami_bracket": bracket, "scenario": "Baseline",
                     "burden_pct": imp["baseline_burden_pct"], "savings_usd": 0})
        for key, label in names.items():
            sol = imp["solutions"].get(key, {})
            # if the household isn't eligible the program does nothing for them
            if sol.get("eligible"):
                rows.append({"ami_bracket": bracket, "scenario": label,
                             "burden_pct": sol["new_burden_pct"], "savings_usd": sol["annual_savings_usd"]})
        combo = imp.get("all_eligible_combined") or {}
        rows.append({"ami_bracket": bracket, "scenario": "All eligible combined",
                     "burden_pct": combo.get("new_burden_pct", imp["baseline_burden_pct"]),
                     "savings_usd": combo.get("annual_savings_usd", 0)})
    return pd.DataFrame(rows)


def burden_rate_case_scenarios() -> pd.DataFrame:
    """
    How burden changes for typical Cuba households as JMEC's rates go up
    (present -> phase 1 -> phase 2). Split by wood-heated vs propane-heated homes.
    """
    b = _load_json("cuba_nm_energy_burden.json")
    pretty_income = {
        "lead_0-30%_income": "0-30% AMI",
        "lead_30-60%_income": "30-60% AMI",
        "cuba_median_income": "Cuba median income",
        "lead_60-80%_income": "60-80% AMI",
    }
    pretty_case = {"present": "Present rates", "phase1": "Rate phase 1", "phase2": "Rate phase 2"}
    rows = []
    for s in b["cuba_87013_scenarios"]:
        for case, vals in s["rate_case"].items():
            rows.append({
                "heating": "Wood-heated home" if s["archetype"] == "wood_heat" else "Propane-heated home",
                "income_group": pretty_income.get(s["income_label"], s["income_label"]),
                "household_income": s["household_income_usd"],
                "rate_case": pretty_case[case],
                "annual_cost_usd": vals["annual_cost_usd"],
                "burden_pct": vals["burden_pct"],
            })
    return pd.DataFrame(rows)


def burden_summaries() -> dict:
    """The headline numbers (households, high-burden counts, savings) for stat tiles."""
    b = _load_json("cuba_nm_energy_burden.json")
    return {"cuba": b["cuba_tract_109_summary"], "state": b["statewide_summary"]}


def weighted_average_burden(area: str) -> float:
    """
    Household-weighted average burden for one area = total energy dollars /
    total income dollars. I do it this way instead of averaging the bracket
    percentages, because a bracket with 300 households should count more
    than one with 50.
    """
    df = burden_by_income()
    df = df[df["area"] == area]
    total_cost = (df["households"] * df["energy_cost"]).sum()
    total_income = (df["households"] * df["income"]).sum()
    return 100 * total_cost / total_income


def county_profiles() -> pd.DataFrame:
    """
    Every NM county with population, residential rate, and energy burden
    (from the eRedux state page). This feeds the county maps.
    """
    counties = _eredux()["state_new_mexico"]["counties"]
    rows = [{"county": name, "population": v[0], "res_rate_cents_kwh": v[1], "energy_burden_pct": v[2]}
            for name, v in counties.items()]
    return pd.DataFrame(rows)


@lru_cache(maxsize=None)
def nm_county_geojson() -> dict:
    """County outlines for NM. Census county FIPS is the 'id' of each shape."""
    with open(_find_file("nm_counties.geojson"), encoding="utf-8") as f:
        return json.load(f)


def county_fips_lookup() -> dict:
    """
    Maps county name -> 5 digit FIPS code using the geojson. The geojson spells
    it 'Doña Ana' with the tilde and eRedux spells it 'Dona Ana', so I strip
    the tilde to make them match.
    """
    out = {}
    for feat in nm_county_geojson()["features"]:
        name = feat["properties"]["NAME"].replace("ñ", "n")
        out[name] = feat["id"]
    return out


# ===========================================================================
# 4) RELIABILITY (EIA-861 SAIDI / SAIFI, Jadon's CSV)
# ===========================================================================

def reliability() -> pd.DataFrame:
    """
    Jadon's cleaned EIA-861 reliability table for every NM utility, every year.

    Quick refresher on the metrics (IEEE 1366):
      SAIDI = average outage MINUTES per customer per year (duration)
      SAIFI = average number of outages per customer per year (frequency)
      CAIDI = SAIDI / SAIFI = average minutes to restore once you lose power
      "with MED" includes Major Event Days (big storms / fires), "without MED"
      takes those out to show normal, day-to-day performance.
    """
    # Jadon uploaded a JSON version to the repo root; the older CSV in data/ has
    # the same 177 rows, so it's kept only as a fallback.
    try:
        df = pd.DataFrame(_load_json("reliability_nm.json"))
    except FileNotFoundError:
        df = pd.read_csv(_find_file("reliability_nm.csv"))
    # make the names readable on a chart (EIA abbreviates a lot)
    short = {
        "Jemez Mountains Elec Coop, Inc": "JMEC (Jemez Mountains)",
        "Public Service Co of NM": "PNM",
        "Central New Mexico El Coop, Inc": "Central NM Co-op",
        "Central Valley Elec Coop, Inc": "Central Valley Co-op",
        "Continental Divide El Coop Inc": "Continental Divide Co-op",
        "El Paso Electric Co": "El Paso Electric",
        "Farmers Electric Coop, Inc": "Farmers Co-op",
        "Kit Carson Electric Coop, Inc": "Kit Carson Co-op",
        "Lea County Electric Coop, Inc": "Lea County Co-op",
        "Navajo Tribal Utility Authority": "NTUA",
        "Rio Grande Electric Coop, Inc": "Rio Grande Co-op",
        "Southwestern Public Service Co": "SPS (Xcel)",
        "Mora-San Miguel Elec Coop": "Mora-San Miguel Co-op",
        "Northern Rio Arriba E Coop Inc": "Northern Rio Arriba Co-op",
        "Sierra Electric Coop, Inc": "Sierra Co-op",
    }
    df["utility"] = df["utility_name"].map(short).fillna(df["utility_name"])
    df["is_jmec"] = df["is_jmec"].astype(str).str.lower() == "true"
    return df


# ===========================================================================
# 4b) CENSUS ACS INCOME + HEATING FUEL (Lenny's benchmarking file)
# ===========================================================================
# Lenny's file is a Word doc converted to JSON, so every number is a string
# like "$58,750", "22.6%" or "−$27,886" (with a unicode minus). These helpers
# find the right table by its columns and turn the strings into numbers.

CUBA_VILLAGE = "Cuba village"

_ACS_FILE = "Cuba_Benchmarking.json"
_ACS_GEOS = (("Cuba village", CUBA_VILLAGE), ("Sandoval County", SANDOVAL), ("New Mexico", NEW_MEXICO))


def _to_number(text: str) -> float:
    """'$58,750' -> 58750.0, '−10.8 pp' -> -10.8, '22.6%' -> 22.6"""
    cleaned = text.replace("−", "-").replace("$", "").replace(",", "").replace("%", "").replace("pp", "")
    return float(cleaned.strip())


def _acs_blocks() -> list:
    """Every block (table, note, list item) from every section, with its section heading attached."""
    doc = _load_json(_ACS_FILE)["document"]
    return [dict(block, section=s["heading"]) for s in doc["sections"] for block in s["blocks"]]


def _acs_table(first_column: str) -> list:
    """The rows of the first table whose first column header matches."""
    for block in _acs_blocks():
        if block["type"] == "table" and block["columns"][0] == first_column:
            return block["rows"]
    raise KeyError(f"No table starting with column '{first_column}' in {_ACS_FILE}")


def acs_benchmarks() -> pd.DataFrame:
    """
    The 'Benchmarks at a glance' table, one row per geography:
    columns = place, median_income, occupied_units, gas_pct, electric_pct, other_pct.

    gas = utility gas + bottled/tank gas (propane) combined, the way the source groups it.
    """
    fields = {
        "Median household income": "median_income",
        "Occupied housing units": "occupied_units",
        "Homes primarily heated by gas": "gas_pct",
        "Homes primarily heated by electricity": "electric_pct",
        "Homes primarily heated by all other fuels": "other_pct",
    }
    rows = {label: {"place": label} for _, label in _ACS_GEOS}
    for r in _acs_table("Indicator"):
        field = next((v for k, v in fields.items() if r["Indicator"].startswith(k)), None)
        if field is None:
            continue
        for col, label in _ACS_GEOS:
            rows[label][field] = _to_number(r[col])
    return pd.DataFrame(rows.values())


def acs_income_moe() -> float | None:
    """
    Cuba's 90% margin of error on median income. It's only written in a
    sentence in the limitations list ("±$46,069"), so pull it out with a regex.
    """
    for block in _acs_blocks():
        m = re.search(r"margin of error of approximately ±\$([\d,]+)", block.get("text", ""))
        if m:
            return _to_number(m.group(1))
    return None


_ACS_FUELS = {"Gas (combined)": "Gas (utility + bottled)", "Electricity": "Electricity",
              "All other fuels": "All other fuels"}


def acs_heating_fuel() -> pd.DataFrame:
    """
    ACS B25040 heating fuel shares in long format: place, fuel, pct.
    The three groups don't always add to 100 (solar, oil and 'no fuel' are
    split out in the source), so the leftover goes into 'Not listed'.
    """
    rows = []
    for _, r in acs_benchmarks().iterrows():
        shares = {"Gas (utility + bottled)": r["gas_pct"], "Electricity": r["electric_pct"],
                  "All other fuels": r["other_pct"]}
        leftover = round(100 - sum(shares.values()), 1)
        if leftover > 0.4:
            shares["Not listed"] = leftover
        for fuel, pct in shares.items():
            rows.append({"place": r["place"], "fuel": fuel, "pct": pct, "housing_units": r["occupied_units"]})
    return pd.DataFrame(rows)


def acs_income_gaps() -> pd.DataFrame:
    """The dollar and % income gaps table (Cuba - county, Cuba - state, county - state)."""
    rows = [{"comparison": r["Comparison"], "dollar_gap": _to_number(r["Dollar difference"]),
             "relative_gap_pct": _to_number(r["Relative gap"])} for r in _acs_table("Comparison")]
    return pd.DataFrame(rows)


def acs_fuel_gaps() -> pd.DataFrame:
    """Percentage-point gaps in heating fuel share, Cuba vs. county and vs. state."""
    rows = [{"fuel": _ACS_FUELS[r["Fuel category"]],
             "cuba_minus_county_pp": _to_number(r["Cuba − county"]),
             "cuba_minus_state_pp": _to_number(r["Cuba − state"])} for r in _acs_table("Fuel category")]
    return pd.DataFrame(rows)


def acs_rankings() -> pd.DataFrame:
    """The three-way ranking table exactly as Lenny wrote it."""
    return pd.DataFrame(_acs_table("Metric"))


def acs_summary() -> str:
    """The executive summary paragraph."""
    return next(b["text"] for b in _acs_blocks() if b["section"] == "Executive summary")


def acs_limitations() -> list:
    """The bullet list from 'Interpretation and limitations'."""
    return [b["text"] for b in _acs_blocks() if b["type"] == "list_item"]


def acs_vs_eredux_heating() -> pd.DataFrame:
    """
    Puts the two Cuba heating estimates side by side using the only categories
    both sources can be collapsed into (gas incl. propane / electricity / everything else):
      - ACS B25040 for Cuba village (159 occupied homes)
      - eRedux for zip 87013 (1,586 homes, includes all the rural area around the village)
    These disagree a LOT on wood/other heat, which is the whole point of the chart.
    """
    er = _eredux()["zip_87013_cuba"]["heating_fuel"]
    gas = (er.get("natural_gas_pct") or 0) + (er.get("propane_pct") or 0)
    elec = er.get("electricity_pct") or 0
    zip_rows = {"Gas (utility + bottled)": gas, "Electricity": elec, "All other fuels": 100 - gas - elec}
    acs = acs_benchmarks().set_index("place").loc[CUBA_VILLAGE]
    village_rows = {"Gas (utility + bottled)": acs["gas_pct"], "Electricity": acs["electric_pct"],
                    "All other fuels": acs["other_pct"]}
    rows = []
    for source, shares, units in (
            (f"ACS: Cuba village ({acs['occupied_units']:,.0f} homes)", village_rows, acs["occupied_units"]),
            (f"eRedux: zip 87013 ({er['housing_units']:,} homes)", zip_rows, er["housing_units"])):
        for fuel, pct in shares.items():
            rows.append({"source": source, "fuel": fuel, "pct": pct, "housing_units": units})
    return pd.DataFrame(rows)


# ===========================================================================
# 5) SOLAR, EV CHARGING, GRID MIX
# ===========================================================================

def solar_resource() -> pd.DataFrame:
    """Solar resource (kWh per m^2 per day) for Cuba vs. the comparison zips and the US average."""
    er = _eredux()
    rows = []
    for place, s in ((CUBA, er["zip_87013_cuba"]["solar_resource"]),
                     (JEMEZ_SPRINGS, er["comparison_zips"]["87025_jemez_springs"]["solar_resource"]),
                     (RIO_RANCHO, er["comparison_zips"]["87124_rio_rancho"]["solar_resource"])):
        rows.append({"place": place, "ghi": s["ghi_kwh_m2_day"], "tilt": s["tilt_kwh_m2_day"], "rating": s["rating"]})
    rows.append({"place": USA + " avg", "ghi": er["zip_87013_cuba"]["solar_resource"]["us_avg_kwh_m2_day"],
                 "tilt": None, "rating": ""})
    return pd.DataFrame(rows)


def pv_estimate(system_kw: float = 6.0, derate: float = 0.80) -> dict:
    """
    Back-of-the-envelope yearly output of a rooftop PV system in Cuba.

        kWh/yr = system size (kW) x peak sun hours (kWh/m^2/day) x 365 x derate

    Peak sun hours = the tilted-plane irradiance, because 1 kW/m^2 is the
    standard test condition panels are rated at. The derate (~0.80) lumps
    inverter losses, wiring, soiling, and heat. This is the same idea as
    NREL PVWatts but way simpler, so it's only a sanity check.

    I compare it to eRedux's 2,385 kWh/yr, which the team flagged as way too
    low, and price the output at JMEC's first-tier residential energy rate.
    """
    er = _eredux()["zip_87013_cuba"]["solar_resource"]
    psh = er["tilt_kwh_m2_day"]
    our_kwh = system_kw * psh * 365 * derate
    tier1 = jmec_residential_tariffs()["2026 tariff (effective Sep 2026)"]["tier1_usd_kwh"]
    return {
        "system_kw": system_kw,
        "peak_sun_hours": psh,
        "derate": derate,
        "first_order_kwh_yr": our_kwh,
        "eredux_kwh_yr": er["est_6kw_system_kwh_yr"],
        "jmec_tier1_usd_kwh": tier1,
        "first_order_value_usd_yr": our_kwh * tier1,
        "capacity_factor_pct": 100 * our_kwh / (system_kw * 8760),
    }


def ev_charging() -> pd.DataFrame:
    """Public EV charging stations and ports by place (eRedux + MyTownView for Cuba)."""
    er = _eredux()
    research = _load_json("cuba_nm_energy_research.json")["assigned_research"]["afdc_ev_stations"]
    rows = [
        {"place": CUBA + " - eRedux", "stations": er["zip_87013_cuba"]["ev"]["stations"],
         "ports": er["zip_87013_cuba"]["ev"]["total_ports"], "group": "Cuba"},
        {"place": CUBA + " - MyTownView", "stations": research["mytownview"]["stations"],
         "ports": research["mytownview"]["dc_fast_ports"], "group": "Cuba"},
        {"place": JEMEZ_SPRINGS, "stations": er["comparison_zips"]["87025_jemez_springs"]["ev"]["stations"],
         "ports": er["comparison_zips"]["87025_jemez_springs"]["ev"]["total_ports"], "group": "Compare"},
        {"place": RIO_RANCHO, "stations": er["comparison_zips"]["87124_rio_rancho"]["ev"]["stations"],
         "ports": er["comparison_zips"]["87124_rio_rancho"]["ev"]["total_ports"], "group": "Compare"},
    ]
    return pd.DataFrame(rows)


def ev_ports_per_10k() -> pd.DataFrame:
    """
    EV ports per 10,000 residents for Sandoval County and New Mexico. We don't
    have a zip-level population in the data yet, so Cuba isn't on this one.
    """
    er = _eredux()
    rows = [
        {"place": SANDOVAL, "ports": er["county_sandoval"]["ev"]["total_ports"],
         "population": er["county_sandoval"]["population"]},
        {"place": NEW_MEXICO, "ports": er["state_new_mexico"]["ev"]["total_ports"],
         "population": er["state_new_mexico"]["population"]},
    ]
    df = pd.DataFrame(rows)
    df["ports_per_10k"] = 1e4 * df["ports"] / df["population"]
    return df


def ev_vs_gas() -> pd.DataFrame:
    """Cost per mile of driving (cents/mile): home EV charging vs. public DC fast vs. a 28 mpg gas car."""
    r = _load_json("cuba_nm_energy_research.json")["other_team_research"]["ev_vs_gas_cost"]
    return pd.DataFrame([
        {"option": "EV, home charging", "cents_per_mile": r["home_ev_cost_cents_per_mile"]},
        {"option": "EV, public DC fast", "cents_per_mile": r["public_dc_fast_charging_cost_cents_per_mile"]},
        {"option": "Gas car (28 mpg)", "cents_per_mile": r["gas_car_cost_cents_per_mile"]},
    ])


def generation_mix() -> pd.DataFrame:
    """
    Where the electricity comes from (percent by fuel) for:
      - the eGRID subregion eRedux assigns to Cuba (NWPP)
      - the AZNM subregion the neighboring zips are in
      - power plants physically located in New Mexico (2024)
      - power plants physically located in Sandoval County (2024)
    Anything that doesn't add to 100 goes into "Unaccounted".
    """
    er = _eredux()
    label = {"natural_gas": "Natural gas", "coal": "Coal", "nuclear": "Nuclear",
             "hydro": "Hydro", "wind": "Wind", "solar": "Solar"}
    sources = {
        "NWPP subregion (eRedux for Cuba)": er["zip_87013_cuba"]["egrid"]["mix_pct"],
        "AZNM subregion (nearby zips)": er["comparison_zips"]["87025_jemez_springs"]["egrid"]["mix_pct"],
        "NM in-state generation 2024": er["state_new_mexico"]["generation_2024_pct"],
        "Sandoval County plants 2024": er["county_sandoval"]["generation_2024"]["mix_pct"],
    }
    rows = []
    for region, mix in sources.items():
        total = sum(mix.values())
        for fuel, pct in mix.items():
            rows.append({"region": region, "source": label[fuel], "pct": pct})
        if total < 99.5:
            rows.append({"region": region, "source": "Unaccounted", "pct": round(100 - total, 1)})
    return pd.DataFrame(rows)


def co2_intensity() -> pd.DataFrame:
    """CO2 emission rate (lb per MWh) for the grid regions, eRedux vs EPA eGRID where we have both."""
    research = _load_json("cuba_nm_energy_research.json")["assigned_research"]["epa_egrid"]
    er = _eredux()
    return pd.DataFrame([
        {"region": "NWPP subregion", "lb_per_mwh": research["epa_egrid2023_revision2_nwpp_co2_lb_per_mwh"]},
        {"region": "AZNM subregion", "lb_per_mwh": research["epa_egrid2023_revision2_aznm_co2_lb_per_mwh"]},
        {"region": "New Mexico (2022)", "lb_per_mwh": er["state_new_mexico"]["co2_2022"]["lbs_per_mwh"]},
    ])


# ===========================================================================
# 6) CROSS-CHECKS AND THE BIG GAP SUMMARY
# ===========================================================================

def eredux_cross_check() -> pd.DataFrame:
    """
    My data-source job was to cross-check eRedux against the federal originals.
    This lines up every number where we have both, and computes the % diff:
        pct_diff = 100 x (eRedux - federal) / federal
    """
    er = _eredux()
    research = _load_json("cuba_nm_energy_research.json")["assigned_research"]["epa_egrid"]
    sales = jmec_sales_history()
    res = sales[sales["sector"] == "Residential"].set_index("year")["avg_price_cents_kwh"]
    latest = int(res.index.max())

    rows = [
        {"metric": f"JMEC residential price (EIA-861 {latest})", "unit": "cents/kWh",
         "eredux": er["zip_87013_cuba"]["rates"]["utilities"][1]["residential_cents_kwh"],
         "federal": round(float(res.loc[latest]), 2)},
        {"metric": "JMEC residential price (EIA-861 2024)", "unit": "cents/kWh",
         "eredux": er["zip_87013_cuba"]["rates"]["utilities"][1]["residential_cents_kwh"],
         "federal": round(float(res.loc[2024]), 2)},
        {"metric": "NWPP CO2 rate (eGRID 2023)", "unit": "lb/MWh",
         "eredux": er["zip_87013_cuba"]["egrid"]["co2_lbs_per_mwh"],
         "federal": research["epa_egrid2023_revision2_nwpp_co2_lb_per_mwh"]},
        {"metric": "AZNM CO2 rate (eGRID 2023)", "unit": "lb/MWh",
         "eredux": er["comparison_zips"]["87025_jemez_springs"]["egrid"]["co2_lbs_per_mwh"],
         "federal": research["epa_egrid2023_revision2_aznm_co2_lb_per_mwh"]},
        {"metric": "6 kW rooftop PV output (vs. first-order estimate)", "unit": "kWh/yr",
         "eredux": er["zip_87013_cuba"]["solar_resource"]["est_6kw_system_kwh_yr"],
         "federal": round(pv_estimate()["first_order_kwh_yr"])},
    ]
    df = pd.DataFrame(rows).drop_duplicates(subset="metric")
    df["pct_diff"] = 100 * (df["eredux"] - df["federal"]) / df["federal"]
    return df


def gap_summary() -> pd.DataFrame:
    """
    The big benchmarking table: Cuba's value next to New Mexico's for every
    metric we actually have data for, plus the % gap.

    higher_is_worse tells the chart which direction is bad for residents.
    For example a higher electric rate is bad, but more sunshine is good.

    gap_pct = 100 x (Cuba - NM) / NM, then flipped to "how much worse" so
    positive always means Cuba is behind, which makes the chart read the same
    way for every row.
    """
    er = _eredux()
    rel = reliability()
    latest = rel["data_year"].max()
    rel_latest = rel[rel["data_year"] == latest]
    jmec = rel_latest[rel_latest["is_jmec"]].iloc[0]
    others = rel_latest[~rel_latest["is_jmec"]]
    acs = acs_benchmarks().set_index("place")

    rows = [
        ("Median household income", "$/year",
         acs.loc[CUBA_VILLAGE, "median_income"], acs.loc[NEW_MEXICO, "median_income"], False,
         "ACS B19013, Cuba village vs NM (Cuba MOE ±$46k)"),
        ("Residential electric rate", "cents/kWh",
         er["zip_87013_cuba"]["rates"]["residential_cents_kwh"], er["state_new_mexico"]["rates"]["residential_cents_kwh"], True,
         "eRedux zip average vs NM"),
        ("Energy burden (household-weighted)", "% of income",
         weighted_average_burden("Cuba area (Tract 109)"), weighted_average_burden(NEW_MEXICO), True,
         "DOE LEAD, Tract 109 vs NM"),
        ("Homes heated with wood", "% of homes",
         er["zip_87013_cuba"]["heating_fuel"]["wood_pct"], er["state_new_mexico"]["heating_fuel"]["wood_pct"], True,
         "eRedux/ACS"),
        ("Homes heated with propane", "% of homes",
         er["zip_87013_cuba"]["heating_fuel"]["propane_pct"], er["state_new_mexico"]["heating_fuel"]["propane_pct"], True,
         "eRedux/ACS"),
        (f"Outage minutes, SAIDI w/o MED ({latest})", "min/customer",
         jmec["saidi_without_med"], others["saidi_without_med"].median(), True,
         "JMEC vs median NM utility"),
        (f"Outages/customer, SAIFI w/o MED ({latest})", "outages/yr",
         jmec["saifi_without_med"], others["saifi_without_med"].median(), True,
         "JMEC vs median NM utility"),
        ("Solar resource (GHI)", "kWh/m²/day",
         er["zip_87013_cuba"]["solar_resource"]["ghi_kwh_m2_day"], er["zip_87013_cuba"]["solar_resource"]["us_avg_kwh_m2_day"], False,
         "vs US average (NM value not in data)"),
    ]
    df = pd.DataFrame(rows, columns=["metric", "unit", "cuba", "benchmark", "higher_is_worse", "basis"])
    raw_gap = 100 * (df["cuba"] - df["benchmark"]) / df["benchmark"]
    # flip sign for metrics where higher is better, so + always = Cuba worse off
    df["worse_by_pct"] = raw_gap.where(df["higher_is_worse"], -raw_gap)
    # Same idea as a ratio (1.0 = same as benchmark, 2.0 = twice as bad).
    # Wood heat is ~10x the state share, which squashes every other bar on a
    # plain % axis, so the chart uses this ratio on a log scale instead.
    ratio = df["cuba"] / df["benchmark"]
    df["worse_ratio"] = ratio.where(df["higher_is_worse"], 1 / ratio)
    return df.sort_values("worse_ratio", ascending=True).reset_index(drop=True)


def data_quality_flags() -> list:
    """
    The data quality warnings the team wrote into the main JSON, plus one I
    add from comparing Lenny's ACS village numbers with eRedux's zip numbers.
    """
    flags = list(_load_json("cuba_nm_energy_data.json")["data_quality_flags"])
    try:
        cmp = acs_vs_eredux_heating().pivot(index="fuel", columns="source", values="pct")
        village, zipcode = sorted(cmp.columns)  # "ACS: ..." sorts before "eRedux: ..."
        flags.append(
            f"Heating fuel: ACS B25040 puts 'all other fuels' (wood included) at "
            f"{cmp.loc['All other fuels', village]:.1f}% of Cuba village homes, but eRedux puts wood alone at "
            f"{_eredux()['zip_87013_cuba']['heating_fuel']['wood_pct']}% for zip 87013. They are different "
            "geographies (159 village homes vs 1,586 zip homes) and the village estimate has a large margin "
            "of error, so the wood-heat finding is a zip-level (rural) result, not a village one.")
    except (FileNotFoundError, KeyError):
        pass
    return flags
