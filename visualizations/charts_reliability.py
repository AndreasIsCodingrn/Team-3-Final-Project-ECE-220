"""
charts_reliability.py
Owner: Julien Werzowa (Team Member 6) - Visualizations

Reliability charts using Jadon's cleaned EIA-861 file (data/reliability_nm.csv).

Quick IEEE 1366 refresher so the charts make sense:
  SAIDI = total outage minutes the average customer sees in a year
  SAIFI = how many sustained outages the average customer sees in a year
  CAIDI = SAIDI / SAIFI = average restoration time per outage (minutes)
  "with MED"    = everything, including Major Event Days (storms, fires, etc.)
  "without MED" = major event days removed, closer to normal day-to-day grid health

These are reported for the whole co-op, not for Cuba by itself, so they're
an estimate of what Cuba members experience.
"""

from __future__ import annotations

import plotly.graph_objects as go

from . import data_loader as dl
from .theme import COMPARE_GRAY, CUBA_BLUE, REFERENCE_INK, style_figure

METRIC_LABELS = {
    "saidi_with_med": ("SAIDI with major events", "minutes per customer per year"),
    "saidi_without_med": ("SAIDI without major events", "minutes per customer per year"),
    "saifi_with_med": ("SAIFI with major events", "outages per customer per year"),
    "saifi_without_med": ("SAIFI without major events", "outages per customer per year"),
    "caidi_with_med": ("CAIDI with major events", "minutes per outage"),
    "caidi_without_med": ("CAIDI without major events", "minutes per outage"),
}


def reliability_trend(metric: str = "saidi_without_med") -> go.Figure:
    """
    Line chart over time: JMEC in thick blue, every other NM utility as a
    thin light gray line, and the NM median (not counting JMEC) as a dashed
    dark line. The "spaghetti" in gray is there for context only, the point
    is to compare the blue line against the dashed median.

    I use the median instead of the mean because a couple of tiny co-ops
    (like Rio Grande with 325 customers) have crazy values that drag the mean around.
    """
    df = dl.reliability()
    name, unit = METRIC_LABELS[metric]
    fig = go.Figure()

    for utility, sub in df[~df["is_jmec"]].groupby("utility"):
        sub = sub.sort_values("data_year")
        fig.add_trace(go.Scatter(
            x=sub["data_year"], y=sub[metric], mode="lines", name=utility,
            line=dict(color="rgba(163,162,156,0.45)", width=1),
            showlegend=False, legendgroup="others",
            hovertemplate=utility + " %{x}: %{y:,.1f}<extra></extra>",
        ))

    median = df[~df["is_jmec"]].groupby("data_year")[metric].median()
    fig.add_trace(go.Scatter(
        x=median.index, y=median.values, mode="lines", name="NM median (other utilities)",
        line=dict(color=REFERENCE_INK, width=2, dash="dash"),
        hovertemplate="NM median %{x}: %{y:,.1f}<extra></extra>",
    ))

    jmec = df[df["is_jmec"]].sort_values("data_year")
    fig.add_trace(go.Scatter(
        x=jmec["data_year"], y=jmec[metric], mode="lines+markers", name="JMEC (serves Cuba)",
        line=dict(color=CUBA_BLUE, width=3), marker=dict(size=8, line=dict(color="white", width=2)),
        hovertemplate="JMEC %{x}: %{y:,.1f}<extra></extra>",
    ))
    # a gray entry in the legend so people know what the faint lines are
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", name="Other NM utilities",
                             line=dict(color=COMPARE_GRAY, width=1)))

    fig.update_xaxes(title="EIA reporting year", dtick=1)
    fig.update_yaxes(title=f"{name.split(' ')[0]} ({unit})", rangemode="tozero")
    fig = style_figure(fig, f"JMEC vs. other NM utilities: {name}",
                       "Source: EIA-861 reliability files, cleaned by Team Member 1. Co-op wide, not Cuba-only.",
                       height=480)
    # 3 legend entries wrap up into the title on this one, so the legend goes under the plot
    fig.update_layout(legend=dict(y=-0.22, yanchor="top"), margin=dict(b=40))
    return fig


def reliability_ranking(metric: str = "saidi_without_med", year: int | None = None) -> go.Figure:
    """
    Horizontal bar ranking every NM utility for one year, worst at the top,
    JMEC in blue. Defaults to the newest year in the data.
    """
    df = dl.reliability()
    year = year or int(df["data_year"].max())
    sub = df[(df["data_year"] == year)].dropna(subset=[metric]).sort_values(metric)
    name, unit = METRIC_LABELS[metric]
    colors = [CUBA_BLUE if j else COMPARE_GRAY for j in sub["is_jmec"]]
    fig = go.Figure(go.Bar(
        x=sub[metric], y=sub["utility"], orientation="h",
        marker=dict(color=colors, cornerradius=4),
        customdata=sub[["customers", "ownership"]].values,
        hovertemplate="%{y}<br>%{x:,.1f} " + unit + "<br>%{customdata[0]:,.0f} customers, %{customdata[1]}<extra></extra>",
    ))
    # label just JMEC's bar with its value and rank
    jmec = sub[sub["is_jmec"]]
    if not jmec.empty:
        rank_from_worst = len(sub) - list(sub["utility"]).index(jmec["utility"].iloc[0])
        fig.add_annotation(x=jmec[metric].iloc[0], y=jmec["utility"].iloc[0], xanchor="left", showarrow=False,
                           text=f"  {jmec[metric].iloc[0]:,.0f} (#{rank_from_worst} worst of {len(sub)})",
                           font=dict(color=CUBA_BLUE))
    fig.update_xaxes(title=unit, range=[0, sub[metric].max() * 1.35])
    return style_figure(fig, f"{year} {name}: NM utilities ranked",
                        "Source: EIA-861 via Team Member 1. Worst at the top.", height=500)


