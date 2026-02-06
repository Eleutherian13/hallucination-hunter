"""
Sidebar component for navigation and settings
"""

import streamlit as st
from src.config.constants import Domain


def render_sidebar():
    """Render the application sidebar"""
    with st.sidebar:
        # Logo and title
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h1 style="font-size: 2rem; margin: 0;">🔍</h1>
            <h2 style="font-size: 1.2rem; margin: 0.5rem 0; color: #1e40af;">Hallucination Hunter</h2>
            <p style="font-size: 0.8rem; color: #64748b; margin: 0;">v2.0</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Navigation
        st.markdown("### Navigation")
        
        if st.button("🏠 Home", key="nav_home", use_container_width=True):
            st.session_state.page = "home"
            st.rerun()
        
        if st.button("📝 New Audit", key="nav_audit", use_container_width=True):
            st.session_state.page = "audit"
            st.rerun()
        
        if st.session_state.get("audit_report"):
            if st.button("📊 Results", key="nav_results", use_container_width=True):
                st.session_state.page = "results"
                st.rerun()
        
        if st.button("⚙️ Settings", key="nav_settings", use_container_width=True):
            st.session_state.page = "settings"
            st.rerun()
        
        st.divider()
        
        # Quick settings
        st.markdown("### Quick Settings")
        
        domain = st.selectbox(
            "Domain",
            options=[d.value for d in Domain],
            index=0,
            key="sidebar_domain"
        )
        st.session_state.domain = domain
        
        st.toggle(
            "Enable Drift Check",
            key="enable_drift",
            value=False
        )
        
        st.toggle(
            "Generate Corrections",
            key="enable_corrections",
            value=True
        )
        
        st.divider()
        
        # Status
        st.markdown("### Status")
        
        sources = st.session_state.get("sources", [])
        llm_output = st.session_state.get("llm_output", "")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Sources", len(sources))
        with col2:
            output_chars = len(llm_output)
            st.metric("Output", f"{output_chars} chars" if output_chars else "-")
        
        if st.session_state.get("audit_report"):
            report = st.session_state.audit_report
            st.success(f"✅ Score: {report.trust_score.score:.0f}/100")
        
        st.divider()
        
        # Footer
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0; font-size: 0.7rem; color: #94a3b8;">
            <p>DataForge Track 1 • E-Summit '26</p>
            <p>Made with ❤️</p>
        </div>
        """, unsafe_allow_html=True)
