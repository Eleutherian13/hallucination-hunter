"""
Correction Panel Component for Hallucination Hunter
Displays correction suggestions for hallucinated claims
"""

import streamlit as st
from typing import Optional, Dict, Any, List


def render_correction_panel(
    original_text: str,
    corrected_text: str,
    explanation: str = "",
    source_reference: str = "",
    confidence: float = 0.0
) -> None:
    """
    Render a correction panel for a hallucinated claim.
    
    Args:
        original_text: The original hallucinated text
        corrected_text: The suggested correction based on sources
        explanation: Why this correction is suggested
        source_reference: Reference to the source document
        confidence: Confidence in the correction
    """
    confidence_pct = int(confidence * 100)
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border: 1px solid #6ee7b7;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    ">
        <div style="
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
        ">
            <span style="
                font-size: 0.85rem;
                color: #065f46;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            ">
                💡 Suggested Correction
            </span>
            <span style="
                font-size: 0.8rem;
                color: #059669;
                background: white;
                padding: 0.25rem 0.75rem;
                border-radius: 20px;
            ">
                {confidence_pct}% confidence
            </span>
        </div>
        
        <div style="
            background: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 0.75rem;
        ">
            <div style="
                font-size: 0.75rem;
                color: #991b1b;
                font-weight: 600;
                margin-bottom: 0.5rem;
            ">
                ❌ ORIGINAL (Hallucinated)
            </div>
            <div style="
                text-decoration: line-through;
                color: #dc2626;
                opacity: 0.9;
            ">
                {original_text}
            </div>
        </div>
        
        <div style="
            text-align: center;
            color: #10b981;
            font-size: 1.5rem;
            margin: 0.5rem 0;
        ">
            ↓
        </div>
        
        <div style="
            background: white;
            border: 2px solid #10b981;
            border-radius: 8px;
            padding: 1rem;
        ">
            <div style="
                font-size: 0.75rem;
                color: #065f46;
                font-weight: 600;
                margin-bottom: 0.5rem;
            ">
                ✓ CORRECTED VERSION
            </div>
            <div style="
                color: #065f46;
                font-weight: 500;
            ">
                {corrected_text}
            </div>
        </div>
        
        {"<div style='margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #a7f3d0;'><div style='font-size: 0.8rem; color: #047857; font-weight: 600; margin-bottom: 0.5rem;'>📖 Based on:</div><div style='font-size: 0.85rem; color: #065f46; font-style: italic;'>" + source_reference + "</div></div>" if source_reference else ""}
    </div>
    """, unsafe_allow_html=True)


def render_corrections_summary(corrections: List[Dict[str, Any]]) -> None:
    """
    Render a summary of all corrections needed.
    
    Args:
        corrections: List of correction dictionaries with keys:
            - original_text: str
            - corrected_text: str
            - explanation: str (optional)
            - source_reference: str (optional)
            - confidence: float
    """
    if not corrections:
        st.success("✅ No corrections needed - all claims are factually accurate!")
        return
    
    # Summary header
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #fecaca;
    ">
        <div style="
            display: flex;
            align-items: center;
            gap: 0.75rem;
        ">
            <span style="font-size: 1.5rem;">⚠️</span>
            <div>
                <div style="
                    font-weight: 600;
                    color: #991b1b;
                    font-size: 1rem;
                ">
                    {len(corrections)} Correction(s) Needed
                </div>
                <div style="
                    color: #dc2626;
                    font-size: 0.85rem;
                    margin-top: 0.25rem;
                ">
                    The following claims contain factual errors and should be corrected
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render each correction
    for correction in corrections:
        render_correction_panel(
            original_text=correction.get('original_text', ''),
            corrected_text=correction.get('corrected_text', ''),
            explanation=correction.get('explanation', ''),
            source_reference=correction.get('source_reference', ''),
            confidence=correction.get('confidence', 0.0)
        )


def render_correction_actions(corrections: List[Dict[str, Any]]) -> None:
    """
    Render action buttons for corrections.
    
    Args:
        corrections: List of correction dictionaries
    """
    if not corrections:
        return
    
    st.markdown("---")
    st.markdown("### 📤 Export Corrections")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Copy All Corrections", use_container_width=True):
            corrected_text = "\n\n".join([
                c.get('corrected_text', '') for c in corrections
            ])
            st.code(corrected_text, language=None)
            st.info("Corrections displayed above - copy as needed")
    
    with col2:
        if st.button("📄 Generate Corrected Document", use_container_width=True):
            st.info("This will generate a new document with all corrections applied")
            
            # Show preview
            st.markdown("#### Preview of Corrected Content:")
            for i, correction in enumerate(corrections, 1):
                st.markdown(f"**{i}.** {correction.get('corrected_text', '')}")


def render_inline_correction(
    original_text: str,
    corrected_text: str,
    compact: bool = False
) -> None:
    """
    Render a compact inline correction.
    
    Args:
        original_text: The original text
        corrected_text: The corrected text
        compact: Whether to use compact styling
    """
    if compact:
        st.markdown(f"""
        <span style="
            text-decoration: line-through;
            color: #ef4444;
            background: #fee2e2;
            padding: 0.1rem 0.25rem;
            border-radius: 3px;
        ">{original_text}</span>
        →
        <span style="
            color: #10b981;
            background: #d1fae5;
            padding: 0.1rem 0.25rem;
            border-radius: 3px;
            font-weight: 500;
        ">{corrected_text}</span>
        """, unsafe_allow_html=True)
    else:
        render_correction_panel(original_text, corrected_text)
