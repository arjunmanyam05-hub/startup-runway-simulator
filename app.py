"""
Startup Runway & Growth Simulator
----------------------------------
Interactive financial health dashboard for an early-stage B2B SaaS startup.
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

# ─── Session State Init ──────────────────────────────────────────────────────────
if "rev_change" not in st.session_state:
    st.session_state["rev_change"] = 0
if "burn_change" not in st.session_state:
    st.session_state["burn_change"] = 0
if "active_scenario" not in st.session_state:
    st.session_state["active_scenario"] = None
if "rev_change_widget" not in st.session_state:
    st.session_state["rev_change_widget"] = 0
if "burn_change_widget" not in st.session_state:
    st.session_state["burn_change_widget"] = 0

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background-color: #0f1117; color: #e8eaf0; }

    .kpi-card {
        background: #161b27; border: 1px solid #1e2535;
        border-radius: 12px; padding: 20px 24px; margin: 4px 0;
        transition: border-color 0.2s;
    }
    .kpi-card:hover { border-color: #374151; }
    .kpi-label {
        font-size: 11px; font-weight: 600; letter-spacing: 0.08em;
        text-transform: uppercase; color: #6b7280; margin-bottom: 6px;
    }
    .kpi-value {
        font-family: 'DM Mono', monospace; font-size: 26px;
        font-weight: 500; color: #f1f3f7; line-height: 1;
    }
    .kpi-delta { font-size: 12px; margin-top: 6px; font-weight: 500; }
    .kpi-delta.positive { color: #34d399; }
    .kpi-delta.negative { color: #f87171; }
    .kpi-delta.neutral  { color: #9ca3af; }

    .section-header {
        font-size: 13px; font-weight: 600; letter-spacing: 0.06em;
        text-transform: uppercase; color: #6b7280;
        margin: 28px 0 12px 0; padding-bottom: 8px;
        border-bottom: 1px solid #1e2535;
    }

    .scenario-panel {
        background: #161b27; border: 1px solid #1e2535;
        border-radius: 12px; padding: 20px 24px 20px 24px; margin-bottom: 8px;
    }

    /* Base button style for ALL buttons */
    div[data-testid="stButton"] button {
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        border-radius: 8px !important;
        width: 100% !important;
        padding: 8px 12px !important;
        transition: all 0.15s ease !important;
        cursor: pointer !important;
    }

    /* Strong Growth — green */
    div[data-testid="stButton"]:has(button[data-testid="btn_strong"]) button,
    div[data-testid="stButton"]:nth-of-type(1) button {
        background: #052e16 !important;
        border: 1.5px solid #16a34a !important;
        color: #4ade80 !important;
    }
    div[data-testid="stButton"]:has(button[data-testid="btn_strong"]) button:hover {
        background: #064e24 !important;
        box-shadow: 0 0 10px rgba(74,222,128,0.25) !important;
    }

    /* Efficient Mode — blue */
    div[data-testid="stButton"]:has(button[data-testid="btn_efficient"]) button {
        background: #0c1a2e !important;
        border: 1.5px solid #2563eb !important;
        color: #60a5fa !important;
    }
    div[data-testid="stButton"]:has(button[data-testid="btn_efficient"]) button:hover {
        background: #162d4e !important;
        box-shadow: 0 0 10px rgba(96,165,250,0.25) !important;
    }

    /* Slowdown — amber */
    div[data-testid="stButton"]:has(button[data-testid="btn_slowdown"]) button {
        background: #1c1407 !important;
        border: 1.5px solid #d97706 !important;
        color: #fbbf24 !important;
    }
    div[data-testid="stButton"]:has(button[data-testid="btn_slowdown"]) button:hover {
        background: #2e200a !important;
        box-shadow: 0 0 10px rgba(251,191,36,0.25) !important;
    }

    /* Crisis — red */
    div[data-testid="stButton"]:has(button[data-testid="btn_crisis"]) button {
        background: #1c0a0a !important;
        border: 1.5px solid #dc2626 !important;
        color: #f87171 !important;
    }
    div[data-testid="stButton"]:has(button[data-testid="btn_crisis"]) button:hover {
        background: #2e1010 !important;
        box-shadow: 0 0 10px rgba(248,113,113,0.25) !important;
    }

    /* Reset — neutral gray */
    div[data-testid="stButton"]:has(button[data-testid="btn_reset"]) button {
        background: #161b27 !important;
        border: 1.5px solid #4b5563 !important;
        color: #d1d5db !important;
    }
    div[data-testid="stButton"]:has(button[data-testid="btn_reset"]) button:hover {
        background: #1f2937 !important;
        border-color: #9ca3af !important;
        color: #f9fafb !important;
    }

    .active-badge {
        display:inline-flex; align-items:center; gap:6px;
        background:#1a2436; border:1px solid #2d4a6e;
        border-radius:20px; padding:5px 14px;
        font-size:12px; color:#60a5fa; font-weight:600;
    }

    .insight-box {
        border-left:3px solid #60a5fa; border-radius:0 8px 8px 0;
        padding:12px 16px; margin:12px 0 4px 0;
        font-size:13px; line-height:1.6;
    }
    .insight-box.info    { background:#0d1a2e; border-left-color:#60a5fa; color:#93c5fd; }
    .insight-box.warning { background:#1c1407; border-left-color:#f59e0b; color:#fcd34d; }
    .insight-box.danger  { background:#1c0a0a; border-left-color:#ef4444; color:#fca5a5; }
    .insight-box.success { background:#052e16; border-left-color:#22c55e; color:#86efac; }

    #MainMenu, footer, header { visibility:hidden; }
    [data-testid="stSidebar"] { display:none; }
    .block-container { padding-top:1.5rem; max-width:1400px; }
    hr { border-color:#1e2535; margin:24px 0; }
</style>
""", unsafe_allow_html=True)

