"""
Startup Runway & Growth Simulator
----------------------------------
A clean, interactive dashboard for visualizing startup financial health
and simulating what happens when key assumptions change.

Built with: Python · Streamlit · Plotly · pandas
"""

import re
import streamlit as st
import plotly.graph_objects as go
from data import generate_startup_data, apply_scenario

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Startup Runway Simulator",
    page_icon="📈",
    layout="wide",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

    .stApp { background-color: #0f1117; color: #e8eaf0; }

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
    .kpi-delta { font-size: 12px; margin-top: 6px; font-weight: 500; }
    .kpi-delta.positive { color: #34d399; }
    .kpi-delta.negative { color: #f87171; }
    .kpi-delta.neutral  { color: #9ca3af; }

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

    .scenario-panel {
        background: #161b27;
        border: 1px solid #1e2535;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 8px;
    }

    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stSidebar"] { display: none; }
    .block-container { padding-top: 1.5rem; }
    hr { border-color: #1e2535; margin: 24px 0; }
</style>
""", unsafe_allow_html=True)

# ─── Color Palette ──────────────────────────────────────────────────────────────
COLORS = {
    "revenue":  "#34d399",
    "burn":     "#f87171",
    "cash":     "#60a5fa",
    "runway":   "#a78bfa",
    "baseline": "#374151",
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
        zeroline=False,
        tickfont=dict(size=11, color=COLORS["subtext"]),
        title_font=dict(size=11, color=COLORS["subtext"]),
    ),
    yaxis=dict(
        showgrid=True, gridcolor=COLORS["grid"], gridwidth=1,
        zeroline=False,
        tickfont=dict(size=11, color=COLORS["subtext"]),
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
def fmt_currency(val: float) -> str:
    """Format a number as a compact currency string."""
    if abs(val) >= 1_000_000:
        return f"${val / 1_000_000:.1f}M"
    if abs(val) >= 1_000:
        return f"${val / 1_000:.0f}K"
    return f"${val:,.0f}"

def fmt_pct(val: float) -> str:
    """Format a float as a signed percentage string."""
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.1f}%"

def delta_class(val: float, good_direction: str = "positive") -> str:
    """Return CSS class name based on whether the delta is good or bad."""
    if val == 0:
        return "neutral"
    is_positive = val > 0
    if good_direction == "positive":
        return "positive" if is_positive else "negative"
    else:
        return "negative" if is_positive else "positive"

def kpi_card(label: str, value: str, delta: str = None, delta_good: str = "positive") -> None:
    """Render a styled KPI card using HTML markdown."""
    delta_html = ""
    if delta:
        numeric_str = re.sub(r"[^0-9.\-]", "", delta.split()[0])
        numeric_val = float(numeric_str) if numeric_str else 0.0
        css_class = delta_class(numeric_val, delta_good)
        delta_html = f'<div class="kpi-delta {css_class}">{delta}</div>'

    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def add_funding_annotation(fig: go.Figure, df) -> go.Figure:
    """Add a vertical dotted line and label for any funding events in the dataset."""
    for _, row in df[df["funding_event"] > 0].iterrows():
        idx = int(row["month"]) - 1  # 0-based index for categorical x-axis
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

# ─── Load Base Data ──────────────────────────────────────────────────────────────
@st.cache_data
def load_base_data():
    return generate_startup_data()

base_df = load_base_data()

# ─── Header ─────────────────────────────────────────────────────────────────────
st.markdown("## 📈 Startup Runway & Growth Simulator")
st.markdown(
    '<p style="color:#6b7280; font-size:14px; margin-top:-8px;">'
    'Financial health dashboard · 24-month early-stage B2B SaaS model'
    '</p>',
    unsafe_allow_html=True,
)

# ─── Scenario Controls (inline, no sidebar) ─────────────────────────────────────
st.markdown('<div class="section-header">Scenario Controls</div>', unsafe_allow_html=True)
st.markdown('<div class="scenario-panel">', unsafe_allow_html=True)

slider_col1, slider_col2 = st.columns(2)
with slider_col1:
    rev_change = st.slider(
        "📈 Revenue Change (%)",
        min_value=-50, max_value=100, value=0, step=5,
        help="Shift all monthly revenue figures up or down by this percentage.",
        format="%d%%",
    )
with slider_col2:
    burn_change = st.slider(
        "🔥 Burn Rate Change (%)",
        min_value=-40, max_value=80, value=0, step=5,
        help="Shift all monthly burn figures up or down (e.g. hiring surge or cost cuts).",
        format="%d%%",
    )

st.markdown(
    '<p style="font-size:12px; color:#6b7280; margin: 12px 0 8px 0;">⚡ Quick Scenarios</p>',
    unsafe_allow_html=True,
)

btn1, btn2, btn3, btn4, _ = st.columns([1, 1, 1, 1, 3])
with btn1:
    strong_growth = st.button("🚀 Strong Growth", use_container_width=True)
with btn2:
    efficient = st.button("✂️ Efficient Mode", use_container_width=True)
with btn3:
    slowdown = st.button("📉 Slowdown", use_container_width=True)
with btn4:
    crisis = st.button("⚠️ Crisis", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# Apply quick scenario button overrides
if strong_growth:
    rev_change = 30
    burn_change = 15
elif efficient:
    rev_change = 0
    burn_change = -20
elif slowdown:
    rev_change = -25
    burn_change = 0
elif crisis:
    rev_change = -40
    burn_change = 20

# ─── Apply Scenario to Data ──────────────────────────────────────────────────────
scenario_df = apply_scenario(base_df, rev_change / 100, burn_change / 100)
is_scenario = rev_change != 0 or burn_change != 0

# Latest month row for KPI cards
latest = scenario_df.iloc[-1]

# ─── KPI Row ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Current Metrics — Month 24</div>', unsafe_allow_html=True)

k1, k2, k3, k4, k5 = st.columns(5)

rev_growth_pct = (
    (scenario_df.iloc[-1]["revenue"] / scenario_df.iloc[-2]["revenue"]) - 1
) * 100

with k1:
    kpi_card(
        "Monthly Revenue",
        fmt_currency(latest["revenue"]),
        fmt_pct(rev_growth_pct) + " MoM",
        delta_good="positive",
    )

with k2:
    kpi_card("Monthly Burn", fmt_currency(latest["burn"]))

with k3:
    net = latest["net_burn"]
    net_label = "Net Burn" if net > 0 else "Net Revenue"
    kpi_card(net_label, fmt_currency(net), delta_good="negative" if net > 0 else "positive")

with k4:
    kpi_card("Cash on Hand", fmt_currency(latest["cash_on_hand"]))

with k5:
    runway_val = max(latest["runway_months"], 0)
    kpi_card("Runway", f"{runway_val:.1f} mo")

# ─── Charts ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Trends Over 24 Months</div>', unsafe_allow_html=True)

month_labels = [f"M{m}" for m in base_df["month"]]

# ── Row 1: Revenue + Burn ────────────────────────────────────────────────────────
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
    fig.update_layout(
        **PLOTLY_LAYOUT, title="Monthly Revenue", height=260,
        yaxis_tickprefix="$", yaxis_tickformat=",",
    )
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
    fig.update_layout(
        **PLOTLY_LAYOUT, title="Monthly Burn Rate", height=260,
        yaxis_tickprefix="$", yaxis_tickformat=",",
    )
    st.plotly_chart(fig, use_container_width=True)

# ── Row 2: Cash on Hand (full width) ────────────────────────────────────────────
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
fig.update_layout(
    **PLOTLY_LAYOUT, title="Cash on Hand", height=260,
    yaxis_tickprefix="$", yaxis_tickformat=",",
)
st.plotly_chart(fig, use_container_width=True)

# ── Row 3: Runway + Revenue vs Burn ─────────────────────────────────────────────
chart_col3, chart_col4 = st.columns(2)

with chart_col3:
    runway_vals = scenario_df["runway_months"].clip(lower=0)
    bar_colors = [
        "#34d399" if v > 12 else ("#fbbf24" if v > 6 else "#f87171")
        for v in runway_vals
    ]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=month_labels, y=runway_vals,
        name="Runway (months)",
        marker_color=bar_colors,
        hovertemplate="Runway: %{y:.1f} months<extra></extra>",
    ))
    fig.add_hline(
        y=6, line_dash="dot", line_color="#fbbf24", line_width=1,
        annotation_text="6 mo", annotation_font=dict(color="#fbbf24", size=10),
    )
    fig.add_hline(
        y=12, line_dash="dot", line_color="#34d399", line_width=1,
        annotation_text="12 mo", annotation_font=dict(color="#34d399", size=10),
    )
    fig.update_layout(
        **PLOTLY_LAYOUT, title="Runway (Months Remaining)", height=260,
        yaxis_title="Months", showlegend=False,
    )
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
    fig.update_layout(
        **PLOTLY_LAYOUT, title="Revenue vs. Burn", height=260,
        barmode="group", yaxis_tickprefix="$", yaxis_tickformat=",",
    )
    st.plotly_chart(fig, use_container_width=True)

# ─── Raw Data Table ──────────────────────────────────────────────────────────────
with st.expander("🗂️  View underlying data"):
    display_df = scenario_df[[
        "month", "revenue", "burn", "net_burn",
        "cash_on_hand", "runway_months", "headcount", "funding_event",
    ]].copy()
    display_df.columns = [
        "Month", "Revenue", "Burn", "Net Burn",
        "Cash on Hand", "Runway (mo)", "Headcount", "Funding Event",
    ]
    st.dataframe(
        display_df.style.format({
            "Revenue": "${:,.0f}",
            "Burn": "${:,.0f}",
            "Net Burn": "${:,.0f}",
            "Cash on Hand": "${:,.0f}",
            "Funding Event": "${:,.0f}",
            "Runway (mo)": "{:.1f}",
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