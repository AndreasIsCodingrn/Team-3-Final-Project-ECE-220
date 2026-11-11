"""
charts_rates.py
Owner: Julien Werzowa (Team Member 6) - Visualizations

Charts for the "how much does electricity cost in Cuba" part of the project.
Every function here returns a plotly Figure, so in Streamlit you just do:

    st.plotly_chart(charts_rates.residential_rate_benchmark(), use_container_width=True)

Data: eRedux (my source), Mike's EIA-861 sales file, and Mike's JMEC tariff data.
"""

import numpy as np
import plotly.graph_objects as go

from . import data_loader as dl
from .theme import CATEGORICAL, COMPARE_GRAY, CUBA_BLUE, REFERENCE_INK, highlight_colors, style_figure


def residential_rate_benchmark() -> go.Figure:
    """
    Horizontal bar chart: residential price in cents/kWh for Cuba and JMEC
    (blue) vs. the county, Bernalillo, NM, and the US (gray).

    I sorted it low to high so you can read the ranking straight off the chart.
    Horizontal bars because the place names are long and would be sideways
    and unreadable on a vertical bar chart.
    """
    df = dl.residential_rate_benchmark().sort_values("cents_per_kwh")
    colors = [CUBA_BLUE if g == "Cuba" else COMPARE_GRAY for g in df["group"]]

    fig = go.Figure(go.Bar(
        x=df["cents_per_kwh"], y=df["place"], orientation="h",
        marker=dict(color=colors, cornerradius=4),
        text=[f"{v:.2f}¢" for v in df["cents_per_kwh"]], textposition="outside",
        hovertemplate="%{y}<br>%{x:.2f} ¢/kWh<extra></extra>",
    ))
    # dashed line at the NM average so it's easy to see who's above or below it
    nm = df.loc[df["place"] == dl.NEW_MEXICO, "cents_per_kwh"].iloc[0]
    fig.add_vline(x=nm, line=dict(color=REFERENCE_INK, width=1, dash="dot"),
                  annotation_text="NM avg", annotation_position="top")
    fig.update_xaxes(title="Residential price (¢/kWh)", range=[0, df["cents_per_kwh"].max() * 1.15])
    return style_figure(fig, "Cuba pays more than the NM average for residential power",
                        "Source: eRedux (EIA / OpenEI). Cuba zip value averages 3 utilities; JMEC serves most of Cuba.")


def sandoval_zip_rates() -> go.Figure:
    """
    Every Sandoval County zip code's residential rate, sorted, with 87013
    in blue. This shows Cuba sits near the top of its own county.

    I used dots instead of bars here on purpose. The spread is only ~1.3
    cents, so the axis has to be zoomed in, and a bar that doesn't start at
    zero exaggerates the differences. A dot only marks the value, so zooming is fair.
    """
    df = dl.sandoval_zip_rates()
    is_cuba = df["zip"] == "87013"
    fig = go.Figure(go.Scatter(
        x=df["zip"], y=df["cents_per_kwh"], mode="markers",
        marker=dict(color=highlight_colors(df["zip"], ["87013"]), size=[14 if c else 10 for c in is_cuba],
                    line=dict(color="white", width=2)),
        hovertemplate="Zip %{x}<br>%{y:.2f} ¢/kWh<extra></extra>",
    ))
    # Label only the Cuba dot, putting a number on all 20 is just clutter.
    # x has to be the position (0, 1, 2...) and not "87013", because plotly reads
    # "87013" as the number 87,013 and stretches the whole axis out to it.
    cuba = df[df["zip"] == "87013"].iloc[0]
    cuba_pos = list(df["zip"]).index("87013")
    fig.add_annotation(x=cuba_pos, y=cuba["cents_per_kwh"], text=f"Cuba {cuba['cents_per_kwh']:.2f}¢",
                       showarrow=False, yshift=12, font=dict(color=CUBA_BLUE))
    # Zoom the y-axis in, the spread is only ~1.3 cents so starting at 0
    # would make every bar look identical. The subtitle says it's zoomed.
    fig.update_yaxes(title="¢/kWh", range=[df["cents_per_kwh"].min() - 0.5, df["cents_per_kwh"].max() + 0.4])
    fig.update_xaxes(title="Sandoval County zip code", type="category")
    return style_figure(fig, "Cuba is one of the most expensive zips in Sandoval County",
                        "Source: eRedux. Y-axis zoomed in; the whole spread is about 1.3¢/kWh.")


