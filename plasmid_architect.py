"""
Plasmid Architect — Circular plasmid map rendering and construct design
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import math
from utils.ai_client import analyze_with_claude


# ── Default plasmid feature library ──────────────────────────────
DEFAULT_FEATURES = [
    {"name": "Origin of Replication (pUC ori)", "start": 0,    "end": 650,  "type": "ori",        "color": "#45b7d1"},
    {"name": "Ampicillin Resistance (AmpR)",     "start": 800,  "end": 1660, "type": "resistance", "color": "#ff6b35"},
    {"name": "AmpR Promoter",                    "start": 760,  "end": 800,  "type": "promoter",   "color": "#c678ff"},
    {"name": "T7 Promoter",                      "start": 1700, "end": 1720, "type": "promoter",   "color": "#c678ff"},
    {"name": "MCS (Multiple Cloning Site)",      "start": 1720, "end": 1820, "type": "mcs",        "color": "#f9ca24"},
    {"name": "lacZ-alpha",                       "start": 1820, "end": 2080, "type": "gene",       "color": "#00ffc8"},
    {"name": "lac Operator",                     "start": 1680, "end": 1720, "type": "regulatory", "color": "#ff9f43"},
    {"name": "T7 Terminator",                    "start": 2100, "end": 2140, "type": "terminator", "color": "#ff6b6b"},
]

FEATURE_COLORS = {
    "gene":       "#00ffc8",
    "promoter":   "#c678ff",
    "terminator": "#ff6b6b",
    "ori":        "#45b7d1",
    "resistance": "#ff6b35",
    "mcs":        "#f9ca24",
    "regulatory": "#ff9f43",
    "insert":     "#00d4ff",
    "tag":        "#98c379",
    "other":      "#7fa3b8",
}


def render():
    st.markdown("""
    <div class="section-title">🧫 Plasmid Architect</div>
    <div class="section-subtitle">Circular map rendering · Feature annotation · Construct design</div>
    <div class="section-divider"></div>
    """, unsafe_allow_html=True)

    # ── Sidebar-style config ───────────────────────────────────────
    col_map, col_panel = st.columns([3, 2])

    with col_panel:
        st.markdown("""
        <div class="gai-card">
            <div class="gai-card-header">🔧 Plasmid Configuration</div>
        </div>
        """, unsafe_allow_html=True)

        plasmid_name = st.text_input("Plasmid Name", value="pGenAI-001")
        total_size   = st.number_input("Total Size (bp)", value=2686, min_value=500, max_value=50000, step=100)
        backbone     = st.selectbox("Backbone Template", [
            "pUC19 (2686 bp)", "pBR322 (4361 bp)", "pET-28a (5369 bp)",
            "pCDNA3.1 (5428 bp)", "pAAV-MCS (4733 bp)", "Custom",
        ])

        st.markdown("---")
        st.markdown("**Feature Editor**")

        # Session-state features
        if "plasmid_features" not in st.session_state:
            st.session_state["plasmid_features"] = DEFAULT_FEATURES.copy()

        features = st.session_state["plasmid_features"]

        with st.expander("➕ Add Feature"):
            fn   = st.text_input("Feature Name")
            fst  = st.number_input("Start (bp)", 0, total_size, 0)
            fen  = st.number_input("End (bp)", 0, total_size, 100)
            ftyp = st.selectbox("Type", list(FEATURE_COLORS.keys()))
            if st.button("Add Feature"):
                if fn and fen > fst:
                    features.append({
                        "name": fn, "start": fst, "end": fen,
                        "type": ftyp, "color": FEATURE_COLORS[ftyp],
                    })
                    st.session_state["plasmid_features"] = features
                    st.success(f"Added: {fn}")
                else:
                    st.error("Valid name and start < end required.")

        with st.expander(f"📋 Feature List ({len(features)})"):
            for i, feat in enumerate(features):
                col_n, col_del = st.columns([4, 1])
                with col_n:
                    st.markdown(f"""
                    <div style="font-size:12px; padding:4px 0">
                        <span style="color:{feat['color']}">■</span>
                        <span style="color:var(--text-primary); margin-left:6px">{feat['name']}</span>
                        <span style="color:var(--text-muted); margin-left:6px">
                            {feat['start']}–{feat['end']} bp
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
                with col_del:
                    if st.button("✕", key=f"del_{i}"):
                        features.pop(i)
                        st.session_state["plasmid_features"] = features
                        st.rerun()

        if st.button("🔄 Reset to pUC19", use_container_width=True):
            st.session_state["plasmid_features"] = DEFAULT_FEATURES.copy()
            st.rerun()

    # ── Circular Map ───────────────────────────────────────────────
    with col_map:
        fig = _build_circular_map(plasmid_name, total_size, features)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # AI Analysis
        if st.button("🤖 AI Construct Analysis", use_container_width=True):
            feat_desc = "\n".join(
                f"- {f['name']} ({f['type']}, {f['start']}–{f['end']} bp)"
                for f in features
            )
            prompt = f"""
You are an expert synthetic biologist. Analyze this plasmid construct:

Plasmid: {plasmid_name}
Backbone: {backbone}
Total size: {total_size} bp
Features:
{feat_desc}

Provide:
# Executive Summary
# Biological Context (vector class, intended use)
# Engineering Analysis (element arrangement, regulatory logic)
# Cloning Strategy Recommendations
# Expression System Assessment
# Risks & Constraints (size, selection, insert compatibility)
# Suggested Next Steps

Be technically precise.
            """
            with st.spinner("Analyzing construct..."):
                result = analyze_with_claude(prompt)
            st.markdown(f'<div class="ai-response">{result}</div>', unsafe_allow_html=True)


