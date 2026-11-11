"""
charts_burden.py
Owner: Julien Werzowa (Team Member 6) - Visualizations

Energy burden charts. Energy burden = yearly home energy cost / yearly
household income x 100. The DOE says anything over 6% is a "high" burden,
so that 6% line shows up on almost every chart here.

Data: Andreas's DOE LEAD file (Census Tract 109 = the Cuba area, plus
statewide NM), and the eRedux county table for the maps.
"""

import plotly.graph_objects as go

from . import data_loader as dl
from .theme import (CATEGORICAL, COMPARE_GRAY, CUBA_BLUE, PROGRAM_COLORS, REFERENCE_INK,
                    SEQUENTIAL_BLUE, style_figure)

CUBA_AREA = "Cuba area (Tract 109)"


def _threshold() -> float:
    """The high burden cutoff from Andreas's metadata (6%)."""
    return dl.burden_metadata()["high_burden_threshold_pct"]


def _add_threshold_line(fig: go.Figure, horizontal: bool = True) -> None:
    """Draws the dotted 6% high-burden reference line on a figure."""
    t = _threshold()
    kw = dict(line=dict(color=REFERENCE_INK, width=1, dash="dot"),
              annotation_text=f"{t:.0f}% = high burden", annotation_font_color=REFERENCE_INK)
    if horizontal:
        fig.add_hline(y=t, annotation_position="top right", **kw)
    else:
        fig.add_vline(x=t, annotation_position="bottom right", **kw)


def burden_by_income() -> go.Figure:
    """
    Grouped bars: energy burden by income bracket (AMI = area median income),
    Cuba area vs. all of NM. The lowest-income households in Cuba spend about
    18% of their income on energy, three times the "high burden" line.
    """
    df = dl.burden_by_income()
    fig = go.Figure()
    for area, color in ((CUBA_AREA, CUBA_BLUE), (dl.NEW_MEXICO, COMPARE_GRAY)):
        sub = df[df["area"] == area]
        fig.add_trace(go.Bar(
            x=sub["ami_bracket"], y=sub["burden_pct"], name=area,
            marker=dict(color=color, cornerradius=4),
            customdata=sub[["households", "income", "energy_cost"]].values,
            hovertemplate=(area + "<br>%{x}<br>Burden: %{y:.1f}%"
                           "<br>Households: %{customdata[0]:,}"
                           "<br>Avg income: $%{customdata[1]:,}"
                           "<br>Avg energy cost: $%{customdata[2]:,}/yr<extra></extra>"),
        ))
    _add_threshold_line(fig)
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="Energy burden (% of income)", ticksuffix="%")
    fig.update_xaxes(title="Income bracket (% of area median income)")
    return style_figure(fig, "Low-income Cuba households spend up to 18% of income on energy",
                        "Source: DOE LEAD (Tract 109, Sandoval Co. and statewide NM), via Team Member 4.")


def burden_components() -> go.Figure:
    """
    Stacked bars for the Cuba tract only: how each bracket's burden splits
    into electricity, gas, and other fuels (wood, propane, etc.).
    Uses LEAD's rounded whole-number components, so a stack can be off from
    the total by a point.
    """
    df = dl.burden_by_income()
    df = df[df["area"] == CUBA_AREA]
    fig = go.Figure()
    parts = (("electric_pct", "Electricity", CATEGORICAL[0]),
             ("gas_pct", "Gas", CATEGORICAL[1]),
             ("other_pct", "Other fuels (wood, propane...)", CATEGORICAL[3]))
    for col, name, color in parts:
        fig.add_trace(go.Bar(
            x=df["ami_bracket"], y=df[col], name=name,
            marker=dict(color=color, line=dict(color="white", width=1)),
            hovertemplate="%{x}<br>" + name + ": %{y}% of income<extra></extra>",
        ))
    _add_threshold_line(fig)
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title="Energy burden (% of income)", ticksuffix="%")
    fig.update_xaxes(title="Income bracket (% of area median income)")
    return style_figure(fig, "Electricity and gas make up most of the burden in every bracket",
                        "Source: DOE LEAD component burdens, Tract 109 (rounded to whole %).")


