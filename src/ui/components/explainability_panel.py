"""
Explainability Panel Component for Hallucination Hunter
Provides detailed explanations for verification decisions

Answers the core questions:
1. Why is this flagged as a hallucination?
2. Where is the proof? (Exact source passage extraction)
3. How confident is the model?
"""

import streamlit as st
from typing import Optional, Dict, Any, List


def render_explainability_panel(
    claim_text: str,
    status: str,  # 'supported', 'hallucination', 'unverifiable'
    confidence: float,
    explanation: str,
    source_snippet: Optional[str] = None,
    source_name: Optional[str] = None,
    paragraph_idx: Optional[int] = None
) -> None:
    """
    Render a comprehensive explainability panel for a claim.
    
    Args:
        claim_text: The claim being explained
        status: Verification status
        confidence: Confidence score (0-1)
        explanation: Detailed explanation of the decision
        source_snippet: Relevant excerpt from source
        source_name: Name of source document
        paragraph_idx: Index of source paragraph
    """
    confidence_pct = int(confidence * 100)
    
    # Determine styling based on status
    if status == "supported":
        status_color = "#10b981"
        status_bg = "#ecfdf5"
        status_icon = "✓"
        status_label = "SUPPORTED"
        certainty_type = "match"
    elif status == "hallucination":
        status_color = "#ef4444"
        status_bg = "#fef2f2"
        status_icon = "✗"
        status_label = "HALLUCINATION"
        certainty_type = "error"
    else:
        status_color = "#f59e0b"
        status_bg = "#fffbeb"
        status_icon = "?"
        status_label = "UNVERIFIABLE"
        certainty_type = "uncertainty"
    
    # Claim header
    st.markdown(f"""
    <div style="
        background: {status_bg};
        border: 1px solid {status_color}40;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    ">
        <div style="
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.5rem;
        ">
            <span style="
                background: {status_color};
                color: white;
                width: 24px;
                height: 24px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 0.85rem;
            ">{status_icon}</span>
            <span style="
                font-weight: 600;
                color: {status_color};
                text-transform: uppercase;
                font-size: 0.85rem;
                letter-spacing: 0.5px;
            ">{status_label}</span>
        </div>
        <div style="
            color: #374151;
            font-size: 0.95rem;
            line-height: 1.5;
        ">
            "{claim_text}"
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Question 1: Why is this flagged?
    st.markdown(f"""
    <div style="
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    ">
        <div style="
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 600;
            color: #1e3a5f;
            font-size: 1rem;
            margin-bottom: 0.75rem;
        ">
            <span style="font-size: 1.25rem;">🔍</span>
            Why is this flagged as a {status.lower()}?
        </div>
        <div style="
            color: #4b5563;
            font-size: 0.95rem;
            line-height: 1.7;
            padding-left: 0.5rem;
            border-left: 3px solid {status_color};
        ">
            {explanation}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Question 2: Where is the proof?
    if source_snippet:
        location_text = f"{source_name}, Paragraph {paragraph_idx + 1}" if source_name and paragraph_idx is not None else "Source document"
        
        st.markdown(f"""
        <div style="
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 10px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        ">
            <div style="
                display: flex;
                align-items: center;
                gap: 0.5rem;
                font-weight: 600;
                color: #1e3a5f;
                font-size: 1rem;
                margin-bottom: 0.75rem;
            ">
                <span style="font-size: 1.25rem;">📖</span>
                Where is the proof?
            </div>
            <div style="
                font-size: 0.8rem;
                color: #6b7280;
                margin-bottom: 0.5rem;
            ">
                📍 {location_text}
            </div>
            <div style="
                background: #f8fafc;
                border-left: 4px solid #3b82f6;
                padding: 1rem;
                border-radius: 0 8px 8px 0;
                font-style: italic;
                color: #374151;
                line-height: 1.6;
            ">
                "{source_snippet}"
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="
            background: #fffbeb;
            border: 1px solid #fcd34d;
            border-radius: 10px;
            padding: 1.25rem;
            margin-bottom: 1rem;
        ">
            <div style="
                display: flex;
                align-items: center;
                gap: 0.5rem;
                font-weight: 600;
                color: #92400e;
                font-size: 1rem;
                margin-bottom: 0.5rem;
            ">
                <span style="font-size: 1.25rem;">📖</span>
                Where is the proof?
            </div>
            <div style="
                color: #b45309;
                font-size: 0.95rem;
            ">
                No matching passage found in the source documents. 
                This claim could not be verified against the provided knowledge base.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Question 3: How confident is the model?
    certainty_level = "certain" if confidence >= 0.85 else ("likely" if confidence >= 0.6 else "possible")
    
    # Confidence bar color
    if confidence >= 0.7:
        bar_color = "#10b981"
    elif confidence >= 0.4:
        bar_color = "#f59e0b"
    else:
        bar_color = "#ef4444"
    
    st.markdown(f"""
    <div style="
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 1.25rem;
        margin-bottom: 1rem;
    ">
        <div style="
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 600;
            color: #1e3a5f;
            font-size: 1rem;
            margin-bottom: 0.75rem;
        ">
            <span style="font-size: 1.25rem;">📊</span>
            How confident is the model?
        </div>
        
        <div style="
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1rem;
        ">
            <div style="
                font-size: 2.5rem;
                font-weight: 700;
                color: {bar_color};
            ">{confidence_pct}%</div>
            <div style="
                flex: 1;
            ">
                <div style="
                    height: 12px;
                    background: #e5e7eb;
                    border-radius: 6px;
                    overflow: hidden;
                ">
                    <div style="
                        width: {confidence_pct}%;
                        height: 100%;
                        background: {bar_color};
                        border-radius: 6px;
                        transition: width 0.5s ease;
                    "></div>
                </div>
            </div>
        </div>
        
        <div style="
            background: #f8fafc;
            border-radius: 8px;
            padding: 1rem;
            color: #4b5563;
            font-size: 0.9rem;
            line-height: 1.6;
        ">
            This assessment indicates a <strong>{certainty_level} {certainty_type}</strong>.
            <br><br>
            {"⚠️ <strong>High certainty:</strong> The model is very confident in this classification. The evidence strongly supports this conclusion." if confidence >= 0.85 else ""}
            {"🔶 <strong>Moderate certainty:</strong> The model has reasonable confidence, but there may be some ambiguity in the source material." if 0.6 <= confidence < 0.85 else ""}
            {"⚡ <strong>Lower certainty:</strong> The model has limited confidence. Manual review is recommended to verify this assessment." if confidence < 0.6 else ""}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_explainability_summary(claims: List[Dict[str, Any]]) -> None:
    """
    Render a summary of all explainability information.
    
    Args:
        claims: List of claim dictionaries with explainability info
    """
    if not claims:
        st.info("No claims to explain. Run verification first.")
        return
    
    # Summary stats
    supported = sum(1 for c in claims if c.get('status') == 'supported')
    hallucinations = sum(1 for c in claims if c.get('status') == 'hallucination')
    unverifiable = sum(1 for c in claims if c.get('status') == 'unverifiable')
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
    ">
        <div style="
            font-weight: 600;
            color: #0369a1;
            font-size: 1.1rem;
            margin-bottom: 1rem;
        ">
            ❓ Explainability Summary
        </div>
        <div style="
            display: flex;
            gap: 2rem;
            flex-wrap: wrap;
        ">
            <div>
                <span style="font-size: 1.5rem; font-weight: 700; color: #10b981;">{supported}</span>
                <span style="color: #6b7280; margin-left: 0.5rem;">claims explained as supported</span>
            </div>
            <div>
                <span style="font-size: 1.5rem; font-weight: 700; color: #ef4444;">{hallucinations}</span>
                <span style="color: #6b7280; margin-left: 0.5rem;">hallucinations identified with reasons</span>
            </div>
            <div>
                <span style="font-size: 1.5rem; font-weight: 700; color: #f59e0b;">{unverifiable}</span>
                <span style="color: #6b7280; margin-left: 0.5rem;">claims requiring manual review</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Individual explanations
    for claim in claims:
        with st.expander(f"📋 {claim.get('claim_text', '')[:60]}..."):
            render_explainability_panel(
                claim_text=claim.get('claim_text', ''),
                status=claim.get('status', 'unverifiable'),
                confidence=claim.get('confidence', 0.0),
                explanation=claim.get('explanation', 'No explanation available'),
                source_snippet=claim.get('source_snippet'),
                source_name=claim.get('source_name'),
                paragraph_idx=claim.get('paragraph_idx')
            )
