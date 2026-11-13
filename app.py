"""
app.py
Streamlit dashboard: Energy Affordability, Access, and Reliability in Cuba, NM (Team 3)

Charts by Julien Werzowa (Team Member 6). This file is the layout that plugs
every chart from the visualizations/ folder into Streamlit tabs. Christian can
rearrange or restyle it, the chart functions don't care where they get placed.

Run it from the repo root with:
    pip install -r requirements.txt
    streamlit run app.py
Then Streamlit opens it in the browser at http://localhost:8501
"""

import streamlit as st

from visualizations import (charts_acs, charts_burden, charts_heating, charts_rates, charts_reliability,
                            charts_solar_ev_grid, charts_summary, data_loader)

# wide layout so side-by-side charts actually have room
st.set_page_config(page_title="Cuba, NM Energy Dashboard", layout="wide")


def show(fig):
    """
    Small helper so every chart gets drawn the same way (full column width).
    Newer Streamlit wants width="stretch" and older versions only know
    use_container_width, so this tries the new way first and falls back.
    """
    try:
        st.plotly_chart(fig, width="stretch")
    except TypeError:
        st.plotly_chart(fig, use_container_width=True)


st.title("Energy Affordability, Access, and Reliability in Cuba, New Mexico")
st.caption("ECE 220 Team 3. Cuba (zip 87013) benchmarked against Sandoval County, Bernalillo County, "
           "New Mexico, and the US.")

# The tabs line up with the topics in our project proposal.
tabs = st.tabs(["Overview", "Electricity rates", "Home heating", "Energy burden", "Income (ACS)",
                "Reliability", "Solar, EV & grid", "Data quality"])

# ---------------------------------------------------------------------------
# OVERVIEW: headline numbers + the gap chart that sums up the whole project
# ---------------------------------------------------------------------------
with tabs[0]:
    gaps = data_loader.gap_summary().set_index("metric")
    pv = data_loader.pv_estimate()
    burden = data_loader.burden_summaries()["cuba"]

    # stat tiles across the top, these are the 4 numbers I'd want someone to remember
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Homes heated with wood", f"{gaps.loc['Homes heated with wood', 'cuba']:.0f}%",
              f"vs {gaps.loc['Homes heated with wood', 'benchmark']:.1f}% in NM", delta_color="off")
    saidi_row = [m for m in gaps.index if m.startswith("Outage minutes")][0]
    c2.metric("JMEC outage minutes / customer", f"{gaps.loc[saidi_row, 'cuba']:,.0f}",
              f"NM median {gaps.loc[saidi_row, 'benchmark']:,.0f} (no major events)", delta_color="off")
    c3.metric("High-burden households (Tract 109)",
              f"{burden['high_burden_households_before']} of {burden['total_households']}",
              "above 6% of income on energy", delta_color="off")
    c4.metric("6 kW rooftop PV output", f"~{pv['first_order_kwh_yr']:,.0f} kWh/yr",
              f"≈ ${pv['first_order_value_usd_yr']:,.0f}/yr at JMEC rates", delta_color="off")

    left, right = st.columns([3, 2])
    with left:
        show(charts_summary.gap_chart())
    with right:
        show(charts_summary.locator_map())
    with st.expander("Gap chart as a table"):
        st.dataframe(charts_summary.gap_table(), hide_index=True)

# ---------------------------------------------------------------------------
# RATES
# ---------------------------------------------------------------------------
with tabs[1]:
    left, right = st.columns(2)
    with left:
        show(charts_rates.residential_rate_benchmark())
    with right:
        show(charts_rates.sandoval_zip_rates())
    show(charts_rates.jmec_price_trend())
    left, right = st.columns(2)
    with left:
        show(charts_rates.jmec_bill_vs_usage())
    with right:
        show(charts_rates.zip_utility_rates())
    # dropdown instead of a second y-axis, see the note in charts_rates.py
    metric = st.radio("JMEC history metric", ["customers", "sales_mwh", "revenue_usd"], horizontal=True,
                      format_func={"customers": "Customers", "sales_mwh": "Energy sold", "revenue_usd": "Revenue"}.get)
    show(charts_rates.jmec_customers_and_sales(metric))

# ---------------------------------------------------------------------------
# HEATING
# ---------------------------------------------------------------------------
with tabs[2]:
    show(charts_heating.heating_fuel_mix())
    st.caption("Census ACS numbers for the village of Cuba alone show a much smaller wood/other share. "
               "See the Income (ACS) tab for the side-by-side and why the two disagree.")
    left, right = st.columns(2)
    with left:
        show(charts_heating.wood_and_propane_share())
    with right:
        show(charts_heating.heat_pump_savings_vs_propane())
    show(charts_heating.heating_cost_by_system())