# ─── Color Palette ──────────────────────────────────────────────────────────────
COLORS = {
    "revenue": "#34d399", "burn": "#f87171", "cash": "#60a5fa",
    "baseline": "#374151", "bg": "#0f1117", "card_bg": "#161b27",
    "grid": "#1e2535", "text": "#e8eaf0", "subtext": "#6b7280",
}

PLOTLY_LAYOUT = dict(
    paper_bgcolor=COLORS["bg"], plot_bgcolor=COLORS["card_bg"],
    font=dict(family="DM Sans", color=COLORS["text"], size=12),
    margin=dict(l=16, r=16, t=40, b=16),
    xaxis=dict(showgrid=True, gridcolor=COLORS["grid"], gridwidth=1, zeroline=False,
               tickfont=dict(size=11, color=COLORS["subtext"]),
               title_font=dict(size=11, color=COLORS["subtext"])),
    yaxis=dict(showgrid=True, gridcolor=COLORS["grid"], gridwidth=1, zeroline=False,
               tickfont=dict(size=11, color=COLORS["subtext"]),
               title_font=dict(size=11, color=COLORS["subtext"])),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11, color=COLORS["subtext"]),
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hoverlabel=dict(bgcolor="#1e2535", font_size=12, font_family="DM Mono", bordercolor="#374151"),
)

# ─── Helpers ────────────────────────────────────────────────────────────────────
def fmt_currency(val: float) -> str:
    if abs(val) >= 1_000_000: return f"${val/1_000_000:.1f}M"
    if abs(val) >= 1_000:     return f"${val/1_000:.0f}K"
    return f"${val:,.0f}"

def fmt_pct(val: float) -> str:
    return f"{'+'if val>=0 else ''}{val:.1f}%"

def delta_class(val: float, good: str = "positive") -> str:
    if val == 0: return "neutral"
    pos = val > 0
    return ("positive" if pos else "negative") if good == "positive" else ("negative" if pos else "positive")

