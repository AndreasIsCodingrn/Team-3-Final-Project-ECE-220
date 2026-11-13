"""
charts_acs.py
Owner: Julien Werzowa (Team Member 6) - Visualizations

Charts for Lenny's Census ACS benchmarking (Cuba_Benchmarking.json):
  - median household income (B19013) for Cuba village vs. Sandoval County vs. NM
  - primary heating fuel (B25040) in the 3 grouped categories Lenny reported
  - a side-by-side of the ACS village heating mix vs. the eRedux zip mix,
    because the two disagree a lot and the report needs to explain why

Important: "Cuba" in this file is the incorporated VILLAGE (a Census place,
159 occupied homes), not zip 87013 like the eRedux charts. The village
estimates come with big margins of error.
"""

import plotly.graph_objects as go

from . import data_loader as dl
from .theme import CATEGORICAL, COMPARE_GRAY, CUBA_BLUE, LIGHT_GRAY, REFERENCE_INK, style_figure

PLACE_ORDER = [dl.CUBA_VILLAGE, dl.SANDOVAL, dl.NEW_MEXICO]

# The ACS groups don't line up with the eRedux fuel list, so they get their own
# colors. Gas keeps the natural-gas blue and electricity keeps its aqua so
# they read the same as on the eRedux heating chart.
ACS_FUEL_COLORS = {
    "Gas (utility + bottled)": CATEGORICAL[0],
    "Electricity": CATEGORICAL[2],
    "All other fuels": CATEGORICAL[3],
    "Not listed": LIGHT_GRAY,
}
SOURCE_NOTE = "Source: Census ACS 2020-2024 5-year, via Team Member 3."


def median_income() -> go.Figure:
    """
    Horizontal bars of median household income. Cuba gets an error bar for its
    90% margin of error (about ±$46k), which is almost as big as the estimate
    itself, so the chart shows that the gap vs. NM could be noise.
    """
    df = dl.acs_benchmarks().set_index("place").reindex(PLACE_ORDER)
    moe = dl.acs_income_moe()
    colors = [CUBA_BLUE if p == dl.CUBA_VILLAGE else COMPARE_GRAY for p in df.index]
    error = [moe if p == dl.CUBA_VILLAGE else 0 for p in df.index] if moe else None
    fig = go.Figure(go.Bar(
        y=df.index, x=df["median_income"], orientation="h",
        marker=dict(color=colors, cornerradius=4),
        error_x=dict(type="data", array=error, color=REFERENCE_INK, thickness=1.5, width=6) if error else None,
        text=[f"${v:,.0f}" for v in df["median_income"]], textposition="inside", insidetextanchor="end",
        textfont=dict(color="white"),
        hovertemplate="%{y}: $%{x:,.0f}<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed")
    upper = df["median_income"].max()
    if moe:
        upper = max(upper, df.loc[dl.CUBA_VILLAGE, "median_income"] + moe)
    fig.update_xaxes(title="Median household income (2024 dollars)", tickprefix="$", range=[0, upper * 1.05])
    moe_note = f" Error bar = Cuba's 90% margin of error (±${moe:,.0f})." if moe else ""
    return style_figure(fig, "Cuba village has the lowest median income of the three",
                        f"{SOURCE_NOTE} Table B19013.{moe_note}", height=340)


def heating_fuel() -> go.Figure:
    """
    100% stacked bars of primary heating fuel for Cuba village, the county and NM,
    in the 3 groups the source reports. Gas = utility gas + propane together.
    """
    df = dl.acs_heating_fuel()
    fig = go.Figure()
    for fuel, color in ACS_FUEL_COLORS.items():
        sub = df[df["fuel"] == fuel].set_index("place").reindex(PLACE_ORDER)
        if sub["pct"].fillna(0).sum() == 0:
            continue
        fig.add_trace(go.Bar(
            y=PLACE_ORDER, x=sub["pct"], name=fuel, orientation="h",
            marker=dict(color=color, line=dict(color="white", width=1)),
            text=[f"{v:.1f}%" if v and v >= 6 else "" for v in sub["pct"]],
            textposition="inside", insidetextanchor="middle",
            customdata=sub[["housing_units"]].values,
            hovertemplate="%{y}<br>" + fuel + ": %{x:.1f}% of homes<br>%{customdata[0]:,.0f} occupied homes<extra></extra>",
        ))
    fig.update_layout(barmode="stack", legend_traceorder="normal")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title="Share of occupied homes by primary heating fuel (%)", range=[0, 100], ticksuffix="%")
    return style_figure(fig, "Cuba village heats with electricity more than the county does",
                        f"{SOURCE_NOTE} Table B25040. Gas includes propane. 'Not listed' = solar, oil and no fuel.",
                        height=360)


def fuel_gaps() -> go.Figure:
    """
    Percentage-point gaps in heating fuel share, Cuba minus county and Cuba
    minus state. Positive = more Cuba homes use that fuel.
    """
    df = dl.acs_fuel_gaps()
    fig = go.Figure()
    for col, name, color in (("cuba_minus_county_pp", "Cuba − Sandoval County", CUBA_BLUE),
                             ("cuba_minus_state_pp", "Cuba − New Mexico", COMPARE_GRAY)):
        fig.add_trace(go.Bar(
            y=df["fuel"], x=df[col], name=name, orientation="h",
            marker=dict(color=color, cornerradius=4),
            text=[f"{v:+.1f} pp" for v in df[col]], textposition="outside",
            hovertemplate="%{y}<br>" + name + ": %{x:+.1f} percentage points<extra></extra>",
        ))
    fig.add_vline(x=0, line=dict(color=REFERENCE_INK, width=1))
    span = df[["cuba_minus_county_pp", "cuba_minus_state_pp"]].abs().max().max() * 1.4
    fig.update_layout(barmode="group")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title="Percentage-point gap (+ = more common in Cuba)", range=[-span, span], ticksuffix=" pp")
    return style_figure(fig, "Cuba's heating mix looks like the state's, not the county's",
                        f"{SOURCE_NOTE} Gaps in share of homes, not in energy use.", height=360)


def village_vs_zip_heating() -> go.Figure:
    """
    The two Cuba heating estimates side by side, collapsed to the 3 groups both
    sources can be mapped to. ACS says the village is mostly gas; eRedux says
    the zip is mostly wood. Different areas, different sample sizes.
    """
    df = dl.acs_vs_eredux_heating()
    sources = list(dict.fromkeys(df["source"]))
    fig = go.Figure()
    for fuel in ("Gas (utility + bottled)", "Electricity", "All other fuels"):
        sub = df[df["fuel"] == fuel].set_index("source").reindex(sources)
        fig.add_trace(go.Bar(
            y=sources, x=sub["pct"], name=fuel if fuel != "All other fuels" else "Other (mostly wood)",
            orientation="h", marker=dict(color=ACS_FUEL_COLORS[fuel], line=dict(color="white", width=1)),
            text=[f"{v:.0f}%" if v >= 6 else "" for v in sub["pct"]],
            textposition="inside", insidetextanchor="middle",
            hovertemplate="%{y}<br>" + fuel + ": %{x:.1f}%<extra></extra>",
        ))
    fig.update_layout(barmode="stack", legend_traceorder="normal")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(title="Share of homes by primary heating fuel (%)", range=[0, 100], ticksuffix="%")
    return style_figure(fig, "The village and the zip code tell very different heating stories",
                        "ACS covers only the incorporated village; eRedux zip 87013 adds the surrounding rural area. "
                        "eRedux gas = natural gas + propane.", height=320)
