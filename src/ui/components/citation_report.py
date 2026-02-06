"""
Citation Report Component for Hallucination Hunter
Provides direct links to source paragraphs that validate claims
"""

import streamlit as st
from typing import Optional, Dict, Any, List


def render_citation_report(
    claim_text: str,
    source_name: str,
    source_snippet: str,
    paragraph_idx: int,
    confidence: float = 0.0,
    on_click_callback: Optional[callable] = None
) -> None:
    """
    Render a citation report card for a supported claim.
    
    Args:
        claim_text: The claim text that is being cited
        source_name: Name of the source document
        source_snippet: The relevant excerpt from the source
        paragraph_idx: Index of the paragraph in source document
        confidence: Confidence score of the verification
        on_click_callback: Optional callback when citation is clicked
    """
    confidence_pct = int(confidence * 100)
    
    st.markdown(f"""
    <div class="citation-card" style="
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.25rem;
        margin: 0.75rem 0;
        transition: all 0.2s ease;
    ">
        <div style="
            font-size: 0.8rem;
            color: #64748b;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
        ">
            <span>📚</span>
            <span>{source_name} • Paragraph {paragraph_idx + 1}</span>
            <span style="margin-left: auto; color: #10b981;">
                {confidence_pct}% match
            </span>
        </div>
        
        <div style="
            font-style: italic;
            color: #374151;
            border-left: 3px solid #3b82f6;
            padding-left: 1rem;
            margin: 0.75rem 0;
            line-height: 1.6;
        ">
            "{source_snippet}"
        </div>
        
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 1rem;
            padding-top: 0.75rem;
            border-top: 1px solid #e2e8f0;
        ">
            <span style="
                font-size: 0.85rem;
                color: #6b7280;
            ">
                Validates: <em>"{claim_text[:50]}..."</em>
            </span>
            <span style="
                color: #3b82f6;
                font-size: 0.85rem;
                font-weight: 500;
                cursor: pointer;
            ">
                🔗 Jump to source
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_citation_summary(citations: List[Dict[str, Any]]) -> None:
    """
    Render a summary of all citations.
    
    Args:
        citations: List of citation dictionaries with keys:
            - claim_text: str
            - source_name: str
            - source_snippet: str
            - paragraph_idx: int
            - confidence: float
    """
    if not citations:
        st.info("No citations available. Upload documents and run verification to generate citations.")
        return
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    ">
        <div style="
            font-weight: 600;
            color: #1e40af;
            font-size: 1rem;
        ">
            📋 Citation Summary
        </div>
        <div style="
            color: #3b82f6;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        ">
            {len(citations)} supported claims with source citations
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    for citation in citations:
        render_citation_report(
            claim_text=citation.get('claim_text', ''),
            source_name=citation.get('source_name', 'Unknown Source'),
            source_snippet=citation.get('source_snippet', ''),
            paragraph_idx=citation.get('paragraph_idx', 0),
            confidence=citation.get('confidence', 0.0)
        )


def render_citation_export_button(citations: List[Dict[str, Any]]) -> None:
    """
    Render a button to export citations in various formats.
    
    Args:
        citations: List of citation dictionaries
    """
    if not citations:
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export as PDF", use_container_width=True):
            st.info("PDF export functionality coming soon!")
    
    with col2:
        if st.button("📊 Export as JSON", use_container_width=True):
            import json
            json_str = json.dumps(citations, indent=2)
            st.download_button(
                label="⬇️ Download JSON",
                data=json_str,
                file_name="citations.json",
                mime="application/json"
            )
    
    with col3:
        if st.button("📝 Export as Markdown", use_container_width=True):
            md_content = "# Citation Report\n\n"
            for i, citation in enumerate(citations, 1):
                md_content += f"## Citation {i}\n\n"
                md_content += f"**Claim:** {citation.get('claim_text', '')}\n\n"
                md_content += f"**Source:** {citation.get('source_name', '')} (Paragraph {citation.get('paragraph_idx', 0) + 1})\n\n"
                md_content += f"> {citation.get('source_snippet', '')}\n\n"
                md_content += f"**Confidence:** {int(citation.get('confidence', 0) * 100)}%\n\n---\n\n"
            
            st.download_button(
                label="⬇️ Download Markdown",
                data=md_content,
                file_name="citations.md",
                mime="text/markdown"
            )
