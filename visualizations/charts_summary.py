"""
charts_summary.py
Owner: Julien Werzowa (Team Member 6) - Visualizations

The "big picture" charts that pull from every teammate's data:
  1. The gap chart: how far behind (or ahead of) the benchmark Cuba is on each metric.
  2. The eRedux cross-check (my assigned data task): eRedux numbers vs. the federal originals.
  3. A locator map so people know where Cuba even is.
"""

import numpy as np
import plotly.graph_objects as go

from . import data_loader as dl
from .theme import BETTER_BLUE, COMPARE_GRAY, CUBA_BLUE, REFERENCE_INK, WORSE_RED, style_figure


def gap_chart() -> go.Figure:
    """
    Diverging bar chart of Cuba vs. its benchmark for every metric.

    x-axis = "times worse than the benchmark" on a LOG scale:
        1x  = same as NM (the center line)
        2x  = twice as bad
        0.8x = 20% better
    Log scale because wood heat is ~10x the state share and on a normal axis
    it squashes everything else flat. On a log axis 2x worse and 2x better
    are also the same distance from center, which is fair to both sides.

    Red = Cuba worse off, blue = Cuba better off. The text label also says
    "worse"/"better" so it doesn't rely on color alone.
    """
    df = dl.gap_summary()
    colors = [WORSE_RED if r > 1 else BETTER_BLUE for r in df["worse_ratio"]]
    labels = []
    for _, r in df.iterrows():
        word = "worse" if r["worse_ratio"] > 1 else "better"
        labels.append(f"{r['worse_ratio']:.2f}× {word}" if r["worse_ratio"] < 3 else f"{r['worse_ratio']:.1f}× {word}")

    # Bars on a log axis need to start at 1 (log(1) = 0), so I draw them with
    # base=1 and length = ratio - 1. That makes "better" bars point left.
    fig = go.Figure(go.Bar(
        y=df["metric"], x=df["worse_ratio"] - 1, base=1, orientation="h",
        marker=dict(color=colors, cornerradius=4),
        text=labels, textposition="outside",
        customdata=np.stack([df["cuba"], df["benchmark"], df["unit"], df["basis"]], axis=-1),
        hovertemplate=("%{y}<br>Cuba: %{customdata[0]:.2f} %{customdata[2]}"
                       "<br>Benchmark: %{customdata[1]:.2f} %{customdata[2]}"
                       "<br>%{customdata[3]}<extra></extra>"),
    ))
    fig.add_vline(x=1, line=dict(color=REFERENCE_INK, width=1))
    fig.update_xaxes(type="log", title="Cuba ÷ benchmark (log scale, 1× = same as benchmark)",
                     tickvals=[0.5, 1, 2, 5, 10, 20], ticktext=["0.5×", "1×", "2×", "5×", "10×", "20×"],
                     range=[np.log10(0.5), np.log10(25)])
    return style_figure(fig, "Where Cuba falls short: gaps vs. New Mexico",
                        "Benchmark is NM unless noted (reliability = median NM utility, solar = US avg). "
                        "Red = Cuba worse off, blue = better.", height=480)


def gap_table():
    """The same gap numbers as a plain table, for st.dataframe and for anyone who can't see the colors."""
    df = dl.gap_summary().sort_values("worse_ratio", ascending=False)
    out = df[["metric", "unit", "cuba", "benchmark", "worse_ratio", "basis"]].copy()
    out.columns = ["Metric", "Unit", "Cuba", "Benchmark", "Times worse (×)", "Comparison"]
    return out.round(2)


def eredux_cross_check() -> go.Figure:
    """
    Dot plot of % difference between eRedux and the federal source for each
    number we could check. Anything inside ±5% (shaded band) I'd call
    "agrees". The PV estimate is way outside, which is why we're not using it.
    """
    df = dl.eredux_cross_check()
    agrees = df["pct_diff"].abs() <= 5
    fig = go.Figure()
    fig.add_vrect(x0=-5, x1=5, fillcolor="rgba(42,120,214,0.08)", line_width=0,
                  annotation_text="±5% = agrees", annotation_position="top left",
                  annotation_font_color=REFERENCE_INK)
    fig.add_trace(go.Scatter(
        x=df["pct_diff"], y=df["metric"], mode="markers+text",
        marker=dict(size=13, color=[CUBA_BLUE if a else "#e34948" for a in agrees],
                    symbol=["circle" if a else "x" for a in agrees], line=dict(color="white", width=2)),
        text=[f"{v:+.1f}%" for v in df["pct_diff"]], textposition="top center",
        customdata=np.stack([df["eredux"], df["federal"], df["unit"]], axis=-1),
        hovertemplate=("%{y}<br>eRedux: %{customdata[0]} %{customdata[2]}"
                       "<br>Federal/check: %{customdata[1]} %{customdata[2]}<extra></extra>"),
        showlegend=False,
    ))
    fig.add_vline(x=0, line=dict(color=REFERENCE_INK, width=1))
    fig.update_xaxes(title="eRedux vs. federal original (% difference)", ticksuffix="%", range=[-90, 20])
    fig.update_yaxes(autorange="reversed")
    return style_figure(fig, "Cross-check: eRedux matches the federal data, except the PV estimate",
                        "eRedux values vs. EIA-861 (Team Member 2), EPA eGRID2023, and a first-order PV calculation.",
                        height=400)


def locator_map() -> go.Figure:
    """
    Simple map of the study area: Sandoval County outlined, Cuba and the
    comparison zips pinned, plus Albuquerque so people have a reference point.
    """
    geo = dl.nm_county_geojson()
    fips = dl.county_fips_lookup()
    focus = {"Sandoval": CUBA_BLUE, "Bernalillo": COMPARE_GRAY}
    locs = list(fips.values())
    z = [1 if fid == fips["Sandoval"] else (0.5 if fid == fips["Bernalillo"] else 0) for fid in locs]
    names = list(fips.keys())
    fig = go.Figure(go.Choropleth(
        geojson=geo, locations=locs, z=z, showscale=False,
        colorscale=[[0, "rgba(214,213,206,0.35)"], [0.5, focus["Bernalillo"]], [1, "#9ec5f4"]],
        marker_line_color="white", marker_line_width=1,
        text=names, hovertemplate="%{text} County<extra></extra>",
    ))
    pins = dl.PLACE_COORDS
    fig.add_trace(go.Scattergeo(
        lat=[c[0] for c in pins.values()], lon=[c[1] for c in pins.values()],
        text=list(pins.keys()), mode="markers+text", textposition="middle right",
        texttemplate=[k.split(" (")[0] for k in pins],
        marker=dict(size=[13, 9, 9, 9], color=[CUBA_BLUE, "#0b0b0b", "#0b0b0b", "#0b0b0b"],
                    line=dict(color="white", width=1.5)),
        textfont=dict(size=11), showlegend=False, hovertemplate="%{text}<extra></extra>",
    ))
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    fig = style_figure(fig, "Study area: Cuba, NM (zip 87013)",
                       "Sandoval County in light blue, Bernalillo in gray. Pins are town centers.", height=520)
    fig.update_layout(margin=dict(l=0, r=0, t=90, b=0))
    return fig
