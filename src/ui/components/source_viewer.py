"""
Source document viewer component
"""

import streamlit as st
from typing import List, Dict, Optional, Any
from src.layers.ingestion import DocumentIndex


def render_source_viewer(
    doc_index: DocumentIndex,
    highlight_text: Optional[str] = None
):
    """
    Render source document viewer with navigation
    
    Args:
        doc_index: Document index with processed documents
        highlight_text: Optional text to highlight
    """
    documents = list(doc_index.documents.values())
    
    if not documents:
        st.info("No source documents loaded")
        return
    
    st.markdown("### 📚 Source Documents")
    
    # Document tabs
    if len(documents) == 1:
        render_single_document(documents[0], highlight_text)
    else:
        tabs = st.tabs([doc.metadata.filename for doc in documents])
        for tab, doc in zip(tabs, documents):
            with tab:
                render_single_document(doc, highlight_text)


def render_single_document(
    doc: Any,  # ProcessedDocument type
    highlight_text: Optional[str] = None
):
    """Render a single document"""
    # Metadata
    with st.expander("📋 Document Info", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Filename:** {doc.metadata.filename}")
            st.markdown(f"**Type:** {doc.metadata.file_type}")
        with col2:
            st.markdown(f"**Chunks:** {len(doc.chunks)}")
            st.markdown(f"**Characters:** {sum(len(c) for c in doc.chunks):,}")
    
    # Content
    content = "\n\n".join(doc.chunks[:10])  # Limit for display
    
    if highlight_text and highlight_text in content:
        # Highlight matching text
        highlighted_content = content.replace(
            highlight_text,
            f'<mark style="background: #fef08a; padding: 2px 4px;">{highlight_text}</mark>'
        )
        st.markdown(f"""
        <div style="
            background: white;
            padding: 1rem;
            border-radius: 8px;
            max-height: 400px;
            overflow-y: auto;
            font-family: 'Source Sans Pro', sans-serif;
            line-height: 1.6;
        ">
            {highlighted_content}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.text_area(
            "Content",
            value=content,
            height=300,
            label_visibility="collapsed"
        )
    
    if len(doc.chunks) > 10:
        st.caption(f"Showing first 10 of {len(doc.chunks)} chunks")


def render_evidence_panel(
    evidence_text: str,
    citation: str,
    relevance_score: Optional[float] = None
):
    """
    Render evidence panel for a claim
    
    Args:
        evidence_text: The evidence text
        citation: Citation string
        relevance_score: Optional relevance score
    """
    score_badge = ""
    if relevance_score is not None:
        score_badge = f"""
        <span style="
            background: #dbeafe;
            color: #1e40af;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            margin-left: 0.5rem;
        ">Relevance: {relevance_score:.0%}</span>
        """
    
    st.markdown(f"""
    <div style="
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    ">
        <div style="
            font-size: 0.8rem;
            color: #64748b;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
        ">
            📖 <strong style="margin-left: 0.25rem;">{citation}</strong>
            {score_badge}
        </div>
        <div style="
            font-style: italic;
            color: #334155;
            line-height: 1.6;
        ">
            "{evidence_text}"
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_chunk_navigator(chunks: List[str], current_index: int = 0):
    """
    Render chunk navigator for large documents
    
    Args:
        chunks: List of document chunks
        current_index: Current chunk index
    """
    st.markdown("#### Chunk Navigator")
    
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        if st.button("◀ Prev", disabled=current_index == 0):
            return max(0, current_index - 1)
    
    with col2:
        new_index = st.slider(
            "Chunk",
            min_value=0,
            max_value=len(chunks) - 1,
            value=current_index,
            label_visibility="collapsed"
        )
    
    with col3:
        if st.button("Next ▶", disabled=current_index >= len(chunks) - 1):
            return min(len(chunks) - 1, current_index + 1)
    
    return new_index


def render_document_stats(doc_index: DocumentIndex):
    """Render document statistics"""
    st.markdown("#### Document Statistics")
    
    total_docs = doc_index.total_documents
    total_chunks = doc_index.total_chunks
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Documents", total_docs)
    
    with col2:
        st.metric("Chunks", total_chunks)
    
    with col3:
        avg_chunks = total_chunks / total_docs if total_docs > 0 else 0
        st.metric("Avg Chunks/Doc", f"{avg_chunks:.1f}")
