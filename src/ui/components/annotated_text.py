"""
Annotated text display component
"""

import streamlit as st
from typing import List, Dict, Optional
from src.layers.correction import AnnotatedClaim
from src.config.constants import ClaimCategory, Colors


def render_annotated_text(
    original_text: str,
    annotated_claims: List[AnnotatedClaim],
    highlight_mode: str = "all"  # all, supported, contradicted, unverifiable
):
    """
    Render text with highlighted claims
    
    Args:
        original_text: Original LLM output text
        annotated_claims: List of annotated claims
        highlight_mode: Which claims to highlight
    """
    # Filter claims based on mode
    if highlight_mode != "all":
        try:
            category = ClaimCategory(highlight_mode)
            annotated_claims = [
                c for c in annotated_claims 
                if c.verification.category == category
            ]
        except ValueError:
            pass
    
    # Sort claims by position in text (reverse for replacement)
    sorted_claims = sorted(
        annotated_claims,
        key=lambda c: original_text.find(c.claim.text),
        reverse=True
    )
    
    result_text = original_text
    
    for ac in sorted_claims:
        claim_text = ac.claim.text
        category = ac.verification.category.value
        confidence = ac.verification.confidence
        color = ac.color
        
        # Find position
        pos = result_text.find(claim_text)
        if pos == -1:
            continue
        
        # Create highlighted span
        highlighted = f'''<span 
            class="claim-highlight claim-{category}" 
            style="
                background-color: {color}20; 
                border-bottom: 2px solid {color}; 
                cursor: pointer;
                padding: 2px 4px;
                border-radius: 3px;
            " 
            title="{category.title()} ({confidence:.0%})"
            data-claim-id="{ac.claim.claim_id}"
        >{claim_text}</span>'''
        
        result_text = result_text[:pos] + highlighted + result_text[pos + len(claim_text):]
    
    # Render with custom styling
    st.markdown(f"""
    <div style="
        background: white; 
        padding: 1.5rem; 
        border-radius: 12px; 
        line-height: 1.8; 
        font-size: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    ">
        {result_text}
    </div>
    """, unsafe_allow_html=True)
    
    # Legend
    render_legend()


def render_legend():
    """Render color legend for claims"""
    st.markdown("""
    <div style="display: flex; gap: 1.5rem; justify-content: center; margin-top: 1rem; font-size: 0.85rem;">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <div style="width: 12px; height: 12px; background: #10b981; border-radius: 2px;"></div>
            <span>Supported</span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <div style="width: 12px; height: 12px; background: #ef4444; border-radius: 2px;"></div>
            <span>Contradicted</span>
        </div>
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <div style="width: 12px; height: 12px; background: #f59e0b; border-radius: 2px;"></div>
            <span>Unverifiable</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_diff_view(
    original: str,
    corrected: str
):
    """
    Render side-by-side diff view
    
    Args:
        original: Original text
        corrected: Corrected text
    """
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Original**")
        st.markdown(f"""
        <div style="
            background: #fee2e2;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #ef4444;
        ">
            {original}
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("**Corrected**")
        st.markdown(f"""
        <div style="
            background: #d1fae5;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #10b981;
        ">
            {corrected}
        </div>
        """, unsafe_allow_html=True)


def render_text_with_tooltip(
    text: str,
    tooltip: str,
    color: str = "#2563eb"
):
    """Render text with hover tooltip"""
    return f"""
    <span style="
        border-bottom: 1px dashed {color};
        cursor: help;
    " title="{tooltip}">{text}</span>
    """


def get_highlight_style(category: str) -> Dict:
    """Get CSS style for highlighting"""
    styles = {
        "supported": {
            "background": "rgba(16, 185, 129, 0.15)",
            "border": "#10b981",
            "text": "#065f46"
        },
        "contradicted": {
            "background": "rgba(239, 68, 68, 0.15)",
            "border": "#ef4444",
            "text": "#991b1b"
        },
        "unverifiable": {
            "background": "rgba(245, 158, 11, 0.15)",
            "border": "#f59e0b",
            "text": "#92400e"
        }
    }
    return styles.get(category, styles["unverifiable"])
