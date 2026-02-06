"""
Audit page for running fact-checking
"""

import streamlit as st
from datetime import datetime

from src.layers.ui_integration import UIIntegrationLayer, AuditRequest, get_integration_layer
from src.config.constants import Domain
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def render_audit_page():
    """Render the audit page"""
    st.markdown("## 📝 New Audit")
    st.markdown("Upload source documents and paste LLM output to verify.")
    
    # Two-column layout
    col1, col2 = st.columns(2)
    
    with col1:
        render_source_upload()
    
    with col2:
        render_llm_input()
    
    st.markdown("---")
    
    # Audit controls
    render_audit_controls()


def render_source_upload():
    """Render source document upload section"""
    st.markdown("### 📚 Source Documents")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Upload trusted source documents",
        accept_multiple_files=True,
        type=["txt", "pdf", "docx", "html"],
        help="Upload documents that contain ground truth information"
    )
    
    if uploaded_files:
        st.session_state.sources = []
        for file in uploaded_files:
            content = file.read()
            st.session_state.sources.append({
                "name": file.name,
                "content": content,
                "type": file.name.split(".")[-1] if "." in file.name else "txt"
            })
        
        st.success(f"✅ {len(uploaded_files)} file(s) uploaded")
        
        with st.expander("View uploaded files"):
            for source in st.session_state.sources:
                st.markdown(f"**{source['name']}** ({source['type']})")
    
    # Or paste text directly
    st.markdown("**Or paste source text directly:**")
    
    source_text = st.text_area(
        "Source text",
        height=200,
        placeholder="Paste your source document text here...",
        label_visibility="collapsed"
    )
    
    if source_text:
        if not st.session_state.get("sources"):
            st.session_state.sources = []
        
        # Check if already added
        existing_names = [s["name"] for s in st.session_state.sources]
        if "pasted_source.txt" not in existing_names:
            st.session_state.sources.append({
                "name": "pasted_source.txt",
                "content": source_text,
                "type": "txt"
            })


def render_llm_input():
    """Render LLM output input section"""
    st.markdown("### 🤖 LLM Output")
    
    llm_output = st.text_area(
        "LLM output to verify",
        height=300,
        placeholder="Paste the LLM-generated text you want to verify here...",
        value=st.session_state.get("llm_output", ""),
        label_visibility="collapsed"
    )
    
    st.session_state.llm_output = llm_output
    
    if llm_output:
        word_count = len(llm_output.split())
        char_count = len(llm_output)
        st.caption(f"📊 {word_count} words, {char_count} characters")
    
    # Sample output button
    if st.button("📋 Load Sample", help="Load a sample LLM output for testing"):
        st.session_state.llm_output = """The Eiffel Tower is located in London, England. It was built in 1887 and stands at 324 meters tall. The tower was designed by Gustave Eiffel and has become a symbol of French culture. It receives approximately 7 million visitors each year."""
        st.rerun()


def render_audit_controls():
    """Render audit control buttons and options"""
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        domain = st.selectbox(
            "Domain",
            options=[d.value for d in Domain],
            index=0,
            help="Select the domain for specialized verification"
        )
        st.session_state.domain = domain
    
    with col2:
        run_drift = st.checkbox(
            "Drift Check",
            value=False,
            help="Analyze output stability across regenerations"
        )
    
    with col3:
        gen_corrections = st.checkbox(
            "Generate Corrections",
            value=True,
            help="Generate corrected versions of hallucinated claims"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Validation
    sources = st.session_state.get("sources", [])
    llm_output = st.session_state.get("llm_output", "")
    
    can_run = len(sources) > 0 and len(llm_output) >= 10
    
    if not sources:
        st.warning("⚠️ Please upload at least one source document")
    elif not llm_output or len(llm_output) < 10:
        st.warning("⚠️ Please enter LLM output to verify (minimum 10 characters)")
    
    # Run button
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button(
            "🔍 Run Audit",
            use_container_width=True,
            type="primary",
            disabled=not can_run
        ):
            run_audit(domain, run_drift, gen_corrections)


def run_audit(domain: str, run_drift: bool, gen_corrections: bool):
    """Execute the audit"""
    sources = st.session_state.get("sources", [])
    llm_output = st.session_state.get("llm_output", "")
    
    try:
        domain_enum = Domain(domain.lower())
    except ValueError:
        domain_enum = Domain.GENERAL
    
    # Progress container
    progress_container = st.container()
    
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(progress):
            progress_bar.progress(progress.progress)
            status_text.markdown(f"**{progress.stage.title()}:** {progress.message}")
        
        try:
            # Get integration layer
            integration = get_integration_layer()
            integration.set_progress_callback(update_progress)
            
            # Create request
            request = AuditRequest(
                sources=sources,
                llm_output=llm_output,
                domain=domain_enum,
                run_drift_check=run_drift,
                generate_corrections=gen_corrections
            )
            
            # Run audit
            status_text.markdown("**Starting:** Initializing audit pipeline...")
            report = integration.run_audit(request)
            
            # Store result
            st.session_state.audit_report = report
            
            # Add to history
            if "history" not in st.session_state:
                st.session_state.history = []
            
            st.session_state.history.append({
                "id": report.report_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "score": report.trust_score.score,
                "claims": len(report.annotated_claims)
            })
            
            # Success
            progress_bar.progress(1.0)
            status_text.empty()
            
            st.success(f"✅ Audit complete! Trust Score: {report.trust_score.score:.0f}/100")
            
            # Navigate to results
            if st.button("View Results →", type="primary"):
                st.session_state.page = "results"
                st.rerun()
            
        except Exception as e:
            logger.error(f"Audit failed: {e}")
            st.error(f"❌ Audit failed: {str(e)}")
            status_text.empty()
            progress_bar.empty()
