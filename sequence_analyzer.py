"""
Sequence Analyzer — Full DNA/RNA/Protein analysis module
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter
import re

from utils.sequence_utils import (
    detect_sequence_type,
    parse_fasta,
    compute_gc_content,
    gc_by_window,
    codon_usage,
    find_orfs,
    find_motifs,
    reverse_complement,
    translate_sequence,
    nucleotide_composition,
    IUPAC_DNA,
)
from utils.ai_client import analyze_with_claude


def render():
    st.markdown("""
    <div class="section-title">🔬 Sequence Analyzer</div>
    <div class="section-subtitle">DNA · RNA · Protein — Multi-layer computational analysis</div>
    <div class="section-divider"></div>
    """, unsafe_allow_html=True)

    # ── Input ──────────────────────────────────────────────────────
    col_input, col_opts = st.columns([3, 1])

    with col_input:
        raw_input = st.text_area(
            "Sequence Input",
            placeholder=">Gene_ID | Optional description\nATGGCTACGATCGATCGATCGATCG...\n\nAccepts: raw sequence, FASTA, multi-FASTA",
            height=160,
            label_visibility="visible",
        )

    with col_opts:
        st.markdown("**Analysis Options**")
        do_gc       = st.checkbox("GC Content Analysis",     value=True)
        do_orf      = st.checkbox("ORF Detection",           value=True)
        do_codon    = st.checkbox("Codon Usage",             value=True)
        do_motif    = st.checkbox("Motif Search",            value=False)
        do_translate = st.checkbox("Translate ORFs",         value=False)
        do_ai       = st.checkbox("AI Deep Analysis",        value=True)

        motif_input = ""
        if do_motif:
            motif_input = st.text_input("Motifs (comma-sep)", placeholder="TATAAA, AATAAA")

    col_btn1, col_btn2, col_btn3, _ = st.columns([1, 1, 1, 3])
    with col_btn1:
        run_btn = st.button("▶ Analyze", use_container_width=True)
    with col_btn2:
        rc_btn = st.button("↔ Rev-Comp", use_container_width=True)
    with col_btn3:
        clear_btn = st.button("✕ Clear", use_container_width=True)

    if clear_btn:
        st.rerun()

    if not raw_input.strip():
        _show_example_panel()
        return

    # ── Parse Input ────────────────────────────────────────────────
    sequences = parse_fasta(raw_input.strip())
    if not sequences:
        st.error("Could not parse input. Ensure valid FASTA or raw sequence.")
        return

    # ── Rev-Comp shortcut ──────────────────────────────────────────
    if rc_btn:
        rc = reverse_complement(list(sequences.values())[0])
        st.markdown(f"""
        <div class="gai-card">
            <div class="gai-card-header">↔ Reverse Complement</div>
            <div class="seq-display">{rc}</div>
        </div>
        """, unsafe_allow_html=True)
        return

    if not run_btn and "seq_results" not in st.session_state:
        st.info("Input detected. Click **▶ Analyze** to run analysis.")
        return

    if run_btn:
        st.session_state["seq_input"] = raw_input
        st.session_state["seq_sequences"] = sequences

    sequences = st.session_state.get("seq_sequences", sequences)

    # ── Multi-sequence selector ────────────────────────────────────
    seq_names = list(sequences.keys())
    selected = seq_names[0]
    if len(seq_names) > 1:
        selected = st.selectbox("Select sequence to analyze", seq_names)

    seq = sequences[selected].upper().replace(" ", "").replace("\n", "")
    seq_type = detect_sequence_type(seq)

    # ── Summary Header ─────────────────────────────────────────────
    st.markdown(f"""
    <div class="gai-card">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px">
            <div>
                <div class="gai-card-header" style="margin-bottom:4px">{selected}</div>
                <div style="font-family:var(--font-mono); font-size:12px; color:var(--text-muted)">
                    {len(seq):,} bp · {seq_type}
                </div>
            </div>
            <div style="display:flex; gap:8px; flex-wrap:wrap">
                <span class="badge badge-info">{seq_type}</span>
                <span class="badge badge-ok">{len(seq):,} bp</span>
                {"<span class='badge badge-ok'>Valid FASTA</span>" if selected != "sequence_1" else ""}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Sequence Preview ───────────────────────────────────────────
    with st.expander("Sequence Preview (colored)", expanded=False):
        colored = _color_sequence(seq[:500])
        suffix = f"... [{len(seq)-500:,} bp more]" if len(seq) > 500 else ""
        st.markdown(
            f'<div class="seq-display">{colored}{suffix}</div>',
            unsafe_allow_html=True,
        )

    # ── Analysis Tabs ──────────────────────────────────────────────
    tabs = st.tabs(["📊 Composition", "🧬 ORF / CDS", "📖 Codon Usage", "🔍 Motifs", "🤖 AI Analysis"])

    # ── Tab 1: Composition ─────────────────────────────────────────
    with tabs[0]:
        if do_gc and seq_type in ("DNA", "RNA"):
            _render_gc_analysis(seq, seq_type)

        _render_nucleotide_bar(seq, seq_type)

    # ── Tab 2: ORF ─────────────────────────────────────────────────
    with tabs[1]:
        if do_orf and seq_type == "DNA":
            _render_orf_analysis(seq, do_translate)
        elif seq_type == "RNA":
            st.info("ORF detection on RNA — converting U→T for analysis.")
            _render_orf_analysis(seq.replace("U", "T"), do_translate)
        else:
            st.info("ORF detection is available for DNA/RNA sequences.")

    # ── Tab 3: Codon Usage ─────────────────────────────────────────
    with tabs[2]:
        if do_codon and seq_type in ("DNA", "RNA"):
            _render_codon_usage(seq)
        else:
            st.info("Codon usage analysis available for DNA/RNA sequences.")

    # ── Tab 4: Motifs ──────────────────────────────────────────────
    with tabs[3]:
        if do_motif and motif_input.strip():
            _render_motif_search(seq, motif_input)
        else:
            st.info("Enable **Motif Search** and enter motifs in the options panel.")

    # ── Tab 5: AI ──────────────────────────────────────────────────
    with tabs[4]:
        if do_ai:
            _render_ai_analysis(seq, selected, seq_type)
        else:
            st.info("Enable **AI Deep Analysis** in the options panel.")


