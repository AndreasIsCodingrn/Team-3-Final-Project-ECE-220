"""
theme.py
Owner: Julien Werzowa (Team Member 6) - Visualizations

This file holds all the colors and the shared plot styling so every chart in the
dashboard looks like it belongs to the same project. I put it in one place so if
the team wants to change a color we only change it here and not in 25 functions.

General color rules I tried to follow:
  - Cuba / JMEC is ALWAYS the same blue so you can spot it on any chart.
  - Everything we compare Cuba against is a neutral gray, unless the chart
    needs to tell several groups apart (like heating fuels), then I use the
    categorical list in a fixed order.
  - Red vs. blue is only used for "worse than" vs. "better than" comparisons.
"""

import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
# Focus color for Cuba (zip 87013) and for JMEC, the co-op that serves Cuba.
CUBA_BLUE = "#2a78d6"

# Neutral gray for "everybody else" (county, state, other utilities, etc.).
# Using gray means the eye goes straight to the blue bar/line first.
COMPARE_GRAY = "#a3a29c"
LIGHT_GRAY = "#d6d5ce"

# Diverging pair for the gap chart: red = Cuba is worse, blue = Cuba is better.
WORSE_RED = "#e34948"
BETTER_BLUE = "#2a78d6"

# Line color used for reference lines like the 6% high energy burden threshold.
REFERENCE_INK = "#52514e"

# Fixed-order categorical colors. Order matters here, these were picked so that
# neighbors in a stacked bar are still tell-apart-able for colorblind viewers.
# I never cycle these, if a chart needs more than 8 groups it gets an "Other".
CATEGORICAL = [
    "#2a78d6",  # 1 blue
    "#eb6834",  # 2 orange
    "#1baf7a",  # 3 aqua
    "#eda100",  # 4 yellow
    "#e87ba4",  # 5 magenta
    "#008300",  # 6 green
    "#6250d6",  # 7 violet
    "#e34948",  # 8 red
]

# Each heating fuel / generation source always gets the same color, no matter
# which chart it shows up in. That way "wood" is always the same color on the
# Cuba chart and the state chart, which makes comparing them way easier.
FUEL_COLORS = {
    "Natural gas": CATEGORICAL[0],
    "Electricity": CATEGORICAL[2],
    "Propane": CATEGORICAL[1],
    "Wood": CATEGORICAL[3],
    "Fuel oil": CATEGORICAL[6],
    "Other / solar": CATEGORICAL[4],
    "Not reported": LIGHT_GRAY,
}

GENERATION_COLORS = {
    "Natural gas": CATEGORICAL[0],
    "Coal": "#52514e",
    "Nuclear": CATEGORICAL[6],
    "Hydro": CATEGORICAL[2],
    "Wind": CATEGORICAL[4],
    "Solar": CATEGORICAL[3],
    "Unaccounted": LIGHT_GRAY,
}

# The three assistance programs from the energy burden JSON.
PROGRAM_COLORS = {
    "Baseline": COMPARE_GRAY,
    "Weatherization": CATEGORICAL[0],
    "Solar for All": CATEGORICAL[3],
    "LIHEAP": CATEGORICAL[1],
    "All eligible combined": CATEGORICAL[2],
}

# Sequential blue ramp (light -> dark) for the maps. One hue only so "darker"
# always means "more", which is how people naturally read a map.
SEQUENTIAL_BLUE = [
    "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5",
    "#2a78d6", "#1c5cab", "#104281", "#0d366b",
]

FONT_FAMILY = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def style_figure(fig: go.Figure, title: str, subtitle: str = "", height: int = 420) -> go.Figure:
    """
    Applies the shared layout to a plotly figure and returns it.

    Every chart function calls this at the end. It sets the title (with a
    smaller gray subtitle under it for the source/caveat), turns the grid way
    down so it doesn't fight with the data, and puts the legend on top so it
    doesn't steal width from the plot on small screens.

    I leave the background transparent on purpose so Streamlit's light/dark
    theme shows through instead of a white box sitting in dark mode.
    """
    # Plotly titles support basic HTML, so I use <br><sup> to make a subtitle.
    full_title = f"<b>{title}</b>"
    if subtitle:
        full_title += f"<br><sup style='color:{REFERENCE_INK}'>{subtitle}</sup>"

    fig.update_layout(
        title=dict(text=full_title, x=0, xanchor="left", font=dict(size=17)),
        font=dict(family=FONT_FAMILY, size=13),
        height=height,
        margin=dict(l=10, r=20, t=90 if subtitle else 60, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, title_text=""),
        hoverlabel=dict(font_family=FONT_FAMILY),
        # 2px-ish gaps between bars so neighboring bars don't blur together
        bargap=0.25,
        bargroupgap=0.08,
    )
    # Thin, faint gridlines. The data should be the loudest thing on the chart.
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor="rgba(137,135,129,0.5)")
    fig.update_yaxes(gridcolor="rgba(137,135,129,0.2)", zeroline=False)
    return fig


def highlight_colors(labels, focus_labels) -> list:
    """
    Gives back a list of colors, blue for anything in focus_labels (Cuba/JMEC)
    and gray for everything else. Handy for bar charts where only one or two
    bars matter and the rest are context.
    """
    focus = set(focus_labels)
    return [CUBA_BLUE if lab in focus else COMPARE_GRAY for lab in labels]
