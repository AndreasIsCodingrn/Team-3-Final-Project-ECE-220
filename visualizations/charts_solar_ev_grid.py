"""
charts_solar_ev_grid.py
Owner: Julien Werzowa (Team Member 6) - Visualizations

Solar resource, rooftop PV, EV charging, and grid generation mix charts.
Mostly built from Christian's research file and the eRedux pages.
"""

import plotly.graph_objects as go

from . import data_loader as dl
from .theme import (CATEGORICAL, COMPARE_GRAY, CUBA_BLUE, GENERATION_COLORS, REFERENCE_INK,
                    highlight_colors, style_figure)


def solar_resource() -> go.Figure:
    """
    Global horizontal irradiance (GHI) for Cuba vs. nearby zips vs. the US
    average. GHI is the total sunlight hitting a flat surface, in kWh per
    square meter per day, which is also "peak sun hours" since panels are
    rated at 1 kW/m^2.
    """
    df = dl.solar_resource()
    fig = go.Figure(go.Bar(
        x=df["place"], y=df["ghi"],
        marker=dict(color=highlight_colors(df["place"], [dl.CUBA]), cornerradius=4),
        text=[f"{v:.1f}" for v in df["ghi"]], textposition="outside",
        customdata=df["rating"],
        hovertemplate="%{x}<br>GHI %{y:.1f} kWh/m²/day<br>%{customdata}<extra></extra>",
    ))
    us = df["ghi"].iloc[-1]
    cuba = df["ghi"].iloc[0]
    fig.update_yaxes(title="GHI (kWh/m²/day)", range=[0, df["ghi"].max() * 1.2])
    return style_figure(fig, f"Cuba gets {100 * (cuba / us - 1):.0f}% more sun than the US average",
                        "Source: eRedux (NREL NSRDB). Labels inferred from page layout; confirm with the NREL API.")


def pv_output_check() -> go.Figure:
    """
    Compares eRedux's 6 kW rooftop estimate (2,385 kWh/yr) to my first-order
    estimate (kW x peak sun hours x 365 x 0.80 derate). eRedux implies a ~4.5%
    capacity factor, which is way too low for New Mexico; ~20% is normal.
    The right fix is to run NREL PVWatts for the exact location.
    """
    pv = dl.pv_estimate()
    labels = ["eRedux estimate", "First-order estimate"]
    values = [pv["eredux_kwh_yr"], pv["first_order_kwh_yr"]]
    cfs = [100 * v / (pv["system_kw"] * 8760) for v in values]
    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker=dict(color=[COMPARE_GRAY, CUBA_BLUE], cornerradius=4),
        text=[f"{v:,.0f} kWh<br>CF {cf:.1f}%" for v, cf in zip(values, cfs)], textposition="outside",
        hovertemplate="%{x}: %{y:,.0f} kWh/yr<extra></extra>",
    ))
    fig.update_yaxes(title="Annual output, 6 kW system (kWh/yr)", range=[0, max(values) * 1.25])
    return style_figure(fig, f"A 6 kW array in Cuba should make ~{pv['first_order_kwh_yr']:,.0f} kWh/yr, not 2,385",
                        f"6 kW × {pv['peak_sun_hours']} sun-hours × 365 × {pv['derate']:.2f} derate. "
                        f"Worth ≈ ${pv['first_order_value_usd_yr']:,.0f}/yr at JMEC's tier-1 rate. CF = capacity factor.")


def ev_charging_ports() -> go.Figure:
    """
    Public EV charging ports in Cuba (both sources, since they disagree)
    vs. the comparison zips.
    """
    df = dl.ev_charging()
    fig = go.Figure(go.Bar(
        x=df["place"], y=df["ports"],
        marker=dict(color=[CUBA_BLUE if g == "Cuba" else COMPARE_GRAY for g in df["group"]], cornerradius=4),
        text=[f"{p} ports / {s} stn" for p, s in zip(df["ports"], df["stations"])], textposition="outside",
        hovertemplate="%{x}<br>%{y} ports<extra></extra>",
    ))
    fig.update_yaxes(title="Public charging ports", range=[0, df["ports"].max() * 1.3])
    return style_figure(fig, "Cuba has a handful of DC fast ports on US 550",
                        "Sources: eRedux (AFDC) and MyTownView (updated 2026-10-07) disagree on Cuba's count.")


