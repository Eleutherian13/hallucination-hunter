"""
Trust meter visualization component
"""

import streamlit as st
from typing import Dict, Optional
from src.layers.scoring import TrustScore, TrustLevel
from src.config.constants import TrustZone


def render_trust_meter(
    trust_score: TrustScore,
    show_breakdown: bool = True,
    compact: bool = False
):
    """
    Render trust score meter visualization
    
    Args:
        trust_score: Trust score object
        show_breakdown: Whether to show score breakdown
        compact: Use compact layout
    """
    score = trust_score.score
    level = trust_score.level
    zone = trust_score.zone
    
    # Color based on score
    if score >= 70:
        color = "#10b981"  # Green
        bg_color = "#d1fae5"
    elif score >= 40:
        color = "#f59e0b"  # Yellow
        bg_color = "#fef3c7"
    else:
        color = "#ef4444"  # Red
        bg_color = "#fee2e2"
    
    if compact:
        # Compact display
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 1rem; padding: 0.5rem; background: {bg_color}; border-radius: 8px;">
            <div style="font-size: 2rem; font-weight: bold; color: {color};">{score:.0f}</div>
            <div style="flex: 1;">
                <div style="font-weight: 600; color: #1f2937;">{level.value.title()}</div>
                <div style="font-size: 0.8rem; color: #6b7280;">{zone[2]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Full display
    st.markdown(f"""
    <div style="text-align: center; padding: 2rem; background: {bg_color}; border-radius: 16px; margin-bottom: 1rem;">
        <div style="font-size: 4rem; font-weight: bold; color: {color};">{score:.0f}</div>
        <div style="font-size: 1.5rem; color: #1f2937; margin-top: 0.5rem;">/ 100</div>
        <div style="font-size: 1.2rem; color: {color}; font-weight: 600; margin-top: 0.5rem;">{level.value.title()} Trust</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress bar
    st.progress(score / 100)
    
    # Zone indicator
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #6b7280; margin-top: 0.5rem;">
        <span>🔴 Low</span>
        <span>🟡 Medium</span>
        <span>🟢 High</span>
    </div>
    """, unsafe_allow_html=True)
    
    if show_breakdown:
        st.markdown("---")
        render_score_breakdown(trust_score.breakdown.to_dict())


def render_score_breakdown(breakdown: Dict):
    """Render detailed score breakdown"""
    st.markdown("#### Score Breakdown")
    
    components = [
        ("Supported Ratio", breakdown["supported_ratio"]),
        ("Confidence", breakdown["avg_confidence"]),
        ("Stability", breakdown["drift_score"]),
        ("Severity", breakdown["severity_score"])
    ]
    
    for name, data in components:
        value = data["value"]
        contribution = data["contribution"]
        weight = data["weight"]
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**{name}**")
            st.progress(min(max(value, 0), 1))
        with col2:
            st.markdown(f"<div style='text-align: center;'>{value:.1%}</div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div style='text-align: center; color: #6b7280;'>×{weight}</div>", unsafe_allow_html=True)


def render_mini_trust_meter(score: float):
    """Render a minimal trust meter for inline display"""
    if score >= 70:
        color = "#10b981"
    elif score >= 40:
        color = "#f59e0b"
    else:
        color = "#ef4444"
    
    return f"""
    <div style="display: inline-flex; align-items: center; gap: 0.5rem;">
        <div style="width: 60px; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden;">
            <div style="width: {score}%; height: 100%; background: {color};"></div>
        </div>
        <span style="font-weight: 600; color: {color};">{score:.0f}</span>
    </div>
    """


def render_category_distribution(counts: Dict[str, int]):
    """Render category distribution chart"""
    total = sum(counts.values())
    if total == 0:
        st.info("No claims to display")
        return
    
    st.markdown("#### Claim Distribution")
    
    colors = {
        "supported": "#10b981",
        "contradicted": "#ef4444",
        "unverifiable": "#f59e0b"
    }
    
    for category, count in counts.items():
        pct = count / total * 100
        color = colors.get(category, "#6b7280")
        
        st.markdown(f"""
        <div style="margin-bottom: 0.5rem;">
            <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 0.25rem;">
                <span style="text-transform: capitalize;">{category}</span>
                <span style="color: #6b7280;">{count} ({pct:.1f}%)</span>
            </div>
            <div style="height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden;">
                <div style="width: {pct}%; height: 100%; background: {color};"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