# ──────────────────────────────────────────────────────────────────
# Sub-renderers
# ──────────────────────────────────────────────────────────────────

def _render_gc_analysis(seq: str, seq_type: str):
    gc = compute_gc_content(seq)
    gc_status = "badge-ok" if 40 <= gc <= 65 else "badge-warn"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="metric-tile">
            <div class="metric-val">{gc:.1f}%</div>
            <div class="metric-label">GC Content</div>
            <div style="margin-top:8px"><span class="badge {gc_status}">
                {"Optimal" if 40<=gc<=65 else "Extreme"}</span></div>
        </div>""", unsafe_allow_html=True)

    at = 100 - gc
    with col2:
        st.markdown(f"""
        <div class="metric-tile">
            <div class="metric-val">{at:.1f}%</div>
            <div class="metric-label">AT Content</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        melting = 4 * seq.count("G") + 4 * seq.count("C") + 2 * seq.count("A") + 2 * seq.count("T")
        st.markdown(f"""
        <div class="metric-tile">
            <div class="metric-val">{melting}°C</div>
            <div class="metric-label">Melting Temp (est.)</div>
        </div>""", unsafe_allow_html=True)

    # GC sliding window
    windows, gc_vals = gc_by_window(seq, window=100)
    if windows:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=windows, y=gc_vals,
            fill="tozeroy",
            fillcolor="rgba(0,255,200,0.05)",
            line=dict(color="#00ffc8", width=1.5),
            name="GC %",
        ))
        fig.add_hline(y=50, line_dash="dot", line_color="rgba(255,255,255,0.2)")
        fig.update_layout(
            title="GC Content — Sliding Window (100 bp)",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,8,16,0.8)",
            font=dict(color="#7fa3b8", size=10),
            margin=dict(l=0, r=0, t=40, b=0), height=200,
            xaxis=dict(title="Position", gridcolor="rgba(0,255,200,0.05)", zeroline=False),
            yaxis=dict(title="GC %", range=[0, 100], gridcolor="rgba(0,255,200,0.05)", zeroline=False),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_nucleotide_bar(seq: str, seq_type: str):
    comp = nucleotide_composition(seq, seq_type)
    fig = go.Figure(go.Bar(
        x=list(comp.keys()),
        y=list(comp.values()),
        marker_color=["#ff6b6b", "#4ecdc4", "#45b7d1", "#f9ca24", "#c678ff"][:len(comp)],
        text=[f"{v:.1f}%" for v in comp.values()],
        textposition="outside",
    ))
    fig.update_layout(
        title="Nucleotide / Residue Composition",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,8,16,0.8)",
        font=dict(color="#7fa3b8", size=11),
        margin=dict(l=0, r=0, t=40, b=0), height=240,
        xaxis=dict(gridcolor="rgba(0,255,200,0.05)"),
        yaxis=dict(title="%", gridcolor="rgba(0,255,200,0.05)", zeroline=False),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_orf_analysis(seq: str, do_translate: bool):
    orfs = find_orfs(seq, min_length=100)

    if not orfs:
        st.warning("No ORFs ≥ 100 bp found in given frames.")
        return

    st.markdown(f"**{len(orfs)} ORFs detected** (≥ 100 bp, all 6 reading frames)")

    # ORF map
    fig = go.Figure()
    colors = ["#00ffc8", "#00d4ff", "#c678ff", "#ff9f43", "#ff6b35", "#ff6b6b"]
    for i, orf in enumerate(orfs[:20]):
        frame_label = f"+{orf['frame']}" if orf['frame'] > 0 else str(orf['frame'])
        fig.add_trace(go.Bar(
            x=[orf["end"] - orf["start"]],
            y=[f"Frame {frame_label} | ORF {i+1}"],
            base=[orf["start"]],
            orientation="h",
            marker_color=colors[abs(orf["frame"]) % len(colors)],
            marker_opacity=0.8,
            text=f"{orf['end']-orf['start']} bp",
            textposition="inside",
            name=f"ORF {i+1}",
            showlegend=False,
        ))

    fig.update_layout(
        title="ORF Map",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,8,16,0.8)",
        font=dict(color="#7fa3b8", size=10),
        margin=dict(l=0, r=0, t=40, b=0),
        height=max(180, len(orfs[:20]) * 26 + 60),
        xaxis=dict(title="Position (bp)", gridcolor="rgba(0,255,200,0.05)", zeroline=False),
        yaxis=dict(gridcolor="rgba(0,255,200,0.05)"),
        barmode="overlay",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ORF table
    with st.expander("ORF Details Table"):
        for orf in orfs[:20]:
            frame_label = f"+{orf['frame']}" if orf['frame'] > 0 else str(orf['frame'])
            protein = translate_sequence(orf["sequence"][:99]) if do_translate else "—"
            st.markdown(f"""
            <div style="font-family:var(--font-mono); font-size:12px; padding:6px 0;
                        border-bottom:1px solid var(--border-dim);">
                <span style="color:var(--accent-bio)">Frame {frame_label}</span> ·
                <span style="color:var(--text-secondary)">{orf['start']}–{orf['end']}</span> ·
                <span style="color:var(--text-primary)">{orf['end']-orf['start']} bp</span>
                {"<br><span style='color:var(--accent-mut); font-size:11px'>→ " + protein + "</span>" if do_translate else ""}
            </div>
            """, unsafe_allow_html=True)


