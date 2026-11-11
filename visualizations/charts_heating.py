"""
charts_heating.py
Owner: Julien Werzowa (Team Member 6) - Visualizations

Charts for home heating: what fuel people heat with, and what it would cost
to heat a home with different systems. This is one of the biggest findings
so far, since ~64% of Cuba homes heat with wood vs ~6% statewide.

Data: eRedux heating fuel shares (from Census ACS) and eRedux's modeled
heating cost per system type.
"""

import plotly.graph_objects as go

from . import data_loader as dl
from .theme import CATEGORICAL, COMPARE_GRAY, CUBA_BLUE, FUEL_COLORS, style_figure

# Order the stack the same way on every bar. Wood and propane go first
# (left side) since those are the Cuba story, "Not reported" always goes last.
FUEL_ORDER = ["Wood", "Propane", "Natural gas", "Electricity", "Fuel oil", "Other / solar", "Not reported"]
PLACE_ORDER = [dl.CUBA, dl.JEMEZ_SPRINGS, dl.RIO_RANCHO, dl.SANDOVAL, dl.NEW_MEXICO, dl.USA]


def heating_fuel_mix() -> go.Figure:
    """
    100% stacked horizontal bars: share of homes by main heating fuel for
    Cuba, two nearby zips, the county, NM, and the US.

    Stacked to 100% because what matters is the *mix*, not the count of homes
    (Cuba has 1,586 homes and the US has 127 million, so raw counts would be useless).
    """
    df = dl.heating_fuel_mix()
    fig = go.Figure()
    for fuel in FUEL_ORDER:
        sub = df[df["fuel"] == fuel].set_index("place").reindex(PLACE_ORDER)
        if sub["pct"].fillna(0).sum() == 0:
            continue  # skip fuels that are zero everywhere so the legend stays clean
        fig.add_trace(go.Bar(
            y=PLACE_ORDER, x=sub["pct"], name=fuel, orientation="h",
            marker=dict(color=FUEL_COLORS[fuel], line=dict(color="white", width=1)),
            # only print the % inside the segment if it's big enough to fit
            text=[f"{v:.0f}%" if v and v >= 8 else "" for v in sub["pct"]],
            textposition="inside", insidetextanchor="middle",
            hovertemplate="%{y}<br>" + fuel + ": %{x:.1f}% of homes<extra></extra>",
        ))
    fig.update_layout(barmode="stack", legend_traceorder="normal")
    # reversed so Cuba is at the top where people start reading
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title="Share of homes by main heating fuel (%)", range=[0, 100], ticksuffix="%")
    return style_figure(fig, "Most Cuba homes heat with wood; most of NM uses natural gas",
                        "Source: eRedux (Census ACS). Sandoval shows only 3 fuels on eRedux, so 13% is unreported. "
                        "Cuba has 1,586 housing units, so check the ACS margin of error.", height=460)


def wood_and_propane_share() -> go.Figure:
    """
    A simpler version of the chart above, just wood + propane share by place.
    These are the two "off-grid-ish" delivered fuels that are expensive or
    labor heavy, so this is the one I'd put on a slide.
    """
    df = dl.heating_fuel_mix()
    df = df[df["fuel"].isin(["Wood", "Propane"])]
    # Sandoval doesn't report wood or propane, so leave it out instead of showing a fake 0.
    places = [p for p in PLACE_ORDER if p != dl.SANDOVAL]
    fig = go.Figure()
    for fuel in ("Wood", "Propane"):
        sub = df[df["fuel"] == fuel].set_index("place").reindex(places)
        fig.add_trace(go.Bar(
            x=places, y=sub["pct"], name=fuel,
            marker=dict(color=FUEL_COLORS[fuel], cornerradius=4),
            text=[f"{v:.0f}%" if v == v else "" for v in sub["pct"]], textposition="outside",
            hovertemplate="%{x}<br>" + fuel + ": %{y:.1f}%<extra></extra>",
        ))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="% of homes", ticksuffix="%", range=[0, 75])
    return style_figure(fig, "Wood and propane heat: Cuba vs. its neighbors",
                        "Source: eRedux (Census ACS). Sandoval County left out because eRedux doesn't report these fuels there.")


def heating_cost_by_system() -> go.Figure:
    """
    Grouped bars: modeled yearly heating cost by system type, Cuba (blue)
    vs. the comparison places (grays get lighter the further away they are).

    Cuba is coldest (~6,485 heating degree days vs ~4,500 in Rio Rancho), so
    every system costs more to run there. The big gap between propane
    ($2,707) and heat pump ($1,486) is the case for heat pump conversions.
    """
    df = dl.heating_cost_estimates()
    systems = ["Natural gas furnace", "Heat pump", "Propane furnace", "Electric resistance"]
    place_colors = {dl.CUBA: CUBA_BLUE, dl.JEMEZ_SPRINGS: "#6b6a65", dl.SANDOVAL: COMPARE_GRAY, dl.RIO_RANCHO: "#d6d5ce"}
    fig = go.Figure()
    for place, color in place_colors.items():
        sub = df[df["place"] == place].set_index("system").reindex(systems)
        hdd = int(sub["heating_degree_days"].iloc[0])
        fig.add_trace(go.Bar(
            x=systems, y=sub["usd_per_year"], name=f"{place.split(' (')[0]}, {hdd:,} HDD",
            marker=dict(color=color, cornerradius=4),
            text=[f"${v:,.0f}" for v in sub["usd_per_year"]] if place == dl.CUBA else None,
            textposition="outside",
            hovertemplate=place + "<br>%{x}: $%{y:,.0f}/yr<extra></extra>",
        ))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="Modeled heating cost ($/year)", tickprefix="$")
    return style_figure(fig, "Heating costs more in Cuba with every system; propane costs the most",
                        "Source: eRedux model, ~2,000 sq ft home, fuel prices as of 2026-03-30. "
                        "HDD = heating degree days. Modeled, not measured spending.", height=460)


def heat_pump_savings_vs_propane() -> go.Figure:
    """
    Simple 2-bar chart for the recommendations slide: what a Cuba propane
    home pays for heat now vs. with a heat pump, at present JMEC rates and
    at the phase-2 rate case (numbers from Andreas's burden file).
    """
    a = dl._load_json("cuba_nm_energy_burden.json")["assumptions"]
    labels = ["Propane furnace", "Heat pump (present rates)", "Heat pump (phase 2 rates)"]
    values = [a["cuba_propane_heating_annual_usd"], a["cuba_heat_pump_heating_annual_usd_present"],
              a["cuba_heat_pump_heating_annual_usd_phase2"]]
    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker=dict(color=[CATEGORICAL[1], CUBA_BLUE, CUBA_BLUE], cornerradius=4,
                    pattern=dict(shape=["", "", "/"], fgcolor="white")),
        text=[f"${v:,.0f}" for v in values], textposition="outside",
        hovertemplate="%{x}: $%{y:,.0f}/yr<extra></extra>",
    ))
    savings = values[0] - values[1]
    fig.update_yaxes(title="Annual heating cost ($)", tickprefix="$", range=[0, max(values) * 1.15])
    return style_figure(fig, f"Switching propane to a heat pump saves about ${savings:,.0f}/yr in Cuba",
                        "Source: eRedux modeled costs via the energy burden dataset (Team Member 4). Savings shrink if phase 2 rates pass.")
