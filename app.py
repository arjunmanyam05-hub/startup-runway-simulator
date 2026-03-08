"""
Startup Runway & Growth Simulator
----------------------------------
A clean, interactive dashboard for visualizing startup financial health
and simulating what happens when key assumptions change.

Built with: Python · Streamlit · Plotly · pandas
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from data import generate_startup_data, apply_scenario

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Startup Runway Simulator",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Import fonts */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

    /* Global */
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    /* Background */
    .stApp {
        background-color: #0f1117;
        color: #e8eaf0;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #161b27;
        border-right: 1px solid #1e2535;
    }

    /* KPI Cards */
    .kpi-card {
        background: #161b27;
        border: 1px solid #1e2535;
        border-radius: 12px;
        padding: 20px 24px;
        margin: 4px 0;
    }
    .kpi-label {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #6b7280;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-family: 'DM Mono', monospace;
        font-size: 26px;
        font-weight: 500;
        color: #f1f3f7;
        line-height: 1;
    }
    .kpi-delta {
        font-size: 12px;
        margin-top: 6px;
        font-weight: 500;
    }
    .kpi-delta.positive { color: #34d399; }
    .kpi-delta.negative { color: #f87171; }
    .kpi-delta.neutral  { color: #9ca3af; }

    /* Section headers */
    .section-header {
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #6b7280;
        margin: 28px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #1e2535;
    }

    /* Scenario badge */
    .scenario-badge {
        display: inline-block;
        background: #1a2436;
        border: 1px solid #2d4a6e;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 11px;
        color: #60a5fa;
        font-weight: 500;
        letter-spacing: 0.04em;
    }

    /* Hide Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }

    /* Hide the sidebar collapse button so it can't be closed */
    [data-testid="collapsedControl"] { display: none; }
    button[kind="header"] { display: none; }
    .block-container { padding-top: 1.5rem; }

    /* Divider */
    hr { border-color: #1e2535; margin: 24px 0; }
</style>
""", unsafe_allow_html=True)

# ─── Color Palette ──────────────────────────────────────────────────────────────
COLORS = {
    "revenue":  "#34d399",   # green
    "burn":     "#f87171",   # red
    "cash":     "#60a5fa",   # blue
    "runway":   "#a78bfa",   # purple
    "baseline": "#374151",   # gray
    "scenario": "#fbbf24",   # amber (for scenario overlays)
    "bg":       "#0f1117",
    "card_bg":  "#161b27",
    "grid":     "#1e2535",
    "text":     "#e8eaf0",
    "subtext":  "#6b7280",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor=COLORS["bg"],
    plot_bgcolor=COLORS["card_bg"],
    font=dict(family="DM Sans", color=COLORS["text"], size=12),
    margin=dict(l=16, r=16, t=36, b=16),
    xaxis=dict(
        showgrid=True, gridcolor=COLORS["grid"], gridwidth=1,
        zeroline=False, tickfont=dict(size=11, color=COLORS["subtext"]),
        title_font=dict(size=11, color=COLORS["subtext"]),
    ),
    yaxis=dict(
        showgrid=True, gridcolor=COLORS["grid"], gridwidth=1,
        zeroline=False, tickfont=dict(size=11, color=COLORS["subtext"]),
        title_font=dict(size=11, color=COLORS["subtext"]),
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(size=11, color=COLORS["subtext"]),
        orientation="h",
        yanchor="bottom", y=1.02,
        xanchor="right", x=1,
    ),
    hoverlabel=dict(
        bgcolor="#1e2535",
        font_size=12,
        font_family="DM Mono",
        bordercolor="#374151",
    ),
)

# ─── Helper Functions ────────────────────────────────────────────────────────────
def fmt_currency(val: float, compact: bool = True) -> str:
    if compact:
        if abs(val) >= 1_000_000:
            return f"${val/1_000_000:.1f}M"
        if abs(val) >= 1_000:
            return f"${val/1_000:.0f}K"
    return f"${val:,.0f}"

