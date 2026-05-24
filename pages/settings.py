"""pages/settings.py"""
import streamlit as st


def render():
    st.markdown("""
    <div class="section-title">⚙️ Settings</div>
    <div class="section-subtitle">API keys · Display preferences · Session management</div>
    <div class="section-divider"></div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="gai-card"><div class="gai-card-header">🔑 API Configuration</div></div>', unsafe_allow_html=True)
        st.info("API key is read from `.streamlit/secrets.toml` or the `ANTHROPIC_API_KEY` environment variable. Do not paste keys directly into the UI.")

        st.code("""# .streamlit/secrets.toml
ANTHROPIC_API_KEY = "sk-ant-..."
""", language="toml")

        st.code("""# Or set environment variable:
export ANTHROPIC_API_KEY="sk-ant-..."
streamlit run app.py
""", language="bash")

        from utils.ai_client import get_client
        client = get_client()
        if client:
            st.markdown('<span class="badge badge-ok">✓ API Key Detected</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="badge badge-warn">⚠ No API Key Found</span>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="gai-card"><div class="gai-card-header">🎛 Analysis Defaults</div></div>', unsafe_allow_html=True)

        st.number_input("Default ORF min length (bp)", value=100, min_value=30, max_value=1000, key="default_orf_min")
        st.number_input("GC window size (bp)",          value=100, min_value=20, max_value=500,  key="default_gc_window")
        st.slider("CRISPR min guide score",              0, 100, 40, key="default_guide_score")
        st.selectbox("Default Cas system", ["SpCas9","SaCas9","Cas12a","SpRY"], key="default_cas")

    st.markdown("---")
    st.markdown('<div class="gai-card"><div class="gai-card-header">🗑 Session Management</div></div>', unsafe_allow_html=True)
    col_a, col_b, _ = st.columns([1, 1, 2])
    with col_a:
        if st.button("Clear All Session Data", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("Session cleared.")
            st.rerun()
    with col_b:
        keys = list(st.session_state.keys())
        st.markdown(f'<span class="badge badge-info">{len(keys)} session keys</span>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; padding:20px; color:var(--text-muted); font-family:var(--font-mono); font-size:11px">
        GenAI Platform v1.0 · Built with Streamlit · Powered by Claude (Anthropic)<br>
        For research and educational purposes.
    </div>
    """, unsafe_allow_html=True)