def _build_circular_map(name: str, size: int, features: list) -> go.Figure:
    """Build a Plotly circular plasmid map."""
    fig = go.Figure()

    R = 1.0       # outer radius
    r = 0.72      # inner radius
    r_tick = 1.12  # tick radius
    r_label = 1.22 # label radius

    # ── Backbone circle ─────────────────────────────────────────
    theta = np.linspace(0, 2 * np.pi, 360)
    for radius, color, width in [(R, "#1e2d45", 18), (R, "#3d5a6e", 2)]:
        fig.add_trace(go.Scatterpolar(
            r=[radius] * 360,
            theta=np.degrees(theta),
            mode="lines",
            line=dict(color=color, width=width),
            showlegend=False,
            hoverinfo="skip",
        ))

    # ── Features ─────────────────────────────────────────────────
    for feat in features:
        start_angle = (feat["start"] / size) * 360
        end_angle   = (feat["end"]   / size) * 360

        if end_angle <= start_angle:
            end_angle += 360

        angles = np.linspace(np.radians(start_angle), np.radians(end_angle), max(3, int((end_angle - start_angle) * 2)))

        # Outer arc
        xs = [R * np.cos(a) for a in angles]
        ys = [R * np.sin(a) for a in angles]
        # Inner arc (reversed)
        xi = [r * np.cos(a) for a in reversed(angles)]
        yi = [r * np.sin(a) for a in reversed(angles)]

        x_poly = xs + xi + [xs[0]]
        y_poly = ys + yi + [ys[0]]

        # Convert to polar
        r_poly     = [math.hypot(x, y) for x, y in zip(x_poly, y_poly)]
        theta_poly = [math.degrees(math.atan2(y, x)) for x, y in zip(x_poly, y_poly)]

        mid_angle = np.radians((start_angle + end_angle) / 2)
        hover_text = (
            f"<b>{feat['name']}</b><br>"
            f"Type: {feat['type']}<br>"
            f"Position: {feat['start']}–{feat['end']} bp<br>"
            f"Length: {feat['end']-feat['start']} bp"
        )

        fig.add_trace(go.Scatterpolar(
            r=r_poly,
            theta=theta_poly,
            fill="toself",
            fillcolor=feat["color"] + "99",
            line=dict(color=feat["color"], width=1.5),
            name=feat["name"],
            hovertemplate=hover_text + "<extra></extra>",
            mode="lines",
        ))

        # Arrow indicator at midpoint
        arr_r = (R + r) / 2
        fig.add_trace(go.Scatterpolar(
            r=[arr_r],
            theta=[np.degrees(mid_angle)],
            mode="markers",
            marker=dict(symbol="triangle-right", size=8, color=feat["color"]),
            showlegend=False,
            hoverinfo="skip",
        ))

    # ── Tick marks ────────────────────────────────────────────────
    tick_interval = _nice_tick_interval(size)
    for bp in range(0, size, tick_interval):
        angle = np.radians(bp / size * 360)
        is_major = bp % (tick_interval * 5) == 0

        r_inner = r_tick if is_major else 1.04
        r_outer = 1.16 if is_major else 1.08

        fig.add_trace(go.Scatterpolar(
            r=[r_inner, r_outer],
            theta=[np.degrees(angle), np.degrees(angle)],
            mode="lines",
            line=dict(color="#3d5a6e" if not is_major else "#7fa3b8", width=1),
            showlegend=False,
            hoverinfo="skip",
        ))

        if is_major and bp > 0:
            fig.add_trace(go.Scatterpolar(
                r=[r_label],
                theta=[np.degrees(angle)],
                mode="text",
                text=[f"{bp//1000}k" if bp >= 1000 else str(bp)],
                textfont=dict(size=9, color="#7fa3b8", family="Space Mono"),
                showlegend=False,
                hoverinfo="skip",
            ))

    # ── Center label ──────────────────────────────────────────────
    fig.add_annotation(
        text=f"<b>{name}</b><br><span style='font-size:10px'>{size:,} bp</span>",
        x=0.5, y=0.5,
        xref="paper", yref="paper",
        showarrow=False,
        font=dict(family="Rajdhani", size=14, color="#e8f4f8"),
        align="center",
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        polar=dict(
            bgcolor="rgba(5,8,16,0.9)",
            radialaxis=dict(visible=False, range=[0, 1.35]),
            angularaxis=dict(
                visible=False,
                rotation=90,
                direction="clockwise",
            ),
        ),
        showlegend=True,
        legend=dict(
            font=dict(size=9, color="#7fa3b8", family="DM Sans"),
            bgcolor="rgba(10,15,30,0.8)",
            bordercolor="rgba(0,255,200,0.2)",
            borderwidth=1,
            x=1.02, y=1,
        ),
        margin=dict(l=0, r=160, t=20, b=20),
        height=520,
    )

    return fig


def _nice_tick_interval(size: int) -> int:
    """Return a clean tick interval for a given plasmid size."""
    if size <= 2000:   return 100
    if size <= 5000:   return 250
    if size <= 10000:  return 500
    if size <= 20000:  return 1000
    return 2000