def saidi_vs_saifi(year: int | None = None, with_med: bool = False) -> go.Figure:
    """
    Scatter: SAIFI (how often) on x vs SAIDI (how long in total) on y, one
    dot per utility, dot size = number of customers. The dashed lines are
    constant CAIDI (SAIDI = CAIDI x SAIFI), so a utility above the 200 min
    line takes over 3 hours on average to restore power.

    Top right corner = outages are frequent AND long = worst place to be.
    """
    df = dl.reliability()
    year = year or int(df["data_year"].max())
    suffix = "with_med" if with_med else "without_med"
    sub = df[df["data_year"] == year].dropna(subset=[f"saidi_{suffix}", f"saifi_{suffix}"])
    x, y = sub[f"saifi_{suffix}"], sub[f"saidi_{suffix}"]

    fig = go.Figure()
    # constant-CAIDI guide lines (they're straight lines through the origin)
    xmax = x.max() * 1.15
    ymax = y.max() * 1.2
    for caidi in (100, 200):
        fig.add_trace(go.Scatter(
            x=[0, xmax], y=[0, caidi * xmax], mode="lines", showlegend=False, hoverinfo="skip",
            line=dict(color="rgba(137,135,129,0.45)", width=1, dash="dot"),
        ))
        # put the label right where the line leaves the plot (right edge or top edge, whichever comes first)
        lx = min(xmax, ymax / caidi) * 0.97
        fig.add_annotation(x=lx, y=caidi * lx, text=f"CAIDI {caidi} min", showarrow=False,
                           xanchor="right", yanchor="bottom", font=dict(size=11, color=REFERENCE_INK))

    for is_jmec, part in sub.groupby("is_jmec"):
        fig.add_trace(go.Scatter(
            x=part[f"saifi_{suffix}"], y=part[f"saidi_{suffix}"],
            mode="markers+text", name="JMEC" if is_jmec else "Other NM utilities",
            text=part["utility"], textposition="top center",
            textfont=dict(size=10, color=CUBA_BLUE if is_jmec else REFERENCE_INK),
            marker=dict(size=(part["customers"] ** 0.5) / 12 + 8,
                        color=CUBA_BLUE if is_jmec else COMPARE_GRAY,
                        line=dict(color="white", width=2), opacity=0.9),
            customdata=part[["customers"]].values,
            hovertemplate="%{text}<br>SAIFI %{x:.2f}<br>SAIDI %{y:,.0f} min<br>%{customdata[0]:,.0f} customers<extra></extra>",
        ))
    fig.update_xaxes(title="SAIFI (outages per customer per year)", range=[0, xmax])
    fig.update_yaxes(title="SAIDI (outage minutes per customer per year)", range=[0, ymax])
    med = "with" if with_med else "without"
    return style_figure(fig, f"{year}: outage frequency vs. total outage time ({med} major events)",
                        "Source: EIA-861 via Team Member 1. Dot size = customers. Dotted lines = constant restoration time.",
                        height=520)


def jmec_med_impact() -> go.Figure:
    """
    JMEC only: SAIDI with vs. without major event days for each year, as
    paired bars. The gap between them is how many outage minutes came from
    major events. 2024 sticks out big time (~1,877 vs ~1,045 minutes).
    """
    df = dl.reliability()
    j = df[df["is_jmec"]].sort_values("data_year")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=j["data_year"], y=j["saidi_without_med"], name="Normal days (without MED)",
                         marker=dict(color=CUBA_BLUE, cornerradius=4),
                         hovertemplate="%{x}: %{y:,.0f} min without MED<extra></extra>"))
    fig.add_trace(go.Bar(x=j["data_year"], y=j["saidi_with_med"] - j["saidi_without_med"],
                         name="Added by major event days",
                         marker=dict(color="#86b6ef", cornerradius=4),
                         customdata=j["saidi_with_med"],
                         hovertemplate="%{x}: +%{y:,.0f} min from major events (total %{customdata:,.0f})<extra></extra>"))
    fig.update_layout(barmode="stack")
    fig.update_xaxes(title="EIA reporting year", dtick=1)
    fig.update_yaxes(title="SAIDI (minutes per customer per year)")
    return style_figure(fig, "JMEC outage minutes: everyday outages vs. major events",
                        "Source: EIA-861 via Team Member 1. Stack total = SAIDI with major events.")
