"""
Home page for Hallucination Hunter
"""

import streamlit as st


def render_home():
    """Render the home page"""
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">🔍 Hallucination Hunter</h1>
        <p style="font-size: 1.2rem; color: #64748b; max-width: 600px; margin: 0 auto;">
            AI-assisted fact-checking system for LLM outputs. Verify claims, detect hallucinations, and ensure accuracy.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick stats if available
    if st.session_state.get("history"):
        render_recent_activity()
    
    # Feature cards
    st.markdown("### ✨ Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
            padding: 1.5rem;
            border-radius: 12px;
            height: 200px;
        ">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📝</div>
            <h4 style="margin: 0 0 0.5rem 0; color: #1e40af;">Claim Extraction</h4>
            <p style="font-size: 0.9rem; color: #3730a3; margin: 0;">
                Automatically extract and categorize claims from any LLM output.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
            padding: 1.5rem;
            border-radius: 12px;
            height: 200px;
        ">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">✅</div>
            <h4 style="margin: 0 0 0.5rem 0; color: #065f46;">Verification</h4>
            <p style="font-size: 0.9rem; color: #047857; margin: 0;">
                Verify claims against trusted source documents using NLI models.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
            padding: 1.5rem;
            border-radius: 12px;
            height: 200px;
        ">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📊</div>
            <h4 style="margin: 0 0 0.5rem 0; color: #92400e;">Trust Scoring</h4>
            <p style="font-size: 0.9rem; color: #b45309; margin: 0;">
                Get comprehensive trust scores with detailed breakdowns.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
            padding: 1.5rem;
            border-radius: 12px;
            height: 200px;
        ">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔧</div>
            <h4 style="margin: 0 0 0.5rem 0; color: #991b1b;">Corrections</h4>
            <p style="font-size: 0.9rem; color: #b91c1c; margin: 0;">
                Generate corrected versions of hallucinated claims.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
            padding: 1.5rem;
            border-radius: 12px;
            height: 200px;
        ">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📖</div>
            <h4 style="margin: 0 0 0.5rem 0; color: #3730a3;">Citations</h4>
            <p style="font-size: 0.9rem; color: #4338ca; margin: 0;">
                Get precise citations linking claims to evidence sources.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%);
            padding: 1.5rem;
            border-radius: 12px;
            height: 200px;
        ">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📤</div>
            <h4 style="margin: 0 0 0.5rem 0; color: #6b21a8;">Export</h4>
            <p style="font-size: 0.9rem; color: #7c3aed; margin: 0;">
                Export reports in JSON, HTML, CSV, or PDF formats.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Call to action
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start New Audit", use_container_width=True, type="primary"):
            st.session_state.page = "audit"
            st.rerun()
    
    # How it works
    st.markdown("### 🔄 How It Works")
    
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; padding: 2rem 0;">
        <div style="text-align: center; flex: 1;">
            <div style="
                width: 60px;
                height: 60px;
                background: #2563eb;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 1rem;
                color: white;
                font-size: 1.5rem;
            ">1</div>
            <h4>Upload Sources</h4>
            <p style="font-size: 0.9rem; color: #64748b;">Add trusted documents as reference sources</p>
        </div>
        <div style="color: #94a3b8; font-size: 2rem;">→</div>
        <div style="text-align: center; flex: 1;">
            <div style="
                width: 60px;
                height: 60px;
                background: #2563eb;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 1rem;
                color: white;
                font-size: 1.5rem;
            ">2</div>
            <h4>Paste LLM Output</h4>
            <p style="font-size: 0.9rem; color: #64748b;">Add the text you want to verify</p>
        </div>
        <div style="color: #94a3b8; font-size: 2rem;">→</div>
        <div style="text-align: center; flex: 1;">
            <div style="
                width: 60px;
                height: 60px;
                background: #2563eb;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 1rem;
                color: white;
                font-size: 1.5rem;
            ">3</div>
            <h4>Run Audit</h4>
            <p style="font-size: 0.9rem; color: #64748b;">Get detailed verification results</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_recent_activity():
    """Render recent audit activity"""
    st.markdown("### 📈 Recent Activity")
    
    history = st.session_state.get("history", [])[-5:]
    
    for item in reversed(history):
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            st.markdown(f"**{item.get('timestamp', 'Unknown')}**")
        
        with col2:
            score = item.get('score', 0)
            color = "#10b981" if score >= 70 else "#f59e0b" if score >= 40 else "#ef4444"
            st.markdown(f"<span style='color: {color}; font-weight: bold;'>{score:.0f}/100</span>", unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"{item.get('claims', 0)} claims")
        
        with col4:
            if st.button("View", key=f"view_{item.get('id', '')}"):
                st.session_state.selected_report = item.get('id')
                st.session_state.page = "results"
                st.rerun()