def program_impact() -> go.Figure:
    """
    Dot plot ("dumbbell" style) for each income bracket in the Cuba tract:
    a gray dot for today's burden, a colored dot for each program on its own,
    and a line connecting baseline to "all programs stacked".

    I picked dots instead of bars because with 5 scenarios x 6 brackets,
    grouped bars got really crowded. The dots make it easy to see how far
    each program moves you toward the 6% line.
    """
    df = dl.burden_program_impact()
    brackets = list(dict.fromkeys(df["ami_bracket"]))
    fig = go.Figure()
    # connector line from baseline to combined for each bracket
    for b in brackets:
        sub = df[df["ami_bracket"] == b].set_index("scenario")
        fig.add_trace(go.Scatter(
            x=[sub.loc["Baseline", "burden_pct"], sub.loc["All eligible combined", "burden_pct"]], y=[b, b],
            mode="lines", line=dict(color="rgba(137,135,129,0.5)", width=2),
            showlegend=False, hoverinfo="skip",
        ))
    for scenario, color in PROGRAM_COLORS.items():
        sub = df[df["scenario"] == scenario]
        fig.add_trace(go.Scatter(
            x=sub["burden_pct"], y=sub["ami_bracket"], name=scenario, mode="markers",
            marker=dict(size=12 if scenario in ("Baseline", "All eligible combined") else 9,
                        color=color, line=dict(color="white", width=2)),
            customdata=sub["savings_usd"],
            hovertemplate=scenario + "<br>%{y}: %{x:.1f}% burden<br>Saves $%{customdata:,.0f}/yr<extra></extra>",
        ))
    _add_threshold_line(fig, horizontal=False)
    fig.update_yaxes(categoryorder="array", categoryarray=brackets[::-1], title="")
    fig.update_xaxes(title="Energy burden after program (% of income)", ticksuffix="%", rangemode="tozero")
    return style_figure(fig, "Stacking every program cuts the lowest bracket's burden from 18% to 11%",
                        "Source: DOE LEAD + program assumptions (Team Member 4). Programs applied sequentially; "
                        "LIHEAP is a one-time credit, not a lasting saving.", height=480)


def rate_case_scenarios(heating: str = "Propane-heated home") -> go.Figure:
    """
    Grouped bars showing how burden changes for Cuba households as JMEC's
    rate case phases in. heating = "Wood-heated home" or "Propane-heated home".

    Wood-heated numbers leave out the cost of firewood (no good local data),
    so those burdens are definitely too low. Propane homes are the scary one,
    a 0-30% AMI propane household is at ~45% burden.
    """
    df = dl.burden_rate_case_scenarios()
    df = df[df["heating"] == heating]
    # ordinal ramp (light -> dark blue) because the rate cases go in order
    case_colors = {"Present rates": SEQUENTIAL_BLUE[2], "Rate phase 1": SEQUENTIAL_BLUE[4], "Rate phase 2": SEQUENTIAL_BLUE[6]}
    fig = go.Figure()
    for case, color in case_colors.items():
        sub = df[df["rate_case"] == case]
        fig.add_trace(go.Bar(
            x=sub["income_group"], y=sub["burden_pct"], name=case,
            marker=dict(color=color, cornerradius=4),
            customdata=sub[["annual_cost_usd", "household_income"]].values,
            hovertemplate=(case + "<br>%{x}<br>Burden: %{y:.1f}%<br>Energy cost: $%{customdata[0]:,}/yr"
                           "<br>Income: $%{customdata[1]:,}<extra></extra>"),
        ))
    _add_threshold_line(fig)
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="Energy burden (% of income)", ticksuffix="%")
    note = "Firewood cost not included, so these understate burden." if heating.startswith("Wood") \
        else "Electric + propane heating cost."
    return style_figure(fig, f"Burden under JMEC rate phases: {heating.lower()}",
                        f"Source: energy burden scenarios (Team Member 4). {note}")


def high_burden_households() -> go.Figure:
    """
    Simple bar: share of households above 6% burden, before and after the
    programs, for the Cuba tract vs. NM. Shown as a share instead of a
    count so the tract (820 homes) and state (812,852 homes) are comparable.
    """
    s = dl.burden_summaries()
    rows = []
    for area, key in ((CUBA_AREA, "cuba"), (dl.NEW_MEXICO, "state")):
        d = s[key]
        rows.append((area, "Before programs", 100 * d["high_burden_households_before"] / d["total_households"],
                     d["high_burden_households_before"]))
        rows.append((area, "After all eligible programs", 100 * d["high_burden_households_after"] / d["total_households"],
                     d["high_burden_households_after"]))
    fig = go.Figure()
    for phase, color in (("Before programs", COMPARE_GRAY), ("After all eligible programs", CUBA_BLUE)):
        sub = [r for r in rows if r[1] == phase]
        fig.add_trace(go.Bar(
            x=[r[0] for r in sub], y=[r[2] for r in sub], name=phase,
            marker=dict(color=color, cornerradius=4),
            text=[f"{r[2]:.0f}%" for r in sub], textposition="outside",
            customdata=[r[3] for r in sub],
            hovertemplate="%{x}<br>" + phase + ": %{y:.1f}% (%{customdata:,} households)<extra></extra>",
        ))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="Households above 6% burden (%)", ticksuffix="%", range=[0, 60])
    return style_figure(fig, "Programs alone don't move any Cuba households below 6%",
                        "Source: DOE LEAD summaries (Team Member 4). Cuba: 391 high-burden households before and after.")