# ---------------------------------------------------------------------------
# ENERGY BURDEN
# ---------------------------------------------------------------------------
with tabs[3]:
    left, right = st.columns(2)
    with left:
        show(charts_burden.burden_by_income())
    with right:
        show(charts_burden.burden_components())
    show(charts_burden.program_impact())
    left, right = st.columns(2)
    with left:
        heating = st.selectbox("Household type", ["Propane-heated home", "Wood-heated home"])
        show(charts_burden.rate_case_scenarios(heating))
    with right:
        show(charts_burden.high_burden_households())
    map_metric = st.radio("County map", ["energy_burden_pct", "res_rate_cents_kwh"], horizontal=True,
                          format_func={"energy_burden_pct": "Energy burden",
                                       "res_rate_cents_kwh": "Residential rate"}.get)
    left, right = st.columns([3, 2])
    with left:
        show(charts_burden.county_choropleth(map_metric))
    with right:
        show(charts_burden.county_rate_vs_burden())
    with st.expander("Energy burden data caveats"):
        for note in data_loader.burden_metadata()["data_caveats"]:
            st.markdown(f"- {note}")

# ---------------------------------------------------------------------------
# INCOME + HEATING FUEL FROM CENSUS ACS (Lenny's benchmarking file)
# ---------------------------------------------------------------------------
with tabs[4]:
    acs = data_loader.acs_benchmarks().set_index("place")
    cuba, county, state = (acs.loc[p] for p in (data_loader.CUBA_VILLAGE, data_loader.SANDOVAL,
                                                 data_loader.NEW_MEXICO))
    moe = data_loader.acs_income_moe()
    st.info("This tab uses Census ACS 2020-2024 data for the incorporated **village of Cuba** "
            f"({cuba['occupied_units']:,.0f} occupied homes), not zip 87013 like the eRedux tabs. "
            "Small-area estimates come with wide margins of error.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Cuba village median income", f"${cuba['median_income']:,.0f}",
              f"±${moe:,.0f} margin of error" if moe else None, delta_color="off")
    c2.metric("Gap vs. Sandoval County", f"−${county['median_income'] - cuba['median_income']:,.0f}",
              f"{100 * (cuba['median_income'] - county['median_income']) / county['median_income']:.1f}% "
              f"vs. ${county['median_income']:,.0f}", delta_color="off")
    c3.metric("Homes heated with electricity", f"{cuba['electric_pct']:.1f}%",
              f"county {county['electric_pct']:.1f}%, NM {state['electric_pct']:.1f}%", delta_color="off")

    left, right = st.columns(2)
    with left:
        show(charts_acs.median_income())
    with right:
        show(charts_acs.heating_fuel())
    left, right = st.columns(2)
    with left:
        show(charts_acs.fuel_gaps())
    with right:
        show(charts_acs.village_vs_zip_heating())

    with st.expander("Benchmark tables"):
        st.dataframe(data_loader.acs_income_gaps().rename(columns={
            "comparison": "Comparison", "dollar_gap": "Dollar difference ($)",
            "relative_gap_pct": "Relative gap (%)"}), hide_index=True)
        st.dataframe(data_loader.acs_rankings(), hide_index=True)
    with st.expander("Interpretation and limitations"):
        st.markdown(data_loader.acs_summary())
        for note in data_loader.acs_limitations():
            st.markdown(f"- {note}")

# ---------------------------------------------------------------------------
# RELIABILITY
# ---------------------------------------------------------------------------
with tabs[5]:
    rel = data_loader.reliability()
    years = sorted(rel["data_year"].unique())
    # controls in one row above the charts
    c1, c2, c3 = st.columns(3)
    measure = c1.selectbox("Metric", ["SAIDI", "SAIFI", "CAIDI"])
    include_med = c2.toggle("Include major event days", value=False)
    year = c3.select_slider("Ranking year", options=years, value=years[-1])
    metric = f"{measure.lower()}_{'with' if include_med else 'without'}_med"

    show(charts_reliability.reliability_trend(metric))
    left, right = st.columns(2)
    with left:
        show(charts_reliability.reliability_ranking(metric, year))
    with right:
        show(charts_reliability.saidi_vs_saifi(year, include_med))
    show(charts_reliability.jmec_med_impact())

# ---------------------------------------------------------------------------
# SOLAR, EV, GRID
# ---------------------------------------------------------------------------
with tabs[6]:
    left, right = st.columns(2)
    with left:
        show(charts_solar_ev_grid.solar_resource())
    with right:
        show(charts_solar_ev_grid.pv_output_check())
    left, right = st.columns(2)
    with left:
        show(charts_solar_ev_grid.ev_charging_ports())
    with right:
        show(charts_solar_ev_grid.ev_cost_per_mile())
    show(charts_solar_ev_grid.generation_mix())
    left, right = st.columns(2)
    with left:
        show(charts_solar_ev_grid.co2_intensity())
    with right:
        show(charts_solar_ev_grid.sandoval_generation())

# ---------------------------------------------------------------------------
# DATA QUALITY: cross-check chart + every flag the team wrote down
# ---------------------------------------------------------------------------
with tabs[7]:
    show(charts_summary.eredux_cross_check())
    st.subheader("Known data issues")
    for flag in data_loader.data_quality_flags():
        st.markdown(f"- {flag}")
