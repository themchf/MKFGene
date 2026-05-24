"""pages/ai_reasoning.py"""
import streamlit as st
from utils.ai_client import analyze_with_claude

PROMPT_TEMPLATES = {
    "Deep Sequence Analysis": "Analyze this biological sequence in full detail:\n\n{input}\n\nCover: sequence type, structural features, biological role hypotheses, engineering potential, and key risks.",
    "CRISPR Strategy Advisory": "Design an optimal CRISPR strategy for this target:\n\n{input}\n\nCover: system selection rationale, guide RNA considerations, edit outcome prediction, delivery strategy concepts, and off-target risk.",
    "Synthetic Biology Design": "I want to engineer this biological system:\n\n{input}\n\nCover: construct architecture, regulatory element choices, expression system, chassis organism considerations, and potential failure modes.",
    "Pathway Optimization": "Analyze and suggest optimizations for this metabolic pathway:\n\n{input}\n\nCover: rate-limiting steps, cofactor requirements, competing reactions, overexpression/knockdown targets, and expected yield improvement.",
    "Mutation Impact Assessment": "Assess the functional impact of these mutations:\n\n{input}\n\nCover: structural domain context, likely functional consequence, gain/loss-of-function assessment, clinical or engineering significance.",
    "Literature-Style Summary": "Summarize the biological significance of:\n\n{input}\n\nWrite as a concise scientific abstract with background, findings, and implications.",
    "Free Form Query": "{input}",
}


def render():
    st.markdown("""
    <div class="section-title">💬 AI Reasoning Engine</div>
    <div class="section-subtitle">Claude-powered deep biological analysis · Full context reasoning</div>
    <div class="section-divider"></div>
    """, unsafe_allow_html=True)

    col_cfg, col_chat = st.columns([1, 3])

    with col_cfg:
        st.markdown('<div class="gai-card"><div class="gai-card-header">⚙️ Mode</div></div>', unsafe_allow_html=True)
        template_key = st.selectbox("Analysis Template", list(PROMPT_TEMPLATES.keys()))
        max_tokens = st.slider("Response depth (tokens)", 500, 3000, 1500, 250)
        clear_btn = st.button("🗑 Clear History", use_container_width=True)
        if clear_btn:
            st.session_state["ai_history"] = []
            st.rerun()

        st.markdown("""
        <div style="font-size:11px; color:var(--text-muted); line-height:1.8; margin-top:16px">
            <strong style="color:var(--text-secondary)">Tips</strong><br>
            • Paste sequences directly<br>
            • Include gene names or pathway context<br>
            • Ask follow-up questions — history is maintained<br>
            • Use templates to structure output
        </div>""", unsafe_allow_html=True)

    with col_chat:
        if "ai_history" not in st.session_state:
            st.session_state["ai_history"] = []

        # Render history
        for msg in st.session_state["ai_history"]:
            if msg["role"] == "user":
                st.markdown(f"""
                <div style="background:var(--bg-elevated); border-radius:var(--radius);
                            padding:12px 16px; margin:8px 0; border-left:3px solid var(--accent-gene)">
                    <span style="font-size:11px; color:var(--text-muted); font-family:var(--font-mono)">YOU</span>
                    <div style="margin-top:6px; font-size:13px">{msg["content"]}</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="ai-response">{msg["content"]}</div>', unsafe_allow_html=True)

        # Input
        user_input = st.text_area(
            "Your query",
            placeholder="Paste a sequence, describe a construct, ask a biological question...",
            height=120,
            label_visibility="collapsed",
            key="ai_input",
        )

        col_send, col_template_badge, _ = st.columns([1, 2, 2])
        with col_send:
            send = st.button("▶ Send", use_container_width=True)
        with col_template_badge:
            st.markdown(f'<span class="badge badge-info">{template_key}</span>', unsafe_allow_html=True)

        if send and user_input.strip():
            template = PROMPT_TEMPLATES[template_key]
            prompt = template.replace("{input}", user_input.strip())

            st.session_state["ai_history"].append({"role": "user", "content": user_input.strip()})

            with st.spinner("Reasoning..."):
                response = analyze_with_claude(prompt, max_tokens=max_tokens)

            st.session_state["ai_history"].append({"role": "assistant", "content": response})
            st.rerun()