def _render_codon_usage(seq: str):
    usage = codon_usage(seq.replace("U", "T"))
    if not usage:
        st.warning("Sequence too short for codon analysis.")
        return

    top_codons = sorted(usage.items(), key=lambda x: x[1], reverse=True)[:20]
    codons, freqs = zip(*top_codons)

    fig = go.Figure(go.Bar(
        x=codons, y=freqs,
        marker_color="#00d4ff",
        marker_opacity=0.8,
        text=[f"{f:.0f}" for f in freqs],
        textposition="outside",
    ))
    fig.update_layout(
        title="Top 20 Codons by Frequency",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,8,16,0.8)",
        font=dict(color="#7fa3b8", family="Space Mono", size=10),
        margin=dict(l=0, r=0, t=40, b=0), height=260,
        xaxis=dict(gridcolor="rgba(0,255,200,0.05)"),
        yaxis=dict(title="Count", gridcolor="rgba(0,255,200,0.05)", zeroline=False),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_motif_search(seq: str, motif_input: str):
    motifs = [m.strip().upper() for m in motif_input.split(",") if m.strip()]
    results = find_motifs(seq, motifs)

    for motif, positions in results.items():
        status = "badge-ok" if positions else "badge-warn"
        st.markdown(f"""
        <div style="padding:12px 0; border-bottom:1px solid var(--border-dim)">
            <span style="font-family:var(--font-mono); color:var(--accent-gene)">{motif}</span>
            <span class="badge {status}" style="margin-left:10px">
                {len(positions)} hit{"s" if len(positions)!=1 else ""}
            </span>
            <span style="font-size:12px; color:var(--text-muted); margin-left:10px">
                {", ".join(str(p) for p in positions[:12])}{"..." if len(positions)>12 else ""}
            </span>
        </div>
        """, unsafe_allow_html=True)