def fmt_pct(val: float) -> str:
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.1f}%"

def delta_class(val: float, good_direction: str = "positive") -> str:
    if val == 0: return "neutral"
    positive = val > 0
    if good_direction == "positive":
        return "positive" if positive else "negative"
    else:
        return "negative" if positive else "positive"

def kpi_card(label: str, value: str, delta: str = None, delta_good: str = "positive"):
    delta_html = ""
    if delta:
        import re
        numeric = re.sub(r"[^0-9.\-]", "", delta.split()[0])
        cls = delta_class(float(numeric) if numeric else 0, delta_good)
        delta_html = f'<div class="kpi-delta {cls}">{delta}</div>'

    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

# ─── Load Data ───────────────────────────────────────────────────────────────────
@st.cache_data
def load_base_data():
    return generate_startup_data()

base_df = load_base_data()

# ─── Sidebar: Scenario Controls ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎛️ Scenario Controls")
    st.markdown("Adjust assumptions to simulate outcomes. Charts update in real time.")
    st.markdown("---")

    st.markdown("**Revenue**")
    rev_change = st.slider(
        "Monthly Revenue Change",
        min_value=-50, max_value=100, value=0, step=5,
        help="Applies a flat % shift to all monthly revenue figures",
        format="%d%%",
    )

    st.markdown("**Burn Rate**")
    burn_change = st.slider(
        "Monthly Burn Change",
        min_value=-40, max_value=80, value=0, step=5,
        help="Applies a flat % shift to all monthly burn figures (e.g. hiring, cost cuts)",
        format="%d%%",
    )

    st.markdown("---")

    # Quick scenario presets
    st.markdown("**⚡ Quick Scenarios**")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Strong Growth", use_container_width=True):
            rev_change = 30
            burn_change = 15
    with col2:
        if st.button("🔥 Efficient Mode", use_container_width=True):
            rev_change = 0
            burn_change = -20

    col3, col4 = st.columns(2)
    with col3:
        if st.button("📉 Slowdown", use_container_width=True):
            rev_change = -25
            burn_change = 0
    with col4:
        if st.button("⚠️ Crisis", use_container_width=True):
            rev_change = -40
            burn_change = 20

    st.markdown("---")
    st.markdown("""
    <div style='font-size:11px; color:#6b7280; line-height:1.6'>
    <b style='color:#9ca3af'>About</b><br>
    Simulated 24-month early-stage B2B SaaS startup. Series A injection at Month 12.<br><br>
    Built by a University of Michigan Economics grad exploring startup analytics.
    </div>
    """, unsafe_allow_html=True)

# ─── Apply Scenario ──────────────────────────────────────────────────────────────
scenario_df = apply_scenario(base_df, rev_change / 100, burn_change / 100)
is_scenario = rev_change != 0 or burn_change != 0

# Latest month stats
latest_base = base_df.iloc[-1]
latest = scenario_df.iloc[-1]

# ─── Header ─────────────────────────────────────────────────────────────────────
col_title, col_badge = st.columns([4, 1])
with col_title:
    st.markdown("## Startup Runway & Growth Simulator")
    st.markdown('<p style="color:#6b7280; font-size:14px; margin-top:-8px;">Financial health dashboard · 24-month early-stage B2B SaaS model</p>', unsafe_allow_html=True)
with col_badge:
    if is_scenario:
        rev_label = fmt_pct(rev_change)
        burn_label = fmt_pct(burn_change)
        st.markdown(f"""
        <div style="text-align:right; padding-top:12px;">
            <span class="scenario-badge">📊 Scenario: Rev {rev_label} / Burn {burn_label}</span>
        </div>
        """, unsafe_allow_html=True)

# ─── KPI Row ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Current Metrics (Month 24)</div>', unsafe_allow_html=True)

k1, k2, k3, k4, k5 = st.columns(5)

