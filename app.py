"""
GenAI Platform — AI-Native Genetic Engineering Intelligence System
Main application entry point
"""

import streamlit as st
from pathlib import Path

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GenAI Platform",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject Global CSS ─────────────────────────────────────────────────────────
def load_css():
    css_path = Path(__file__).parent / "assets" / "style.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ── Sidebar Navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <span class="brand-icon">🧬</span>
        <span class="brand-name">GenAI<span class="brand-accent">Platform</span></span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    nav = st.radio(
        "Navigation",
        options=[
            "🏠  Dashboard",
            "🔬  Sequence Analyzer",
            "✂️  CRISPR Designer",
            "🧫  Plasmid Architect",
            "🔗  Pathway Engineer",
            "💬  AI Reasoning Engine",
            "📁  File Import / Export",
            "⚙️  Settings",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown(
        '<p class="sidebar-footer">Powered by Claude · Anthropic</p>',
        unsafe_allow_html=True,
    )

# ── Page Routing ──────────────────────────────────────────────────────────────
page_key = nav.split("  ", 1)[-1].strip()

if page_key == "Dashboard":
    from pages import dashboard; dashboard.render()
elif page_key == "Sequence Analyzer":
    from pages import sequence_analyzer; sequence_analyzer.render()
elif page_key == "CRISPR Designer":
    from pages import crispr_designer; crispr_designer.render()
elif page_key == "Plasmid Architect":
    from pages import plasmid_architect; plasmid_architect.render()
elif page_key == "Pathway Engineer":
    from pages import pathway_engineer; pathway_engineer.render()
elif page_key == "AI Reasoning Engine":
    from pages import ai_reasoning; ai_reasoning.render()
elif page_key == "File Import / Export":
    from pages import file_manager; file_manager.render()
elif page_key == "Settings":
    from pages import settings; settings.render()
