"""
Dashboard — Overview / landing page for GenAI Platform
"""

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import random


def render():
    st.markdown("""
    <div class="section-title">🧬 GenAI Platform</div>
    <div class="section-subtitle">AI-Native Genetic Engineering Intelligence System · Ready for Analysis</div>
    <div class="section-divider"></div>
    """, unsafe_allow_html=True)

    # ── Top Metrics ────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    metrics = [
        ("Supported Sequence Types", "12", "DNA · RNA · Protein · Plasmid"),
        ("AI Reasoning Engine", "Active", "Claude Sonnet 4"),
        ("Analysis Modules", "7", "CRISPR · Pathway · Plasmid · More"),
        ("Viz Frameworks", "5", "Plotly · Matplotlib · Biopython · Custom"),
    ]

    for col, (label, val, sub) in zip([col1, col2, col3, col4], metrics):
        with col:
            st.markdown(f"""
            <div class="metric-tile">
                <div class="metric-val">{val}</div>
                <div class="metric-label">{label}</div>
                <div style="font-size:10px; color:var(--text-muted); margin-top:6px">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Quick Start Cards ──────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("""
        <div class="gai-card">
            <div class="gai-card-header">⚡ Quick Analysis</div>
            <p style="color:var(--text-secondary); font-size:13px; margin-bottom:16px">
                Paste any sequence below for instant AI-powered analysis. Supports FASTA, raw DNA, RNA, protein.
            </p>
        </div>
        """, unsafe_allow_html=True)

        quick_seq = st.text_area(
            "Quick Sequence Input",
            placeholder=">Example_Gene\nATGGCTACGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGAT...",
            height=100,
            label_visibility="collapsed",
        )

        if st.button("⚡ Analyze Now", use_container_width=True):
            if quick_seq.strip():
                with st.spinner("Running rapid analysis..."):
                    from utils.sequence_utils import quick_analyze
                    result = quick_analyze(quick_seq.strip())
                    st.markdown(f'<div class="ai-response">{result}</div>', unsafe_allow_html=True)
            else:
                st.warning("Paste a sequence to analyze.")

    with col_b:
        st.markdown("""
        <div class="gai-card">
            <div class="gai-card-header">🗺️ Platform Capabilities</div>
        </div>
        """, unsafe_allow_html=True)

        capabilities = [
            ("🔬", "Sequence Analyzer", "GC content, ORF detection, codon usage, motif search"),
            ("✂️", "CRISPR Designer", "PAM identification, guide RNA scoring, off-target logic"),
            ("🧫", "Plasmid Architect", "Circular map rendering, element annotation, cloning design"),
            ("🔗", "Pathway Engineer", "Metabolic pathway reasoning, bottleneck identification"),
            ("💬", "AI Reasoning Engine", "Full Claude-powered deep biological analysis"),
        ]

        for icon, name, desc in capabilities:
            st.markdown(f"""
            <div style="display:flex; align-items:flex-start; gap:12px; padding:10px 0;
                        border-bottom:1px solid var(--border-dim);">
                <span style="font-size:20px">{icon}</span>
                <div>
                    <div style="font-family:var(--font-display); font-weight:600;
                                color:var(--accent-bio); font-size:14px">{name}</div>
                    <div style="font-size:12px; color:var(--text-secondary)">{desc}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Signal / Activity Chart ────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="gai-card-header" style="padding:0 0 12px 0">📊 Synthetic Activity Monitor</div>', unsafe_allow_html=True)

    # Fake bioluminescent signal chart
    np.random.seed(42)
    x = np.linspace(0, 100, 300)
    signal_a = 0.6 * np.sin(x * 0.15) + 0.4 * np.sin(x * 0.4 + 1) + np.random.normal(0, 0.05, 300) + 1
    signal_b = 0.4 * np.sin(x * 0.22 + 0.5) + 0.3 * np.cos(x * 0.3) + np.random.normal(0, 0.04, 300) + 0.6
    signal_c = 0.3 * np.sin(x * 0.1 + 2) + 0.2 * np.sin(x * 0.5) + np.random.normal(0, 0.03, 300) + 0.3

    fig = go.Figure()

    for signal, name, color in [
        (signal_a, "Gene A Expression", "#00ffc8"),
        (signal_b, "Gene B Expression", "#00d4ff"),
        (signal_c, "Gene C Expression", "#c678ff"),
    ]:
        fig.add_trace(go.Scatter(
            x=x, y=signal, name=name,
            line=dict(color=color, width=1.5),
            fill="tozeroy",
            fillcolor=color.replace(")", ", 0.05)").replace("rgb", "rgba") if "rgb" in color else color + "0D",
        ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(5,8,16,0.8)",
        font=dict(color="#7fa3b8", family="Space Mono", size=10),
        legend=dict(orientation="h", y=1.1, bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=0, r=0, t=10, b=0),
        height=220,
        xaxis=dict(
            showgrid=True, gridcolor="rgba(0,255,200,0.05)",
            zeroline=False, title="Timepoint", color="#3d5a6e",
        ),
        yaxis=dict(
            showgrid=True, gridcolor="rgba(0,255,200,0.05)",
            zeroline=False, title="Expression Level", color="#3d5a6e",
        ),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Recent Analysis Log ────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    col_log, col_tips = st.columns([2, 1])

    with col_log:
        st.markdown("""
        <div class="gai-card">
            <div class="gai-card-header">📋 Session Log</div>
        </div>
        """, unsafe_allow_html=True)

        log_entries = st.session_state.get("analysis_log", [
            {"action": "Platform initialized", "type": "system",  "detail": "All modules loaded"},
            {"action": "AI Engine connected", "type": "ai",     "detail": "Claude Sonnet 4 ready"},
        ])

        for entry in reversed(log_entries[-8:]):
            badge_class = {
                "system": "badge-info", "ai": "badge-ok",
                "warn": "badge-warn", "mutation": "badge-mut",
            }.get(entry.get("type", "info"), "badge-info")

            st.markdown(f"""
            <div style="display:flex; align-items:center; justify-content:space-between;
                        padding:8px 0; border-bottom:1px solid var(--border-dim); font-size:13px;">
                <span style="color:var(--text-primary)">{entry['action']}</span>
                <div style="display:flex; gap:8px; align-items:center">
                    <span style="color:var(--text-muted); font-size:11px">{entry['detail']}</span>
                    <span class="badge {badge_class}">{entry['type']}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_tips:
        st.markdown("""
        <div class="gai-card">
            <div class="gai-card-header">💡 Tips</div>
            <div style="font-size:13px; color:var(--text-secondary); line-height:1.8">
                <p>🔹 Use FASTA headers (&gt;ID) for accurate gene labeling</p>
                <p>🔹 CRISPR module supports SpCas9, SaCas9, Cas12a PAMs</p>
                <p>🔹 AI Reasoning Engine processes multi-sequence context</p>
                <p>🔹 All analyses are session-scoped — export before closing</p>
                <p>🔹 Upload GenBank (.gb) files for full annotation parsing</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