# Revenue
rev_growth = ((scenario_df.iloc[-1]["revenue"] / scenario_df.iloc[-2]["revenue"]) - 1) * 100
with k1:
    kpi_card("Monthly Revenue", fmt_currency(latest["revenue"]), fmt_pct(rev_growth) + " MoM")

# Burn
with k2:
    kpi_card("Monthly Burn", fmt_currency(latest["burn"]), None)

# Net Burn
net = latest["net_burn"]
with k3:
    label = "Net Burn" if net > 0 else "Net Revenue"
    kpi_card(label, fmt_currency(net), None, "negative" if net > 0 else "positive")

# Cash on Hand
with k4:
    kpi_card("Cash on Hand", fmt_currency(latest["cash_on_hand"]), None)

# Runway
runway = latest["runway_months"]
runway_color = "positive" if runway > 12 else ("neutral" if runway > 6 else "negative")
with k5:
    kpi_card("Runway", f"{max(runway, 0):.1f} mo", None)

# ─── Charts ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Trends Over 24 Months</div>', unsafe_allow_html=True)

month_labels = [f"M{m}" for m in base_df["month"]]

def add_funding_annotation(fig, df):
    for _, row in df[df["funding_event"] > 0].iterrows():
        # Use integer index position (0-based) for categorical x-axis
        idx = int(row['month']) - 1
        fig.add_shape(
            type="line",
            x0=idx, x1=idx, y0=0, y1=1,
            xref="x", yref="paper",
            line=dict(color="#fbbf24", width=1.5, dash="dot"),
        )
        fig.add_annotation(
            x=idx, y=1,
            xref="x", yref="paper",
            text="Series A",
            showarrow=False,
            font=dict(color="#fbbf24", size=10),
            yanchor="bottom",
        )
    return fig

# ── Chart 1 & 2: Revenue and Burn side by side ──────────────────────────────────
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    fig = go.Figure()
    if is_scenario:
        fig.add_trace(go.Scatter(
            x=month_labels, y=base_df["revenue"],
            name="Baseline", mode="lines",
            line=dict(color=COLORS["baseline"], width=1.5, dash="dot"),
            hovertemplate="Baseline: $%{y:,.0f}<extra></extra>",
        ))
    fig.add_trace(go.Scatter(
        x=month_labels, y=scenario_df["revenue"],
        name="Revenue", mode="lines+markers",
        line=dict(color=COLORS["revenue"], width=2.5),
        marker=dict(size=4),
        fill="tozeroy", fillcolor="rgba(52,211,153,0.07)",
        hovertemplate="Revenue: $%{y:,.0f}<extra></extra>",
    ))
    add_funding_annotation(fig, base_df)
    fig.update_layout(**PLOTLY_LAYOUT, title="Monthly Revenue", height=260,
                      yaxis_tickprefix="$", yaxis_tickformat=",")
    st.plotly_chart(fig, use_container_width=True)

with chart_col2:
    fig = go.Figure()
    if is_scenario:
        fig.add_trace(go.Scatter(
            x=month_labels, y=base_df["burn"],
            name="Baseline", mode="lines",
            line=dict(color=COLORS["baseline"], width=1.5, dash="dot"),
            hovertemplate="Baseline: $%{y:,.0f}<extra></extra>",
        ))
    fig.add_trace(go.Scatter(
        x=month_labels, y=scenario_df["burn"],
        name="Burn", mode="lines+markers",
        line=dict(color=COLORS["burn"], width=2.5),
        marker=dict(size=4),
        fill="tozeroy", fillcolor="rgba(248,113,113,0.07)",
        hovertemplate="Burn: $%{y:,.0f}<extra></extra>",
    ))
    add_funding_annotation(fig, base_df)
    fig.update_layout(**PLOTLY_LAYOUT, title="Monthly Burn Rate", height=260,
                      yaxis_tickprefix="$", yaxis_tickformat=",")
    st.plotly_chart(fig, use_container_width=True)

