"""pages/pathway_engineer.py"""
import streamlit as st
import plotly.graph_objects as go
from utils.ai_client import analyze_with_claude

EXAMPLE_PATHWAYS = {
    "Lycopene Biosynthesis (E. coli)": {
        "steps": [
            ("IPP/DMAPP", "Geranylgeranyl-PP", "IspA / GGS1"),
            ("Geranylgeranyl-PP", "Phytoene", "CrtB"),
            ("Phytoene", "Lycopene", "CrtI (4 desaturations)"),
        ],
        "target": "Lycopene",
        "organism": "E. coli",
        "bottleneck": "CrtI (rate-limiting desaturation steps)",
    },
    "Violacein Pathway": {
        "steps": [
            ("Tryptophan", "IPA imine", "VioA (oxidase)"),
            ("IPA imine", "Protodeoxyviolaceinic acid", "VioB + VioE"),
            ("Protodeoxyviolaceinic acid", "Violacein", "VioC + VioD"),
        ],
        "target": "Violacein",
        "organism": "Chromobacterium violaceum",
        "bottleneck": "VioB (unstable intermediate)",
    },
    "Resveratrol Biosynthesis": {
        "steps": [
            ("Phenylalanine", "Cinnamic acid", "PAL"),
            ("Cinnamic acid", "4-Coumaroyl-CoA", "C4H + 4CL"),
            ("4-Coumaroyl-CoA + Malonyl-CoA×3", "Resveratrol", "STS"),
        ],
        "target": "Resveratrol",
        "organism": "Vitis vinifera / engineered yeast",
        "bottleneck": "Malonyl-CoA availability",
    },
}


def render():
    st.markdown("""
    <div class="section-title">🔗 Pathway Engineer</div>
    <div class="section-subtitle">Metabolic pathway design · Bottleneck identification · AI flux reasoning</div>
    <div class="section-divider"></div>
    """, unsafe_allow_html=True)

    col_cfg, col_main = st.columns([1, 3])

    with col_cfg:
        st.markdown('<div class="gai-card"><div class="gai-card-header">🧪 Pathway Config</div></div>', unsafe_allow_html=True)
        mode = st.radio("Input Mode", ["Example Pathways", "Custom Pathway"])

        if mode == "Example Pathways":
            chosen = st.selectbox("Select Pathway", list(EXAMPLE_PATHWAYS.keys()))
            pathway = EXAMPLE_PATHWAYS[chosen]
        else:
            pathway = _build_custom_pathway()

        show_flux = st.checkbox("Overlay flux heuristics", value=True)
        ai_analyze = st.button("🤖 AI Pathway Analysis", use_container_width=True)

    with col_main:
        _render_pathway_diagram(pathway, show_flux)

        st.markdown("<br>", unsafe_allow_html=True)
        _render_pathway_table(pathway)

        if ai_analyze:
            steps_desc = "\n".join(f"{s} → {e} (enzyme: {en})" for s, e, en in pathway["steps"])
            prompt = f"""
Analyze this metabolic pathway for synthetic biology engineering:

Pathway: {pathway.get('target', 'Unknown')}
Host organism: {pathway.get('organism', 'Unknown')}
Steps:
{steps_desc}
Known bottleneck: {pathway.get('bottleneck', 'Unknown')}

Provide:
# Executive Summary
# Biological Context
# Engineering Analysis (enzyme optimization, cofactor balance)
# Bottleneck Assessment and Strategies
# Risks & Constraints (toxicity, metabolic burden, competing pathways)
# Suggested Next Computational Steps
"""
            with st.spinner("Analyzing metabolic pathway..."):
                result = analyze_with_claude(prompt)
            st.markdown(f'<div class="ai-response">{result}</div>', unsafe_allow_html=True)


def _render_pathway_diagram(pathway, show_flux):
    steps = pathway["steps"]
    nodes = []
    for s, e, _ in steps:
        if s not in nodes: nodes.append(s)
        if e not in nodes: nodes.append(e)

    n = len(nodes)
    x = [i / max(n - 1, 1) for i in range(n)]
    y = [0.5] * n

    fig = go.Figure()

    # Edges
    for i, (src, dst, enzyme) in enumerate(steps):
        xi, xd = x[nodes.index(src)], x[nodes.index(dst)]
        is_bottleneck = pathway.get("bottleneck", "") and enzyme in pathway.get("bottleneck", "")
        edge_color = "#ff6b35" if is_bottleneck else "#00ffc8"
        fig.add_annotation(
            x=xd, y=0.5, ax=xi, ay=0.5,
            xref="x", yref="y", axref="x", ayref="y",
            showarrow=True,
            arrowhead=3, arrowsize=1.5, arrowwidth=2,
            arrowcolor=edge_color,
        )
        fig.add_trace(go.Scatter(
            x=[(xi + xd) / 2], y=[0.58],
            mode="text",
            text=[enzyme],
            textfont=dict(size=9, color="#7fa3b8", family="Space Mono"),
            showlegend=False, hoverinfo="skip",
        ))

    # Nodes
    for i, node in enumerate(nodes):
        is_target = node == pathway.get("target")
        color = "#00ffc8" if is_target else "#00d4ff"
        size  = 22 if is_target else 16
        fig.add_trace(go.Scatter(
            x=[x[i]], y=[0.5],
            mode="markers+text",
            marker=dict(size=size, color=color, line=dict(color=color, width=2)),
            text=[node],
            textposition="bottom center",
            textfont=dict(size=10, color="#e8f4f8", family="DM Sans"),
            name=node,
            showlegend=False,
        ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(5,8,16,0.8)",
        font=dict(color="#7fa3b8"),
        height=220, margin=dict(l=0, r=0, t=20, b=60),
        xaxis=dict(visible=False, range=[-0.1, 1.1]),
        yaxis=dict(visible=False, range=[0.2, 0.8]),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _render_pathway_table(pathway):
    for src, dst, enzyme in pathway["steps"]:
        is_bn = pathway.get("bottleneck", "") and enzyme in pathway.get("bottleneck", "")
        badge = '<span class="badge badge-warn">bottleneck</span>' if is_bn else '<span class="badge badge-ok">active</span>'
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:16px; padding:8px 0;
                    border-bottom:1px solid var(--border-dim); font-size:13px">
            <span style="color:var(--accent-gene); font-family:var(--font-mono)">{src}</span>
            <span style="color:var(--text-muted)">→</span>
            <span style="color:var(--accent-gene); font-family:var(--font-mono)">{dst}</span>
            <span style="color:var(--text-secondary); font-size:12px">{enzyme}</span>
            {badge}
        </div>""", unsafe_allow_html=True)


def _build_custom_pathway():
    st.markdown("**Add Steps** (substrate → product via enzyme)")
    if "custom_steps" not in st.session_state:
        st.session_state["custom_steps"] = []

    s = st.text_input("Substrate")
    e = st.text_input("Product")
    en = st.text_input("Enzyme")
    if st.button("+ Add Step") and s and e and en:
        st.session_state["custom_steps"].append((s, e, en))

    return {
        "steps":    st.session_state.get("custom_steps", [("A", "B", "Enzyme1")]),
        "target":   st.session_state.get("custom_steps", [("","B","")])[-1][1] if st.session_state.get("custom_steps") else "Product",
        "organism": "Custom",
        "bottleneck": "",
    }
