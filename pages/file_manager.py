"""pages/file_manager.py"""
import streamlit as st
import re
from utils.sequence_utils import parse_fasta, detect_sequence_type, compute_gc_content, find_orfs


def render():
    st.markdown("""
    <div class="section-title">📁 File Import / Export</div>
    <div class="section-subtitle">FASTA · GenBank · CSV — upload, inspect, and export analysis results</div>
    <div class="section-divider"></div>
    """, unsafe_allow_html=True)

    tab_import, tab_export = st.tabs(["📥 Import", "📤 Export"])

    with tab_import:
        uploaded = st.file_uploader(
            "Upload biological file",
            type=["fasta", "fa", "fna", "ffn", "frn", "txt", "gb", "gbk", "csv", "tsv"],
            accept_multiple_files=True,
        )

        if uploaded:
            for f in uploaded:
                raw = f.read().decode("utf-8", errors="replace")
                ext = f.name.rsplit(".", 1)[-1].lower()

                st.markdown(f"""
                <div class="gai-card">
                    <div style="display:flex; justify-content:space-between; align-items:center">
                        <div class="gai-card-header">📄 {f.name}</div>
                        <span class="badge badge-info">{ext.upper()}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if ext in ("fasta", "fa", "fna", "ffn", "frn", "txt"):
                    seqs = parse_fasta(raw)
                    st.success(f"{len(seqs)} sequence(s) parsed")

                    for name, seq in list(seqs.items())[:5]:
                        seq_type = detect_sequence_type(seq)
                        gc = compute_gc_content(seq) if seq_type in ("DNA","RNA") else None
                        orfs = find_orfs(seq) if seq_type == "DNA" else []
                        st.markdown(f"""
                        <div style="padding:8px 0; border-bottom:1px solid var(--border-dim); font-size:13px">
                            <span style="color:var(--accent-bio); font-family:var(--font-mono)">{name}</span>
                            <span class="badge badge-info" style="margin-left:8px">{seq_type}</span>
                            <span style="color:var(--text-muted); margin-left:8px">{len(seq):,} bp</span>
                            {"<span style='color:var(--text-secondary); margin-left:8px'>GC: " + f"{gc:.1f}%" + "</span>" if gc is not None else ""}
                            {"<span style='color:var(--text-secondary); margin-left:8px'>ORFs: " + str(len(orfs)) + "</span>" if orfs else ""}
                        </div>
                        """, unsafe_allow_html=True)

                    if len(seqs) > 5:
                        st.info(f"Showing first 5 of {len(seqs)} sequences.")

                    # Store in session
                    if st.button(f"Load into Sequence Analyzer — {f.name}"):
                        st.session_state["imported_seqs"] = seqs
                        st.success("Sequences loaded. Navigate to Sequence Analyzer.")

                elif ext in ("gb", "gbk"):
                    st.info("GenBank parsing: feature annotations extracted (basic).")
                    lines = raw.splitlines()
                    features = [l.strip() for l in lines if l.strip().startswith(("gene","CDS","promoter","rep_origin"))]
                    st.code("\n".join(features[:30]), language=None)

                elif ext in ("csv", "tsv"):
                    sep = "\t" if ext == "tsv" else ","
                    rows = [l.split(sep) for l in raw.splitlines() if l.strip()]
                    if rows:
                        import pandas as pd
                        df = pd.DataFrame(rows[1:], columns=rows[0])
                        st.dataframe(df.head(20), use_container_width=True)

                else:
                    st.text_area("Raw content (first 2000 chars)", raw[:2000], height=200)

        else:
            st.markdown("""
            <div class="gai-card" style="text-align:center; padding:40px">
                <div style="font-size:40px">📂</div>
                <div style="font-family:var(--font-display); font-size:18px; color:var(--text-secondary); margin-top:12px">
                    Drop files here or click Browse
                </div>
                <div style="font-size:13px; color:var(--text-muted); margin-top:8px">
                    FASTA · GenBank (.gb/.gbk) · CSV/TSV · Plain text
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab_export:
        st.markdown('<div class="gai-card"><div class="gai-card-header">📤 Export Session Data</div></div>', unsafe_allow_html=True)

        seqs = st.session_state.get("seq_sequences", {})
        if seqs:
            fasta_out = "\n".join(f">{name}\n{seq}" for name, seq in seqs.items())
            st.download_button(
                "⬇ Download FASTA",
                fasta_out,
                file_name="genai_export.fasta",
                mime="text/plain",
                use_container_width=True,
            )
        else:
            st.info("Run a sequence analysis first to enable export.")

        log = st.session_state.get("analysis_log", [])
        if log:
            log_text = "\n".join(f"[{e.get('type','')}] {e['action']} — {e['detail']}" for e in log)
            st.download_button(
                "⬇ Download Analysis Log",
                log_text,
                file_name="genai_log.txt",
                mime="text/plain",
                use_container_width=True,
            )
