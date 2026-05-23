import streamlit as st
import analysis_module as am

# Configure the genomic workspace layout
st.set_page_config(
    page_title="Elite Synthetic Biology Intelligence System",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🧬 AI Genetic Engineering & Synthetic Biology Intelligence System")
st.markdown("---")
st.markdown("### `System: Operational` | Specialized Genomic Reasoning & Computational Design Platform")

# Sidebar Workspace Configuration
st.sidebar.header("📥 Genomic Data Ingest")
st.sidebar.markdown("Upload molecular sequence payloads for analysis.")

uploaded_file = st.sidebar.file_uploader(
    "Choose a file (FASTA, GenBank, or Text)", 
    type=["fasta", "gb", "txt"],
    help="Supports standard genomic and proteomic file structures."
)

if uploaded_file:
    # Safely decode the biological file stream
    sequence_data = uploaded_file.getvalue().decode("utf-8")
    st.sidebar.success("✅ Sequence Payload Ingested Successfully.")
    
    # Main Engine Output Display
    st.header("📋 Genomic Analysis & Reasoning Report")
    
    # Execute backend intelligence module
    with st.spinner("Processing molecular data and evaluating engineering constraints..."):
        report = am.generate_analysis(sequence_data)
        st.markdown(report)
    
    # Visualization Module Hook
    st.markdown("---")
    st.subheader("📊 Recommended Workspace Visualizations")
    st.info("Interactive rendering pipeline initialized. Interactive Plasmid Maps, Sequence Alignment matrices, and Codon Optimization heatmaps can be mounted here.")
    
else:
    st.info("💡 Awaiting genomic sequence data. Upload a file via the sidebar module to initiate system reasoning.")
    st.markdown("""
    #### Supported Workspace Input Types:
    * **FASTA/GenBank Records:** Full genome fragments, plasmids, or open reading frames.
    * **Synthetic Architecture Profiles:** Modular promoter-RBS-CDS construct configurations.
    * **CRISPR Target Coordinates:** High-level guide-RNA target blocks for editing logic verification.
    """)