def _render_ai_analysis(seq: str, name: str, seq_type: str):
    cache_key = f"ai_seq_{hash(seq[:200])}"

    if cache_key in st.session_state:
        st.markdown(f'<div class="ai-response">{st.session_state[cache_key]}</div>', unsafe_allow_html=True)
        return

    if st.button("🤖 Run AI Analysis", use_container_width=True):
        prompt = f"""
You are an elite genetic engineering AI. Analyze this {seq_type} sequence:

Name: {name}
Length: {len(seq):,} bp
Sequence (first 800 bp): {seq[:800]}

Provide:
# Executive Summary
# Biological Context
# Engineering Analysis
# Molecular Insights (GC={compute_gc_content(seq):.1f}%, notable features)
# Risks & Constraints
# Suggested Next Computational Steps

Be scientific, precise, and concise.
        """
        with st.spinner("AI analysis running..."):
            result = analyze_with_claude(prompt)
            st.session_state[cache_key] = result

        st.markdown(f'<div class="ai-response">{result}</div>', unsafe_allow_html=True)
    else:
        st.info("Click **Run AI Analysis** to get Claude-powered deep biological interpretation.")


def _color_sequence(seq: str) -> str:
    """Return HTML with per-nucleotide color spans."""
    color_map = {"A": "seq-A", "T": "seq-T", "G": "seq-G", "C": "seq-C", "U": "seq-U"}
    chunks = []
    for i, ch in enumerate(seq):
        cls = color_map.get(ch, "")
        if cls:
            chunks.append(f'<span class="{cls}">{ch}</span>')
        else:
            chunks.append(ch)
        if (i + 1) % 60 == 0:
            chunks.append("\n")
    return "".join(chunks)


def _show_example_panel():
    st.markdown("""
    <div class="gai-card">
        <div class="gai-card-header">🧬 Accepted Formats</div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:12px">
            <div>
                <div style="color:var(--accent-gene); font-family:var(--font-mono); font-size:12px; margin-bottom:6px">FASTA</div>
                <div class="seq-display" style="font-size:11px">&gt;Gene_Name | description\nATGGCTACGATCGATCGA...</div>
            </div>
            <div>
                <div style="color:var(--accent-gene); font-family:var(--font-mono); font-size:12px; margin-bottom:6px">Raw DNA</div>
                <div class="seq-display" style="font-size:11px">ATGGCTACGATCGATCGA...</div>
            </div>
            <div>
                <div style="color:var(--accent-gene); font-family:var(--font-mono); font-size:12px; margin-bottom:6px">RNA</div>
                <div class="seq-display" style="font-size:11px">AUGGCUACGAUCGAUCGA...</div>
            </div>
            <div>
                <div style="color:var(--accent-gene); font-family:var(--font-mono); font-size:12px; margin-bottom:6px">Multi-FASTA</div>
                <div class="seq-display" style="font-size:11px">&gt;Gene_A\nATGGCT...\n&gt;Gene_B\nATCGAT...</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