# ── Chart 3: Cash on Hand ────────────────────────────────────────────────────────
fig = go.Figure()
if is_scenario:
    fig.add_trace(go.Scatter(
        x=month_labels, y=base_df["cash_on_hand"],
        name="Baseline Cash", mode="lines",
        line=dict(color=COLORS["baseline"], width=1.5, dash="dot"),
        hovertemplate="Baseline: $%{y:,.0f}<extra></extra>",
    ))
fig.add_trace(go.Scatter(
    x=month_labels, y=scenario_df["cash_on_hand"],
    name="Cash on Hand", mode="lines+markers",
    line=dict(color=COLORS["cash"], width=2.5),
    marker=dict(size=4),
    fill="tozeroy", fillcolor="rgba(96,165,250,0.07)",
    hovertemplate="Cash: $%{y:,.0f}<extra></extra>",
))
add_funding_annotation(fig, base_df)
fig.update_layout(**PLOTLY_LAYOUT, title="Cash on Hand", height=260,
                  yaxis_tickprefix="$", yaxis_tickformat=",")
st.plotly_chart(fig, use_container_width=True)

# ── Chart 4 & 5: Runway + Revenue vs Burn ───────────────────────────────────────
chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    fig = go.Figure()
    # Color runway bars based on risk level
    runway_vals = scenario_df["runway_months"].clip(lower=0)
    bar_colors = [
        "#34d399" if v > 12 else ("#fbbf24" if v > 6 else "#f87171")
        for v in runway_vals
    ]
    fig.add_trace(go.Bar(
        x=month_labels, y=runway_vals,
        name="Runway (months)",
        marker_color=bar_colors,
        hovertemplate="Runway: %{y:.1f} months<extra></extra>",
    ))
    # Add 6-month and 12-month threshold lines
    fig.add_hline(y=6,  line_dash="dot", line_color="#fbbf24", line_width=1,
                  annotation_text="6 mo", annotation_font=dict(color="#fbbf24", size=10))
    fig.add_hline(y=12, line_dash="dot", line_color="#34d399", line_width=1,
                  annotation_text="12 mo", annotation_font=dict(color="#34d399", size=10))
    fig.update_layout(**PLOTLY_LAYOUT, title="Runway (Months Remaining)", height=260,
                      yaxis_title="Months", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with chart_col4:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=month_labels, y=scenario_df["revenue"],
        name="Revenue", marker_color=COLORS["revenue"],
        opacity=0.85,
        hovertemplate="Revenue: $%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=month_labels, y=scenario_df["burn"],
        name="Burn", marker_color=COLORS["burn"],
        opacity=0.85,
        hovertemplate="Burn: $%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(**PLOTLY_LAYOUT, title="Revenue vs. Burn", height=260,
                      barmode="group", yaxis_tickprefix="$", yaxis_tickformat=",")
    st.plotly_chart(fig, use_container_width=True)

# ─── Raw Data Toggle ─────────────────────────────────────────────────────────────
with st.expander("🗂️  View underlying data"):
    display_df = scenario_df[["month","revenue","burn","net_burn","cash_on_hand","runway_months","headcount","funding_event"]].copy()
    display_df.columns = ["Month","Revenue","Burn","Net Burn","Cash on Hand","Runway (mo)","Headcount","Funding Event"]
    st.dataframe(
        display_df.style.format({
            "Revenue": "${:,.0f}", "Burn": "${:,.0f}",
            "Net Burn": "${:,.0f}", "Cash on Hand": "${:,.0f}",
            "Funding Event": "${:,.0f}", "Runway (mo)": "{:.1f}",
        }),
        use_container_width=True,
        hide_index=True,
    )
    st.download_button(
        "⬇️ Download CSV",
        data=display_df.to_csv(index=False),
        file_name="startup_simulation.csv",
        mime="text/csv",
    )