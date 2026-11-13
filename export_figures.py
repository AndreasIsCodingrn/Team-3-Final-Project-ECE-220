"""
export_figures.py
Owner: Julien Werzowa (Team Member 6) - Visualizations

Saves every chart to figures/ so we can drop them into the report and the
PowerPoint without having to screenshot the dashboard.

  - Always writes an interactive .html file for each chart.
  - Also writes a .png (good for slides) if the 'kaleido' package is installed:
        pip install kaleido

Usage (from the repo root):
    python export_figures.py
    python export_figures.py --out figures --scale 2
"""

import argparse
from pathlib import Path

from visualizations import (charts_acs, charts_burden, charts_heating, charts_rates, charts_reliability,
                            charts_solar_ev_grid, charts_summary)

# filename -> function that builds the figure. Numbered by dashboard section
# so they sort in the same order they show up in the report.
FIGURES = {
    "01_gap_chart": charts_summary.gap_chart,
    "02_locator_map": charts_summary.locator_map,
    "10_residential_rate_benchmark": charts_rates.residential_rate_benchmark,
    "11_sandoval_zip_rates": charts_rates.sandoval_zip_rates,
    "12_zip_utility_rates": charts_rates.zip_utility_rates,
    "13_jmec_price_trend": charts_rates.jmec_price_trend,
    "14_jmec_customers": lambda: charts_rates.jmec_customers_and_sales("customers"),
    "15_jmec_sales": lambda: charts_rates.jmec_customers_and_sales("sales_mwh"),
    "16_jmec_bill_vs_usage": charts_rates.jmec_bill_vs_usage,
    "20_heating_fuel_mix": charts_heating.heating_fuel_mix,
    "21_wood_and_propane": charts_heating.wood_and_propane_share,
    "22_heating_cost_by_system": charts_heating.heating_cost_by_system,
    "23_heat_pump_vs_propane": charts_heating.heat_pump_savings_vs_propane,
    "30_burden_by_income": charts_burden.burden_by_income,
    "31_burden_components": charts_burden.burden_components,
    "32_program_impact": charts_burden.program_impact,
    "33_rate_case_propane": lambda: charts_burden.rate_case_scenarios("Propane-heated home"),
    "34_rate_case_wood": lambda: charts_burden.rate_case_scenarios("Wood-heated home"),
    "35_high_burden_households": charts_burden.high_burden_households,
    "36_county_burden_map": lambda: charts_burden.county_choropleth("energy_burden_pct"),
    "37_county_rate_map": lambda: charts_burden.county_choropleth("res_rate_cents_kwh"),
    "38_county_rate_vs_burden": charts_burden.county_rate_vs_burden,
    "39_acs_median_income": charts_acs.median_income,
    "39b_acs_heating_fuel": charts_acs.heating_fuel,
    "39c_acs_fuel_gaps": charts_acs.fuel_gaps,
    "39d_village_vs_zip_heating": charts_acs.village_vs_zip_heating,
    "40_saidi_trend": lambda: charts_reliability.reliability_trend("saidi_without_med"),
    "41_saifi_trend": lambda: charts_reliability.reliability_trend("saifi_without_med"),
    "42_saidi_ranking": lambda: charts_reliability.reliability_ranking("saidi_without_med"),
    "43_saidi_vs_saifi": charts_reliability.saidi_vs_saifi,
    "44_jmec_med_impact": charts_reliability.jmec_med_impact,
    "50_solar_resource": charts_solar_ev_grid.solar_resource,
    "51_pv_output_check": charts_solar_ev_grid.pv_output_check,
    "52_ev_ports": charts_solar_ev_grid.ev_charging_ports,
    "53_ev_cost_per_mile": charts_solar_ev_grid.ev_cost_per_mile,
    "54_generation_mix": charts_solar_ev_grid.generation_mix,
    "55_co2_intensity": charts_solar_ev_grid.co2_intensity,
    "56_sandoval_generation": charts_solar_ev_grid.sandoval_generation,
    "60_eredux_cross_check": charts_summary.eredux_cross_check,
}


def main():
    parser = argparse.ArgumentParser(description="Export every dashboard chart to files.")
    parser.add_argument("--out", default="figures", help="Folder to save into (default: figures)")
    parser.add_argument("--scale", type=float, default=2, help="PNG resolution multiplier (2 = crisp on slides)")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # check once if kaleido is around, so we don't crash halfway through
    try:
        import kaleido  # noqa: F401
        can_png = True
    except ImportError:
        can_png = False
        print("kaleido not installed, saving HTML only (pip install kaleido for PNGs).")

    for name, build in FIGURES.items():
        fig = build()
        # the dashboard uses a transparent background, but slides need a solid white one
        # Arial for exports: the PNG renderer measures the system font wrong and clips long labels
        fig.update_layout(paper_bgcolor="white", plot_bgcolor="white", font_family="Arial")
        fig.write_html(out / f"{name}.html", include_plotlyjs="cdn")
        if can_png:
            fig.write_image(out / f"{name}.png", width=1100, height=fig.layout.height or 450, scale=args.scale)
        print(f"saved {name}")
    print(f"\nDone: {len(FIGURES)} figures in {out.resolve()}")


if __name__ == "__main__":
    main()
