"""
CRISPR Designer — PAM identification, guide RNA scoring, edit strategy reasoning
"""

import streamlit as st
import plotly.graph_objects as go
import re
from utils.crispr_utils import (
    find_pam_sites,
    score_guide_rna,
    PAM_SYSTEMS,
    predict_edit_outcome,
)
from utils.ai_client import analyze_with_claude


def render():
    st.markdown("""
    <div class="section-title">✂️ CRISPR Designer</div>
    <div class="section-subtitle">Guide RNA identification · PAM analysis · Edit strategy reasoning</div>
    <div class="section-divider"></div>
    """, unsafe_allow_html=True)

    # ── Configuration ──────────────────────────────────────────────
    col_cfg, col_input = st.columns([1, 2])

    with col_cfg:
        st.markdown("""
        <div class="gai-card">
            <div class="gai-card-header">⚙️ System Config</div>
        </div>
        """, unsafe_allow_html=True)

        cas_system = st.selectbox(
            "Cas Nuclease",
            options=list(PAM_SYSTEMS.keys()),
            format_func=lambda k: PAM_SYSTEMS[k]["label"],
        )

        info = PAM_SYSTEMS[cas_system]
        st.markdown(f"""
        <div style="background:var(--bg-elevated); border-radius:var(--radius);
                    padding:12px; margin-top:-8px; font-size:12px">
            <div style="color:var(--accent-bio)">PAM: <code>{info['pam']}</code></div>
            <div style="color:var(--text-secondary); margin-top:4px">Guide: {info['guide_len']} nt</div>
            <div style="color:var(--text-muted); margin-top:4px">{info['description']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        edit_type = st.selectbox(
            "Edit Strategy",
            ["Knockout (NHEJ)", "Knock-in (HDR)", "Base Editing (CBE)", "Base Editing (ABE)", "Prime Editing"],
        )

        min_score = st.slider("Min. Guide Score", 0, 100, 40, help="Heuristic on-target scoring threshold")
        show_offtarget = st.checkbox("Show off-target risk flags", value=True)

    with col_input:
        st.markdown("""
        <div class="gai-card">
            <div class="gai-card-header">🧬 Target Sequence</div>
        </div>
        """, unsafe_allow_html=True)

        target_seq = st.text_area(
            "Target DNA",
            placeholder="Paste 100–5000 bp genomic target region...\n\nATGGCTACGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGATCGAT",
            height=140,
            label_visibility="collapsed",
        )

        col_b1, col_b2, _ = st.columns([1, 1, 2])
        with col_b1:
            run_btn = st.button("✂️ Find Guide RNAs", use_container_width=True)
        with col_b2:
            ai_btn = st.button("🤖 AI Strategy", use_container_width=True)

    if not target_seq.strip():
        _show_crispr_primer()
        return

    seq = target_seq.upper().replace(" ", "").replace("\n", "")

    # ── Find PAM Sites ─────────────────────────────────────────────
    if run_btn or "crispr_results" in st.session_state:
        if run_btn:
            guides = find_pam_sites(seq, cas_system)
            scored = [
                {**g, "score": score_guide_rna(g["guide"], cas_system)}
                for g in guides
            ]
            scored = [g for g in scored if g["score"] >= min_score]
            scored.sort(key=lambda x: x["score"], reverse=True)
            st.session_state["crispr_results"] = scored
            st.session_state["crispr_seq"] = seq
            st.session_state["crispr_system"] = cas_system

        scored = st.session_state.get("crispr_results", [])

        # Summary
        st.markdown(f"""
        <div class="gai-card">
            <div style="display:flex; justify-content:space-between; align-items:center">
                <div>
                    <span class="badge badge-ok">{len(scored)} guides found</span>
                    <span class="badge badge-info" style="margin-left:8px">{PAM_SYSTEMS[cas_system]['pam']} PAM</span>
                    <span class="badge badge-info" style="margin-left:8px">{edit_type}</span>
                </div>
                <span style="font-size:12px; color:var(--text-muted)">Score threshold: {min_score}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not scored:
            st.warning(f"No guide RNAs found with score ≥ {min_score} using {PAM_SYSTEMS[cas_system]['pam']} PAM.")
        else:
            _render_guide_table(scored, seq, show_offtarget)
            _render_guide_score_chart(scored)
            _render_cut_site_map(seq, scored[:10])

    # ── AI Strategy ────────────────────────────────────────────────
    if ai_btn:
        guides = st.session_state.get("crispr_results", [])
        top_guides = guides[:5] if guides else []

        prompt = f"""
You are an expert CRISPR scientist. Analyze this CRISPR design scenario:

Cas System: {PAM_SYSTEMS[cas_system]['label']} (PAM: {PAM_SYSTEMS[cas_system]['pam']})
Edit Strategy: {edit_type}
Target sequence (first 300 bp): {seq[:300]}
Top guide candidates: {[g['guide'] for g in top_guides]}
Guide scores: {[g['score'] for g in top_guides]}

Provide:
# Executive Summary
# Biological Context (what is this region likely?)
# Engineering Analysis (best guide selection rationale)
# Edit Outcome Prediction ({edit_type})
# Off-Target Risk Assessment
# Risks & Constraints
# Recommended Next Steps (experimental or computational)

Be scientifically precise. Distinguish established fact from prediction.
        """
        with st.spinner("AI strategy analysis..."):
            result = analyze_with_claude(prompt)

        st.markdown(f'<div class="ai-response">{result}</div>', unsafe_allow_html=True)


def _render_guide_table(guides, seq, show_offtarget):
    st.markdown("### 🎯 Top Guide RNAs")

    for i, g in enumerate(guides[:15]):
        score = g["score"]
        bar_color = "#00ffc8" if score >= 70 else "#ff9f43" if score >= 50 else "#ff6b35"
        ot_flag = ""
        if show_offtarget:
            # Heuristic: low-complexity guides flagged
            gc = (g["guide"].count("G") + g["guide"].count("C")) / len(g["guide"]) * 100
            if gc < 30 or gc > 75:
                ot_flag = '<span class="badge badge-warn" style="margin-left:8px">GC risk</span>'

        strand_badge = "badge-ok" if g.get("strand", "+") == "+" else "badge-mut"

        st.markdown(f"""
        <div style="padding:10px 0; border-bottom:1px solid var(--border-dim);">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px">
                <div>
                    <span style="font-family:var(--font-mono); font-size:13px; color:var(--accent-bio)">#{i+1}</span>
                    <span class="crispr-guide" style="font-family:var(--font-mono); font-size:13px;
                           margin-left:10px; color:var(--accent-gene)">{g['guide']}</span>
                    <span style="font-family:var(--font-mono); color:var(--accent-warn); font-size:13px;
                           margin-left:4px font-weight:700">{g.get('pam_seq','NGG')}</span>
                    {ot_flag}
                </div>
                <div style="display:flex; align-items:center; gap:10px">
                    <span class="badge {strand_badge}">{g.get('strand','+')}</span>
                    <span style="font-size:12px; color:var(--text-muted)">pos {g['position']}</span>
                    <div style="width:80px; height:6px; background:var(--bg-void); border-radius:3px; overflow:hidden">
                        <div style="width:{score}%; height:100%; background:{bar_color}; border-radius:3px"></div>
                    </div>
                    <span style="font-family:var(--font-mono); font-size:12px; color:{bar_color}">{score}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_guide_score_chart(guides):
    if len(guides) < 2:
        return

    guides_show = guides[:20]
    labels = [f"#{i+1} {g['guide'][:12]}..." for i, g in enumerate(guides_show)]
    scores = [g["score"] for g in guides_show]
    colors = ["#00ffc8" if s >= 70 else "#ff9f43" if s >= 50 else "#ff6b35" for s in scores]

    fig = go.Figure(go.Bar(
        x=scores, y=labels,
        orientation="h",
        marker_color=colors,
        marker_opacity=0.85,
        text=[str(s) for s in scores],
        textposition="outside",
    ))
    fig.update_layout(
        title="Guide RNA On-Target Scores",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,8,16,0.8)",
        font=dict(color="#7fa3b8", family="Space Mono", size=9),
        margin=dict(l=0, r=0, t=40, b=0),
        height=max(200, len(guides_show) * 22 + 60),
        xaxis=dict(title="Score (0–100)", range=[0, 110], gridcolor="rgba(0,255,200,0.05)"),
        yaxis=dict(gridcolor="rgba(0,255,200,0.05)", autorange="reversed"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_cut_site_map(seq: str, guides: list):
    st.markdown("### 🗺️ Cut Site Map")

    fig = go.Figure()

    # Target sequence backbone
    fig.add_trace(go.Scatter(
        x=[0, len(seq)], y=[0, 0],
        mode="lines",
        line=dict(color="#3d5a6e", width=4),
        name="Target DNA",
        showlegend=True,
    ))

    for i, g in enumerate(guides):
        pos = g["position"]
        score = g["score"]
        color = "#00ffc8" if score >= 70 else "#ff9f43" if score >= 50 else "#ff6b35"
        y_offset = (i % 4 + 1) * 0.15

        fig.add_trace(go.Scatter(
            x=[pos, pos + len(g["guide"])],
            y=[y_offset, y_offset],
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=5, color=color),
            name=f"Guide #{i+1}",
            hovertemplate=f"Guide #{i+1}<br>Pos: {pos}<br>Score: {score}<extra></extra>",
        ))

        # Cut indicator
        cut_pos = pos + len(g["guide"]) // 2
        fig.add_vline(x=cut_pos, line_dash="dash", line_color=color, opacity=0.3)

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,8,16,0.8)",
        font=dict(color="#7fa3b8", size=10),
        margin=dict(l=0, r=0, t=20, b=0), height=220,
        xaxis=dict(title="Position (bp)", gridcolor="rgba(0,255,200,0.05)", zeroline=False),
        yaxis=dict(visible=False),
        legend=dict(orientation="h", y=1.1, bgcolor="rgba(0,0,0,0)", font_size=9),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _show_crispr_primer():
    st.markdown("""
    <div class="gai-card">
        <div class="gai-card-header">✂️ How CRISPR Design Works</div>
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; margin-top:12px">
            <div style="padding:14px; background:var(--bg-elevated); border-radius:var(--radius);
                        border:1px solid var(--border-dim)">
                <div style="color:var(--accent-bio); font-family:var(--font-display); font-size:15px; margin-bottom:8px">
                    1. PAM Scanning
                </div>
                <div style="font-size:12px; color:var(--text-secondary); line-height:1.7">
                    The system scans both strands of the target for PAM sequences
                    (e.g., NGG for SpCas9). Each PAM defines a potential cut site.
                </div>
            </div>
            <div style="padding:14px; background:var(--bg-elevated); border-radius:var(--radius);
                        border:1px solid var(--border-dim)">
                <div style="color:var(--accent-gene); font-family:var(--font-display); font-size:15px; margin-bottom:8px">
                    2. Guide Extraction
                </div>
                <div style="font-size:12px; color:var(--text-secondary); line-height:1.7">
                    The 20 nt upstream of each PAM becomes the spacer sequence of the guide RNA.
                    GC content, homopolymers, and seed region are evaluated.
                </div>
            </div>
            <div style="padding:14px; background:var(--bg-elevated); border-radius:var(--radius);
                        border:1px solid var(--border-dim)">
                <div style="color:var(--accent-mut); font-family:var(--font-display); font-size:15px; margin-bottom:8px">
                    3. Scoring & Ranking
                </div>
                <div style="font-size:12px; color:var(--text-secondary); line-height:1.7">
                    Guides are scored heuristically on GC content, seed sequence quality,
                    homopolymer runs, and position. Top candidates shown first.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