def ev_cost_per_mile() -> go.Figure:
    """
    Cost to drive one mile: EV charged at home vs. public DC fast charging
    vs. a 28 mpg gas car. Public fast charging in Cuba at $0.48/kWh is
    actually more expensive per mile than gas, which matters since Cuba only
    has fast chargers.
    """
    df = dl.ev_vs_gas()
    colors = [CUBA_BLUE, CATEGORICAL[2], COMPARE_GRAY]
    fig = go.Figure(go.Bar(
        x=df["option"], y=df["cents_per_mile"],
        marker=dict(color=colors, cornerradius=4),
        text=[f"{v:.1f}¢" for v in df["cents_per_mile"]], textposition="outside",
        hovertemplate="%{x}: %{y:.1f}¢/mile<extra></extra>",
    ))
    fig.update_yaxes(title="Cost per mile (¢)", range=[0, df["cents_per_mile"].max() * 1.25])
    return style_figure(fig, "Home EV charging is about a third the cost of gas per mile",
                        "Source: eRedux. Assumes 12,000 mi/yr, $3.97/gal (Gulf Coast price), $0.48/kWh public DC fast.")


def generation_mix() -> go.Figure:
    """
    100% stacked bars of where the electricity comes from. The first two
    bars are the eGRID subregions (what Cuba's power "looks like" on the
    regional grid), the last two are plants physically inside NM / Sandoval.

    The NWPP vs AZNM question is open: eRedux puts Cuba in NWPP but its
    neighbors in AZNM, so I show both until Christian checks the Power Profiler.
    """
    df = dl.generation_mix()
    regions = list(dict.fromkeys(df["region"]))
    fig = go.Figure()
    for source, color in GENERATION_COLORS.items():
        sub = df[df["source"] == source].set_index("region").reindex(regions)
        if sub["pct"].isna().all():
            continue
        fig.add_trace(go.Bar(
            y=regions, x=sub["pct"], name=source, orientation="h",
            marker=dict(color=color, line=dict(color="white", width=1)),
            text=[f"{v:.0f}%" if v == v and v >= 8 else "" for v in sub["pct"]],
            textposition="inside", insidetextanchor="middle",
            hovertemplate="%{y}<br>" + source + ": %{x:.1f}%<extra></extra>",
        ))
    fig.update_layout(barmode="stack", legend_traceorder="normal")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title="Share of generation (%)", ticksuffix="%", range=[0, 102])
    return style_figure(fig, "Generation mix depends on which eGRID subregion Cuba is in",
                        "Sources: eRedux (EPA eGRID, EIA-923/860). NWPP display sums to 90%; NM 2024 sums to 101.8% on eRedux.",
                        height=440)


def co2_intensity() -> go.Figure:
    """CO2 emitted per MWh generated for each region, lower is cleaner."""
    df = dl.co2_intensity()
    fig = go.Figure(go.Bar(
        x=df["lb_per_mwh"], y=df["region"], orientation="h",
        marker=dict(color=COMPARE_GRAY, cornerradius=4),
        text=[f"{v:,.0f}" for v in df["lb_per_mwh"]], textposition="outside",
        hovertemplate="%{y}: %{x:,.1f} lb CO₂/MWh<extra></extra>",
    ))
    fig.update_xaxes(title="lb CO₂ per MWh", range=[0, df["lb_per_mwh"].max() * 1.15])
    fig.update_yaxes(autorange="reversed")
    return style_figure(fig, "Grid CO₂ intensity by region",
                        "Source: EPA eGRID2023 rev 2 (subregions) and eRedux (NM 2022).", height=320)


def sandoval_generation() -> go.Figure:
    """
    Sandoval County in-county generation for 2024 split into solar and wind
    MWh. Just a reminder that power made in the county isn't the same as
    power delivered to Cuba.
    """
    r = dl._load_json("cuba_nm_energy_research.json")["other_team_research"]["sandoval_county_generation"]
    mwh = r["estimated_generation_mwh_from_rounded_percentages"]
    labels = [k.title() for k in mwh]
    fig = go.Figure(go.Bar(
        x=labels, y=list(mwh.values()),
        marker=dict(color=[GENERATION_COLORS[l] for l in labels], cornerradius=4),
        text=[f"{v:,.0f} MWh" for v in mwh.values()], textposition="outside",
        hovertemplate="%{x}: %{y:,.0f} MWh<extra></extra>",
    ))
    fig.update_yaxes(title="2024 generation (MWh)", range=[0, max(mwh.values()) * 1.2])
    return style_figure(fig, f"Sandoval County plants made {r['total_generation_mwh']:,} MWh in 2024, all renewable",
                        "Source: eRedux (EIA-923/860). In-county generation is not the same as power delivered to Cuba.")
