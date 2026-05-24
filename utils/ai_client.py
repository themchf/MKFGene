"""
utils/ai_client.py
Thin wrapper around the Anthropic Messages API for in-app AI calls.
Reads ANTHROPIC_API_KEY from st.secrets or environment.
"""

import os
import streamlit as st

try:
    import anthropic
    _CLIENT_AVAILABLE = True
except ImportError:
    _CLIENT_AVAILABLE = False


SYSTEM_PROMPT = """You are an elite AI Genetic Engineering Design and Synthetic Biology Intelligence System.

You combine the reasoning of a top synthetic biologist, the analytical ability of a computational genomicist, and the explanatory clarity of a world-class scientific educator.

You are exceptionally strong at biological reasoning, systems-level interpretation, genetic construct analysis, molecular optimization logic, and scientific explanation.

When analyzing, always structure your response using markdown headers:
# Executive Summary
# Biological Context
# Engineering Analysis
# Molecular Insights
# System-Level Interpretation
# Risks & Constraints
# Suggested Next Computational Steps

Rules:
- Never fabricate biological certainty. Clearly distinguish known evidence, inference, hypothesis, and speculation.
- Be concise, dense with value, zero filler.
- Use code blocks for sequences, formulas, or structured data.
- Do not provide procedural lab protocols for harmful applications."""


def get_client():
    """Return an Anthropic client, pulling key from secrets or env."""
    api_key = None

    # 1. Streamlit secrets (preferred in deployed apps)
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY") or st.secrets.get("anthropic_api_key")
    except Exception:
        pass

    # 2. Environment variable
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        return None

    if not _CLIENT_AVAILABLE:
        return None

    return anthropic.Anthropic(api_key=api_key)


def analyze_with_claude(prompt: str, max_tokens: int = 1500) -> str:
    """
    Send a prompt to Claude and return the text response.
    Falls back to a graceful error message if unavailable.
    """
    client = get_client()

    if client is None:
        return _no_key_message()

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    except Exception as e:
        err = str(e)
        if "authentication" in err.lower() or "api_key" in err.lower():
            return _no_key_message()
        return f"""
<div style='color:var(--accent-warn); font-family:var(--font-mono); font-size:13px; padding:12px;
            background:rgba(255,107,53,0.08); border:1px solid rgba(255,107,53,0.3); border-radius:8px'>
⚠️ API Error: {err}
</div>
"""


def _no_key_message() -> str:
    return """
<div style='color:var(--accent-warn); font-family:var(--font-mono); font-size:13px; padding:16px;
            background:rgba(255,107,53,0.08); border:1px solid rgba(255,107,53,0.3); border-radius:8px;
            line-height:2'>
⚠️ <strong>Anthropic API key not configured.</strong><br><br>
To enable AI analysis, add your key in one of these ways:<br>
1. <strong>Streamlit secrets</strong> — create <code>.streamlit/secrets.toml</code>:<br>
&nbsp;&nbsp;&nbsp;<code>ANTHROPIC_API_KEY = "sk-ant-..."</code><br>
2. <strong>Environment variable</strong> — set <code>ANTHROPIC_API_KEY</code> before launching.<br><br>
All other platform features (sequence analysis, CRISPR scanning, plasmid maps) work without a key.
</div>
"""