def kpi_card(label: str, value: str, delta: str = None, delta_good: str = "positive") -> None:
    delta_html = ""
    if delta:
        num = re.sub(r"[^0-9.\-]", "", delta.split()[0])
        css = delta_class(float(num) if num else 0.0, delta_good)
        delta_html = f'<div class="kpi-delta {css}">{delta}</div>'
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>""", unsafe_allow_html=True)

def add_funding_annotation(fig: go.Figure, df) -> go.Figure:
    for _, row in df[df["funding_event"] > 0].iterrows():
        idx = int(row["month"]) - 1
        fig.add_shape(type="line", x0=idx, x1=idx, y0=0, y1=1,
                      xref="x", yref="paper",
                      line=dict(color="#fbbf24", width=1.5, dash="dot"))
        fig.add_annotation(x=idx, y=1, xref="x", yref="paper",
                           text="Series A", showarrow=False,
                           font=dict(color="#fbbf24", size=10), yanchor="bottom")
    return fig

def runway_insight(runway: float) -> tuple:
    if runway <= 0:
        return ("danger", "⛔ Company has run out of cash under these assumptions. Emergency fundraising or deep cuts required immediately.")
    elif runway < 6:
        return ("danger", f"🚨 Only {runway:.1f} months of runway. The company needs to raise or cut costs urgently — most investors want 18+ months before leading a round.")
    elif runway < 12:
        return ("warning", f"⚠️ {runway:.1f} months of runway. Below the typical 18-month fundraising buffer. Time to start investor conversations or tighten operations.")
    elif runway < 18:
        return ("warning", f"🟡 {runway:.1f} months of runway. Healthy but worth monitoring. A 10% revenue miss could push this toward the danger zone.")
    else:
        return ("success", f"✅ {runway:.1f} months of runway. Strong position — enough breathing room to focus on growth. Series B conversations can happen from a position of strength.")

# ─── Load Data ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_base_data():
    return generate_startup_data()

base_df = load_base_data()

# ─── Header ─────────────────────────────────────────────────────────────────────
header_col, badge_col = st.columns([5, 1])
with header_col:
    st.markdown("## 📈 Startup Runway & Growth Simulator")
    st.markdown(
        '<p style="color:#6b7280;font-size:14px;margin-top:-8px;">'
        'Financial health dashboard · 24-month early-stage B2B SaaS model</p>',
        unsafe_allow_html=True)
with badge_col:
    if st.session_state["active_scenario"]:
        st.markdown(
            f'<div style="padding-top:18px;text-align:right">'
            f'<span class="active-badge">📊 {st.session_state["active_scenario"]}</span></div>',
            unsafe_allow_html=True)

# ─── Scenario Controls ───────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Scenario Controls</div>', unsafe_allow_html=True)
st.markdown('<div class="scenario-panel">', unsafe_allow_html=True)

slider_col1, slider_col2 = st.columns(2)
with slider_col1:
    st.slider("📈 Revenue Change (%)", min_value=-50, max_value=100, step=5,
              format="%d%%", help="Shift all monthly revenue up or down.",
              value=st.session_state["rev_change"],
              key="rev_change_widget")
with slider_col2:
    st.slider("🔥 Burn Rate Change (%)", min_value=-40, max_value=80, step=5,
              format="%d%%", help="Shift all monthly burn up or down.",
              value=st.session_state["burn_change"],
              key="burn_change_widget")

# Only sync slider → session state when user manually drags (no active scenario)
if st.session_state["active_scenario"] is None:
    st.session_state["rev_change"] = st.session_state["rev_change_widget"]
    st.session_state["burn_change"] = st.session_state["burn_change_widget"]

st.markdown('<p style="font-size:12px;color:#6b7280;margin:14px 0 10px 0;">⚡ Quick Scenarios</p>',
            unsafe_allow_html=True)

bcol1, bcol2, bcol3, bcol4, bcol5, _ = st.columns([1.1, 1.1, 1, 1, 0.85, 2])

with bcol1:
    clicked_strong = st.button("🚀 Strong Growth", key="btn_strong", use_container_width=True)
with bcol2:
    clicked_efficient = st.button("✂️ Efficient Mode", key="btn_efficient", use_container_width=True)
with bcol3:
    clicked_slowdown = st.button("📉 Slowdown", key="btn_slowdown", use_container_width=True)
with bcol4:
    clicked_crisis = st.button("⚠️ Crisis", key="btn_crisis", use_container_width=True)
with bcol5:
    clicked_reset = st.button("↺ Reset", key="btn_reset", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)  # close scenario-panel

# Process button clicks — update session state then rerun so sliders reflect new values
if clicked_strong:
    st.session_state["rev_change"] = 30
    st.session_state["burn_change"] = 15
    st.session_state["active_scenario"] = "Strong Growth"
    st.rerun()
elif clicked_efficient:
    st.session_state["rev_change"] = 0
    st.session_state["burn_change"] = -20
    st.session_state["active_scenario"] = "Efficient Mode"
    st.rerun()
elif clicked_slowdown:
    st.session_state["rev_change"] = -25
    st.session_state["burn_change"] = 0
    st.session_state["active_scenario"] = "Slowdown"
    st.rerun()
elif clicked_crisis:
    st.session_state["rev_change"] = -40
    st.session_state["burn_change"] = 20
    st.session_state["active_scenario"] = "Crisis"
    st.rerun()
elif clicked_reset:
    st.session_state["rev_change"] = 0
    st.session_state["burn_change"] = 0
    st.session_state["active_scenario"] = None
    st.rerun()

# ─── Read values and apply scenario ─────────────────────────────────────────────
rev_change  = st.session_state["rev_change"]
burn_change = st.session_state["burn_change"]
is_scenario = rev_change != 0 or burn_change != 0

scenario_df = apply_scenario(base_df, rev_change / 100, burn_change / 100)
latest = scenario_df.iloc[-1]

# ─── Insight Banner ──────────────────────────────────────────────────────────────
runway_val = max(latest["runway_months"], 0)
insight_type, insight_text = runway_insight(runway_val)
st.markdown(f'<div class="insight-box {insight_type}">{insight_text}</div>',
            unsafe_allow_html=True)

# ─── KPI Cards ───────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Current Metrics — Month 24</div>', unsafe_allow_html=True)

k1, k2, k3, k4, k5 = st.columns(5)
rev_growth_pct = ((scenario_df.iloc[-1]["revenue"] / scenario_df.iloc[-2]["revenue"]) - 1) * 100

with k1:
    kpi_card("Monthly Revenue", fmt_currency(latest["revenue"]),
             fmt_pct(rev_growth_pct) + " MoM", delta_good="positive")
with k2:
    kpi_card("Monthly Burn", fmt_currency(latest["burn"]))
with k3:
    net = latest["net_burn"]
    kpi_card("Net Burn" if net > 0 else "Net Revenue", fmt_currency(net),
             delta_good="negative" if net > 0 else "positive")
with k4:
    kpi_card("Cash on Hand", fmt_currency(latest["cash_on_hand"]))
with k5:
    kpi_card("Runway", f"{runway_val:.1f} mo")

# ─── Scenario Delta Row (only shown when a scenario is active) ──────────────────
if is_scenario:
    base_latest = base_df.iloc[-1]
    rev_delta = latest["revenue"] - base_latest["revenue"]
    burn_delta = latest["burn"] - base_latest["burn"]
    cash_delta = latest["cash_on_hand"] - base_latest["cash_on_hand"]
    runway_delta = runway_val - max(base_latest["runway_months"], 0)

    def delta_arrow(val, good="positive"):
        if val == 0: return "─"
        up = val > 0
        arrow = "▲" if up else "▼"
        color = "#34d399" if (up and good == "positive") or (not up and good == "negative") else "#f87171"
        return f'<span style="color:{color};font-size:11px;font-weight:600">{arrow} {fmt_currency(abs(val)) if abs(val) >= 100 else f"{abs(val):.1f}"}</span>'

    st.markdown(f"""
    <div style="display:flex;gap:12px;margin:8px 0 4px 0;padding:12px 16px;
                background:#0d1117;border:1px solid #1e2535;border-radius:10px;
                font-size:12px;color:#6b7280;align-items:center;">
        <span style="font-weight:600;color:#9ca3af;margin-right:4px;">vs. Baseline →</span>
        <span>Revenue: {delta_arrow(rev_delta, "positive")}</span>
        <span style="color:#374151">|</span>
        <span>Burn: {delta_arrow(burn_delta, "negative")}</span>
        <span style="color:#374151">|</span>
        <span>Cash: {delta_arrow(cash_delta, "positive")}</span>
        <span style="color:#374151">|</span>
        <span>Runway: {delta_arrow(runway_delta, "positive")} mo</span>
    </div>
    """, unsafe_allow_html=True)

# ─── Charts ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Trends Over 24 Months</div>', unsafe_allow_html=True)

month_labels = [f"M{m}" for m in base_df["month"]]

# Row 1: Revenue + Burn
c1, c2 = st.columns(2)
with c1:
    fig = go.Figure()
    if is_scenario:
        fig.add_trace(go.Scatter(x=month_labels, y=base_df["revenue"], name="Baseline",
            mode="lines", line=dict(color=COLORS["baseline"], width=1.5, dash="dot"),
            hovertemplate="Baseline: $%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=month_labels, y=scenario_df["revenue"], name="Revenue",
        mode="lines+markers", line=dict(color=COLORS["revenue"], width=2.5),
        marker=dict(size=4), fill="tozeroy", fillcolor="rgba(52,211,153,0.07)",
        hovertemplate="Revenue: $%{y:,.0f}<extra></extra>"))
    add_funding_annotation(fig, base_df)
    fig.update_layout(**PLOTLY_LAYOUT, title="Monthly Revenue", height=270,
                      yaxis_tickprefix="$", yaxis_tickformat=",")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    fig = go.Figure()
    if is_scenario:
        fig.add_trace(go.Scatter(x=month_labels, y=base_df["burn"], name="Baseline",
            mode="lines", line=dict(color=COLORS["baseline"], width=1.5, dash="dot"),
            hovertemplate="Baseline: $%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=month_labels, y=scenario_df["burn"], name="Burn",
        mode="lines+markers", line=dict(color=COLORS["burn"], width=2.5),
        marker=dict(size=4), fill="tozeroy", fillcolor="rgba(248,113,113,0.07)",
        hovertemplate="Burn: $%{y:,.0f}<extra></extra>"))
    add_funding_annotation(fig, base_df)
    fig.update_layout(**PLOTLY_LAYOUT, title="Monthly Burn Rate", height=270,
                      yaxis_tickprefix="$", yaxis_tickformat=",")
    st.plotly_chart(fig, use_container_width=True)

# Row 2: Cash on Hand
fig = go.Figure()
if is_scenario:
    fig.add_trace(go.Scatter(x=month_labels, y=base_df["cash_on_hand"], name="Baseline Cash",
        mode="lines", line=dict(color=COLORS["baseline"], width=1.5, dash="dot"),
        hovertemplate="Baseline: $%{y:,.0f}<extra></extra>"))
fig.add_trace(go.Scatter(x=month_labels, y=scenario_df["cash_on_hand"], name="Cash on Hand",
    mode="lines+markers", line=dict(color=COLORS["cash"], width=2.5),
    marker=dict(size=4), fill="tozeroy", fillcolor="rgba(96,165,250,0.07)",
    hovertemplate="Cash: $%{y:,.0f}<extra></extra>"))
add_funding_annotation(fig, base_df)
fig.update_layout(**PLOTLY_LAYOUT, title="Cash on Hand", height=270,
                  yaxis_tickprefix="$", yaxis_tickformat=",")
st.plotly_chart(fig, use_container_width=True)

# Row 3: Runway + Revenue vs Burn
c3, c4 = st.columns(2)
with c3:
    runway_vals = scenario_df["runway_months"].clip(lower=0)
    bar_colors = ["#34d399" if v > 12 else ("#fbbf24" if v > 6 else "#f87171") for v in runway_vals]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=month_labels, y=runway_vals, name="Runway",
        marker_color=bar_colors, hovertemplate="Runway: %{y:.1f} months<extra></extra>"))
    fig.add_hline(y=6, line_dash="dot", line_color="#fbbf24", line_width=1,
                  annotation_text="6 mo", annotation_font=dict(color="#fbbf24", size=10))
    fig.add_hline(y=12, line_dash="dot", line_color="#34d399", line_width=1,
                  annotation_text="12 mo", annotation_font=dict(color="#34d399", size=10))
    fig.update_layout(**PLOTLY_LAYOUT, title="Runway (Months Remaining)", height=270,
                      yaxis_title="Months", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with c4:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=month_labels, y=scenario_df["revenue"], name="Revenue",
        marker_color=COLORS["revenue"], opacity=0.85,
        hovertemplate="Revenue: $%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Bar(x=month_labels, y=scenario_df["burn"], name="Burn",
        marker_color=COLORS["burn"], opacity=0.85,
        hovertemplate="Burn: $%{y:,.0f}<extra></extra>"))
    # Annotate the first month revenue exceeds burn (default profitability)
    crossover = scenario_df[scenario_df["revenue"] >= scenario_df["burn"]]
    if not crossover.empty:
        cx = int(crossover.iloc[0]["month"]) - 1
        fig.add_shape(type="line", x0=cx, x1=cx, y0=0, y1=1,
                      xref="x", yref="paper",
                      line=dict(color="#a78bfa", width=1.5, dash="dot"))
        fig.add_annotation(x=cx, y=1, xref="x", yref="paper",
                           text="Rev > Burn", showarrow=False,
                           font=dict(color="#a78bfa", size=10), yanchor="bottom")
    fig.update_layout(**PLOTLY_LAYOUT, title="Revenue vs. Burn", height=270,
                      barmode="group", yaxis_tickprefix="$", yaxis_tickformat=",")
    st.plotly_chart(fig, use_container_width=True)

# ─── Raw Data ────────────────────────────────────────────────────────────────────
with st.expander("🗂️  View underlying data"):
    display_df = scenario_df[["month","revenue","burn","net_burn","cash_on_hand",
                               "runway_months","headcount","funding_event"]].copy()
    display_df.columns = ["Month","Revenue","Burn","Net Burn","Cash on Hand",
                          "Runway (mo)","Headcount","Funding Event"]
    st.dataframe(
        display_df.style.format({
            "Revenue":"${:,.0f}", "Burn":"${:,.0f}", "Net Burn":"${:,.0f}",
            "Cash on Hand":"${:,.0f}", "Funding Event":"${:,.0f}", "Runway (mo)":"{:.1f}",
        }),
        use_container_width=True, hide_index=True,
    )
    st.download_button("⬇️ Download CSV", data=display_df.to_csv(index=False),
                       file_name="startup_simulation.csv", mime="text/csv")