def zip_utility_rates() -> go.Figure:
    """
    Grouped bars: the 3 utilities eRedux lists for zip 87013, split by
    residential / commercial / industrial. It shows why the "zip average" is
    misleading: NTUA's industrial rate is almost 4x Continental Divide's.
    """
    df = dl.zip_utility_rates()
    fig = go.Figure()
    # One trace per utility so each one gets its own legend entry + color.
    for i, (utility, sub) in enumerate(df.groupby("utility", sort=False)):
        fig.add_trace(go.Bar(
            x=sub["sector"], y=sub["cents_per_kwh"], name=utility,
            marker=dict(color=CATEGORICAL[i], cornerradius=4),
            hovertemplate=utility + "<br>%{x}: %{y:.2f} ¢/kWh<extra></extra>",
        ))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="¢/kWh")
    return style_figure(fig, "The three utilities behind Cuba's zip-average rate",
                        "Source: eRedux (EIA / OpenEI). eRedux averages these equally for 87013.")


def jmec_price_trend() -> go.Figure:
    """
    Line chart of JMEC's average price by sector from EIA-861 (2015-2025),
    with the 2013-2014 residential numbers added as hollow dots because
    those came from a secondary source Mike hasn't reconciled yet.

    Heads up, this is the "realized" price = revenue / kWh sold, which
    includes the fixed monthly charge spread over usage. It's NOT the
    tariff rate on the bill.
    """
    df = dl.jmec_sales_history()
    sec = dl.jmec_secondary_history()
    res = df[df["sector"] == "Residential"].set_index("year")["avg_price_cents_kwh"]
    first, last = int(res.index.min()), int(res.index.max())
    change = 100 * (res.loc[last] / res.loc[first] - 1)
    fig = go.Figure()
    sector_colors = {"Residential": CUBA_BLUE, "Commercial": CATEGORICAL[1],
                     "Industrial": CATEGORICAL[2], "Total": COMPARE_GRAY}
    for sector, color in sector_colors.items():
        sub = df[df["sector"] == sector]
        fig.add_trace(go.Scatter(
            x=sub["year"], y=sub["avg_price_cents_kwh"], name=sector, mode="lines+markers",
            line=dict(color=color, width=2, dash="dot" if sector == "Total" else "solid"),
            marker=dict(size=8),
            hovertemplate=sector + " %{x}: %{y:.2f} ¢/kWh<extra></extra>",
        ))
    fig.add_trace(go.Scatter(
        x=sec["year"], y=sec["avg_price_cents_kwh"], name="2013-14 (secondary)",
        mode="markers", marker=dict(size=9, color="rgba(0,0,0,0)", line=dict(color=CUBA_BLUE, width=2)),
        hovertemplate="Residential %{x}: %{y:.2f} ¢/kWh (not yet reconciled)<extra></extra>",
    ))
    fig.update_layout(hovermode="x unified")
    fig.update_yaxes(title="Average realized price (¢/kWh)")
    fig.update_xaxes(title="EIA reporting year", dtick=1)
    return style_figure(fig, f"JMEC residential price rose {change:.0f}% from {first} to {last}",
                        "Source: EIA-861 via Team Member 2. Price = revenue ÷ MWh sold, not the tariff rate.", height=450)


