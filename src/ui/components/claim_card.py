"""
Claim card component for displaying individual claims
"""

import streamlit as st
from typing import Optional, Callable
from src.layers.correction import AnnotatedClaim
from src.config.constants import ClaimCategory


def render_claim_card(
    annotated_claim: AnnotatedClaim,
    show_evidence: bool = True,
    show_correction: bool = True,
    on_feedback: Optional[Callable] = None,
    expanded: bool = False
):
    """
    Render a claim card with full details
    
    Args:
        annotated_claim: The annotated claim to display
        show_evidence: Whether to show evidence
        show_correction: Whether to show correction
        on_feedback: Callback for feedback submission
        expanded: Whether to start expanded
    """
    ac = annotated_claim
    category = ac.verification.category
    color = ac.color
    
    # Category icon
    icons = {
        ClaimCategory.SUPPORTED: "✅",
        ClaimCategory.CONTRADICTED: "❌",
        ClaimCategory.UNVERIFIABLE: "❓"
    }
    icon = icons.get(category, "❓")
    
    # Card container
    with st.container():
        st.markdown(f"""
        <div style="
            background: white;
            border-left: 4px solid {color};
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div style="flex: 1;">
                    <div style="font-size: 0.8rem; color: {color}; font-weight: 600; margin-bottom: 0.5rem;">
                        {icon} {category.value.upper()}
                    </div>
                    <div style="font-size: 1rem; color: #1f2937; line-height: 1.5;">
                        {ac.claim.text}
                    </div>
                </div>
                <div style="
                    background: {color}20;
                    color: {color};
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-weight: 600;
                    font-size: 0.9rem;
                    margin-left: 1rem;
                ">
                    {ac.verification.confidence:.0%}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Expandable details
        with st.expander("View Details", expanded=expanded):
            # Evidence
            if show_evidence and ac.verification.evidence_used:
                st.markdown("**📖 Evidence:**")
                st.markdown(f"""
                <div style="
                    background: #f8fafc;
                    padding: 0.75rem;
                    border-radius: 6px;
                    font-style: italic;
                    color: #475569;
                    margin-bottom: 1rem;
                ">
                    "{ac.verification.evidence_used}"
                </div>
                """, unsafe_allow_html=True)
                
                st.caption(f"📍 {ac.verification.citation}")
            
            # Explanation
            st.markdown("**💬 Explanation:**")
            st.markdown(ac.verification.explanation)
            
            # Correction
            if show_correction and ac.correction:
                st.markdown("---")
                st.markdown("**✏️ Suggested Correction:**")
                st.markdown(f"""
                <div style="
                    background: #d1fae5;
                    padding: 0.75rem;
                    border-radius: 6px;
                    color: #065f46;
                ">
                    {ac.correction.corrected_claim}
                </div>
                """, unsafe_allow_html=True)
                
                if ac.correction.explanation:
                    st.caption(f"ℹ️ {ac.correction.explanation}")
            
            # Feedback buttons
            if on_feedback:
                st.markdown("---")
                st.markdown("**Was this classification correct?**")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("👍 Correct", key=f"fb_correct_{ac.claim.claim_id}"):
                        on_feedback(ac.claim.claim_id, "correct")
                
                with col2:
                    if st.button("👎 Wrong", key=f"fb_wrong_{ac.claim.claim_id}"):
                        on_feedback(ac.claim.claim_id, "wrong")
                
                with col3:
                    if st.button("🤔 Unsure", key=f"fb_unsure_{ac.claim.claim_id}"):
                        on_feedback(ac.claim.claim_id, "unsure")


def render_claim_list(
    claims: list,
    filter_category: Optional[ClaimCategory] = None,
    sort_by: str = "confidence"
):
    """
    Render a list of claim cards
    
    Args:
        claims: List of AnnotatedClaim objects
        filter_category: Optional category filter
        sort_by: Sort order (confidence, category, position)
    """
    # Filter
    if filter_category:
        claims = [c for c in claims if c.verification.category == filter_category]
    
    # Sort
    if sort_by == "confidence":
        claims = sorted(claims, key=lambda c: c.verification.confidence, reverse=True)
    elif sort_by == "category":
        order = {ClaimCategory.CONTRADICTED: 0, ClaimCategory.UNVERIFIABLE: 1, ClaimCategory.SUPPORTED: 2}
        claims = sorted(claims, key=lambda c: order.get(c.verification.category, 3))
    
    # Render
    if not claims:
        st.info("No claims match the current filter")
        return
    
    for claim in claims:
        render_claim_card(claim)


def render_compact_claim(annotated_claim: AnnotatedClaim):
    """Render a compact version of a claim"""
    ac = annotated_claim
    color = ac.color
    
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.5rem;
        border-left: 3px solid {color};
        background: {color}10;
        border-radius: 4px;
        margin-bottom: 0.5rem;
    ">
        <div style="
            width: 8px;
            height: 8px;
            background: {color};
            border-radius: 50%;
        "></div>
        <div style="flex: 1; font-size: 0.9rem; color: #374151;">
            {ac.claim.text[:100]}{'...' if len(ac.claim.text) > 100 else ''}
        </div>
        <div style="
            font-size: 0.8rem;
            color: {color};
            font-weight: 600;
        ">
            {ac.verification.confidence:.0%}
        </div>
    </div>
    """, unsafe_allow_html=True)