def county_choropleth(metric: str = "energy_burden_pct") -> go.Figure:
    """
    Map of New Mexico counties shaded by energy burden or residential rate.
    metric = "energy_burden_pct" or "res_rate_cents_kwh"

    Sandoval (where Cuba is) and Bernalillo get a thick outline, and Cuba
    and the comparison zips get dropped as pins. One-hue blue scale so
    darker always = higher.
    """
    df = dl.county_profiles()
    fips = dl.county_fips_lookup()
    df["fips"] = df["county"].map(fips)
    label = {"energy_burden_pct": ("Energy burden (%)", "%"),
             "res_rate_cents_kwh": ("Residential rate (¢/kWh)", "¢")}[metric]

    fig = go.Figure(go.Choropleth(
        geojson=dl.nm_county_geojson(), locations=df["fips"], z=df[metric],
        colorscale=[[i / (len(SEQUENTIAL_BLUE) - 1), c] for i, c in enumerate(SEQUENTIAL_BLUE)],
        marker_line_color="white", marker_line_width=1,
        colorbar=dict(title=label[0], ticksuffix=label[1], thickness=12),
        customdata=df[["county", "population"]].values,
        hovertemplate="%{customdata[0]} County<br>" + label[0] + ": %{z}<br>Pop: %{customdata[1]:,}<extra></extra>",
    ))
    # thicker outline on the two counties from the proposal
    focus = df[df["county"].isin(["Sandoval", "Bernalillo"])]
    fig.add_trace(go.Choropleth(
        geojson=dl.nm_county_geojson(), locations=focus["fips"], z=[0] * len(focus),
        colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], showscale=False,
        marker_line_color="#0b0b0b", marker_line_width=2.5, hoverinfo="skip",
    ))
    pins = dl.PLACE_COORDS
    fig.add_trace(go.Scattergeo(
        lat=[c[0] for c in pins.values()], lon=[c[1] for c in pins.values()],
        text=list(pins.keys()), mode="markers+text", textposition="middle left",
        # only Cuba and Albuquerque get a printed label, the rest show on hover (labels piled up otherwise)
        texttemplate=[k.split(" (")[0] if k in (dl.CUBA, "Albuquerque") else "" for k in pins],
        marker=dict(size=[12, 8, 8, 8], color=["#e34948", "#0b0b0b", "#0b0b0b", "#0b0b0b"],
                    line=dict(color="white", width=1.5)),
        textfont=dict(size=12, color="#0b0b0b"), showlegend=False, hovertemplate="%{text}<extra></extra>",
    ))
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    title = ("Energy burden by NM county" if metric == "energy_burden_pct"
             else "Residential electricity rate by NM county")
    fig = style_figure(fig, title, "Source: eRedux (DOE LEAD / EIA). Sandoval and Bernalillo outlined; red pin = Cuba.",
                       height=560)
    fig.update_layout(margin=dict(l=0, r=0, t=90, b=0))
    return fig


def county_rate_vs_burden() -> go.Figure:
    """
    Scatter of every NM county: residential rate (x) vs. energy burden (y),
    dot size = population. Checks whether higher rates actually line up
    with higher burden at the county level (spoiler: only loosely, income
    matters a lot more).
    """
    df = dl.county_profiles().dropna(subset=["res_rate_cents_kwh"])
    focus = df["county"].isin(["Sandoval", "Bernalillo"])
    fig = go.Figure()
    for is_focus, sub in df.groupby(focus):
        fig.add_trace(go.Scatter(
            x=sub["res_rate_cents_kwh"], y=sub["energy_burden_pct"], mode="markers+text" if is_focus else "markers",
            name="Sandoval & Bernalillo" if is_focus else "Other NM counties",
            text=sub["county"] if is_focus else None, textposition="top center",
            marker=dict(size=(sub["population"] ** 0.5) / 18 + 8,
                        color=CUBA_BLUE if is_focus else COMPARE_GRAY,
                        line=dict(color="white", width=2), opacity=0.9),
            customdata=sub[["county", "population"]].values,
            hovertemplate="%{customdata[0]}<br>Rate: %{x:.2f}¢/kWh<br>Burden: %{y:.1f}%"
                          "<br>Pop: %{customdata[1]:,}<extra></extra>",
        ))
    fig.update_xaxes(title="Residential rate (¢/kWh)")
    fig.update_yaxes(title="Average energy burden (%)", ticksuffix="%", rangemode="tozero")
    return style_figure(fig, "County rates and energy burden only loosely track each other",
                        "Source: eRedux state page. Dot size = population. Los Alamos left out (no rate listed).")