def jmec_customers_and_sales(metric: str = "customers") -> go.Figure:
    """
    JMEC customers OR energy sold by sector over time. I made this one
    take a 'metric' argument instead of putting both on one chart with two
    y-axes, because two y-axes on one plot basically always confuse people.
    metric = "customers" or "sales_mwh" or "revenue_usd"
    """
    labels = {"customers": ("Customer accounts", "Customers"),
              "sales_mwh": ("Energy sold (MWh/yr)", "MWh"),
              "revenue_usd": ("Revenue ($/yr)", "$")}
    axis_title, unit = labels[metric]
    df = dl.jmec_sales_history()
    df = df[df["sector"] != "Total"]
    fig = go.Figure()
    for sector, color in (("Residential", CUBA_BLUE), ("Commercial", CATEGORICAL[1]), ("Industrial", CATEGORICAL[2])):
        sub = df[df["sector"] == sector]
        fig.add_trace(go.Scatter(
            x=sub["year"], y=sub[metric], name=sector, mode="lines+markers",
            line=dict(color=color, width=2), marker=dict(size=8),
            hovertemplate=f"{sector} %{{x}}: %{{y:,.0f}} {unit}<extra></extra>",
        ))
    fig.update_layout(hovermode="x unified")
    fig.update_yaxes(title=axis_title, rangemode="tozero")
    fig.update_xaxes(title="EIA reporting year", dtick=1)
    return style_figure(fig, f"JMEC {axis_title.split(' (')[0].lower()} by sector",
                        "Source: EIA-861 via Team Member 2. Whole JMEC territory, not just Cuba.")


def _monthly_bill(kwh: np.ndarray, t: dict) -> np.ndarray:
    """
    Monthly residential bill for an array of kWh usage under JMEC's
    two-tier rate:
        bill = facility charge
             + tier1 price x min(kWh, 700)
             + tier2 price x max(kWh - 700, 0)
    Doesn't include fuel/power-cost adjustments or taxes, so real bills are a bit higher.
    """
    tier1_kwh = np.minimum(kwh, t["tier1_limit_kwh"])
    tier2_kwh = np.maximum(kwh - t["tier1_limit_kwh"], 0)
    return t["facility_usd"] + t["tier1_usd_kwh"] * tier1_kwh + t["tier2_usd_kwh"] * tier2_kwh


def jmec_bill_vs_usage(typical_kwh: int = 654) -> go.Figure:
    """
    Monthly bill ($) vs monthly usage (kWh) under the current 2026 JMEC
    residential tariff and the scheduled 2029 one. It's basically a
    piecewise-linear transfer function: the y-intercept is the fixed
    facility charge, the slope is the per-kWh price, and there's a kink
    at 700 kWh where tier 2 kicks in.

    The vertical marker is the typical NM household (654 kWh/month) so you
    can read the expected bill and how much it goes up in 2029.
    """
    tariffs = dl.jmec_residential_tariffs()
    kwh = np.arange(0, 1501, 10)
    fig = go.Figure()
    colors = [CUBA_BLUE, CATEGORICAL[1]]
    typical_bills = {}
    for (label, t), color in zip(tariffs.items(), colors):
        bill = _monthly_bill(kwh, t)
        typical_bills[label] = float(_monthly_bill(np.array([typical_kwh]), t)[0])
        fig.add_trace(go.Scatter(
            x=kwh, y=bill, name=label, mode="lines", line=dict(color=color, width=2),
            hovertemplate="%{x} kWh → $%{y:.2f}/month<extra>" + label + "</extra>",
        ))
    fig.add_vline(x=typical_kwh, line=dict(color=REFERENCE_INK, width=1, dash="dot"),
                  annotation_text=f"Typical NM home: {typical_kwh} kWh", annotation_position="top left")
    # direct labels at the typical usage so nobody has to hover to get the key numbers
    for (label, bill), color in zip(typical_bills.items(), colors):
        fig.add_trace(go.Scatter(
            x=[typical_kwh], y=[bill], mode="markers+text", showlegend=False,
            marker=dict(size=9, color=color, line=dict(color="white", width=2)),
            text=[f"${bill:.0f}"], textposition="middle right",
            hoverinfo="skip",
        ))
    fig.update_layout(hovermode="x unified")
    fig.update_xaxes(title="Monthly usage (kWh)")
    fig.update_yaxes(title="Monthly bill before adjustments ($)", rangemode="tozero")
    diff = list(typical_bills.values())
    return style_figure(fig, f"Scheduled 2029 JMEC rates add about ${diff[1] - diff[0]:.0f}/month for a typical home",
                        "Source: JMEC Rate No. 1 tariffs via Team Member 2. Excludes power-cost adjustments and taxes.")
