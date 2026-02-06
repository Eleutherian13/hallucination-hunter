"""
Results page for displaying audit results
"""

import streamlit as st
from datetime import datetime

from src.ui.components.trust_meter import render_trust_meter, render_category_distribution
from src.ui.components.annotated_text import render_annotated_text
from src.ui.components.claim_card import render_claim_card, render_claim_list
from src.ui.components.source_viewer import render_evidence_panel
from src.layers.correction import AuditReport
from src.config.constants import ClaimCategory, ExportFormat


def render_results_page():
    """Render the results page"""
    report = st.session_state.get("audit_report")
    
    if not report:
        st.warning("No audit results available. Please run an audit first.")
        if st.button("Go to Audit →"):
            st.session_state.page = "audit"
            st.rerun()
        return
    
    # Header
    st.markdown("## 📊 Audit Results")
    
    # Overview row
    render_overview(report)
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Annotated Text",
        "📋 Claims List",
        "📈 Analysis",
        "📤 Export"
    ])
    
    with tab1:
        render_annotated_view(report)
    
    with tab2:
        render_claims_view(report)
    
    with tab3:
        render_analysis_view(report)
    
    with tab4:
        render_export_view(report)


def render_overview(report: AuditReport):
    """Render overview section"""
    col1, col2 = st.columns([1, 2])
    
    with col1:
        render_trust_meter(report.trust_score, show_breakdown=False)
    
    with col2:
        stats = report.to_dict()["statistics"]
        
        st.markdown("### Summary")
        
        col_a, col_b, col_c, col_d = st.columns(4)
        
        with col_a:
            st.metric("Total Claims", stats["total_claims"])
        
        with col_b:
            st.metric(
                "Supported",
                stats["supported"],
                delta=f"{stats['supported']/stats['total_claims']*100:.0f}%" if stats["total_claims"] > 0 else "0%"
            )
        
        with col_c:
            st.metric(
                "Contradicted",
                stats["contradicted"],
                delta=f"-{stats['contradicted']}" if stats["contradicted"] > 0 else None,
                delta_color="inverse"
            )
        
        with col_d:
            st.metric(
                "Unverifiable",
                stats["unverifiable"]
            )
        
        # Recommendations
        if report.trust_score.recommendations:
            st.markdown("#### 💡 Recommendations")
            for rec in report.trust_score.recommendations:
                st.markdown(f"• {rec}")


def render_annotated_view(report: AuditReport):
    """Render annotated text view"""
    st.markdown("### Annotated LLM Output")
    
    # Filter controls
    col1, col2 = st.columns([3, 1])
    
    with col2:
        highlight_mode = st.selectbox(
            "Highlight",
            options=["all", "supported", "contradicted", "unverifiable"],
            index=0
        )
    
    # Render annotated text
    render_annotated_text(
        report.llm_output,
        report.annotated_claims,
        highlight_mode=highlight_mode
    )
    
    # Click to see details
    st.markdown("---")
    st.markdown("### Claim Details")
    st.markdown("Click on a claim above or select below to see details:")
    
    claim_options = {
        f"{i+1}. {ac.claim.text[:50]}...": ac
        for i, ac in enumerate(report.annotated_claims)
    }
    
    selected = st.selectbox(
        "Select claim",
        options=list(claim_options.keys()),
        label_visibility="collapsed"
    )
    
    if selected:
        ac = claim_options[selected]
        render_claim_card(ac, expanded=True)


def render_claims_view(report: AuditReport):
    """Render claims list view"""
    st.markdown("### All Claims")
    
    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        filter_cat = st.selectbox(
            "Filter by category",
            options=["All", "Supported", "Contradicted", "Unverifiable"],
            index=0
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            options=["confidence", "category", "position"],
            index=0
        )
    
    with col3:
        show_corrections = st.checkbox("Show corrections", value=True)
    
    # Filter claims
    claims = report.annotated_claims
    
    if filter_cat != "All":
        try:
            cat = ClaimCategory(filter_cat.lower())
            claims = [c for c in claims if c.verification.category == cat]
        except ValueError:
            pass
    
    # Sort claims
    if sort_by == "confidence":
        claims = sorted(claims, key=lambda c: c.verification.confidence, reverse=True)
    elif sort_by == "category":
        order = {ClaimCategory.CONTRADICTED: 0, ClaimCategory.UNVERIFIABLE: 1, ClaimCategory.SUPPORTED: 2}
        claims = sorted(claims, key=lambda c: order.get(c.verification.category, 3))
    
    # Display
    st.markdown(f"**Showing {len(claims)} claims**")
    
    for ac in claims:
        render_claim_card(ac, show_correction=show_corrections)


def render_analysis_view(report: AuditReport):
    """Render analysis view"""
    st.markdown("### Detailed Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Score Breakdown")
        render_trust_meter(report.trust_score, show_breakdown=True, compact=True)
    
    with col2:
        st.markdown("#### Category Distribution")
        stats = report.to_dict()["statistics"]
        render_category_distribution({
            "supported": stats["supported"],
            "contradicted": stats["contradicted"],
            "unverifiable": stats["unverifiable"]
        })
    
    st.markdown("---")
    
    # Confidence distribution
    st.markdown("#### Confidence Distribution")
    
    confidences = [ac.verification.confidence for ac in report.annotated_claims]
    
    if confidences:
        import pandas as pd
        df = pd.DataFrame({"Confidence": confidences})
        st.bar_chart(df["Confidence"])
    
    # High-risk claims
    st.markdown("---")
    st.markdown("#### ⚠️ High-Risk Claims")
    
    high_risk = [
        ac for ac in report.annotated_claims
        if ac.verification.category == ClaimCategory.CONTRADICTED
        or (ac.verification.category == ClaimCategory.UNVERIFIABLE and ac.verification.confidence < 0.5)
    ]
    
    if high_risk:
        for ac in high_risk[:5]:
            st.markdown(f"""
            <div style="
                background: #fee2e2;
                padding: 0.75rem;
                border-radius: 8px;
                margin-bottom: 0.5rem;
                border-left: 4px solid #ef4444;
            ">
                <strong>{ac.verification.category.value.title()}</strong>: {ac.claim.text}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ No high-risk claims detected")


def render_export_view(report: AuditReport):
    """Render export options"""
    st.markdown("### Export Report")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Choose Format")
        
        format_option = st.radio(
            "Export format",
            options=["JSON", "HTML", "CSV", "PDF"],
            horizontal=True,
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("#### Options")
        include_corrections = st.checkbox("Include corrections", value=True)
        include_evidence = st.checkbox("Include evidence", value=True)
    
    st.markdown("---")
    
    # Generate export
    from src.layers.ui_integration import get_integration_layer
    integration = get_integration_layer()
    
    try:
        export_format = ExportFormat(format_option.lower())
        content = integration.export_report(report, export_format)
        
        # Download button
        if export_format == ExportFormat.PDF:
            st.download_button(
                label=f"📥 Download {format_option}",
                data=content,
                file_name=f"audit_report_{report.report_id[:8]}.pdf",
                mime="application/pdf"
            )
        elif export_format == ExportFormat.HTML:
            st.download_button(
                label=f"📥 Download {format_option}",
                data=content,
                file_name=f"audit_report_{report.report_id[:8]}.html",
                mime="text/html"
            )
            
            # Preview
            with st.expander("Preview HTML"):
                st.components.v1.html(content, height=500, scrolling=True)
        else:
            st.download_button(
                label=f"📥 Download {format_option}",
                data=content,
                file_name=f"audit_report_{report.report_id[:8]}.{format_option.lower()}",
                mime="text/plain"
            )
            
            # Preview
            with st.expander("Preview"):
                if isinstance(content, bytes):
                    content_str = content.decode('utf-8', errors='replace')
                elif isinstance(content, str):
                    content_str = content
                else:
                    content_str = str(content)
                st.code(content_str[:2000] + "..." if len(content_str) > 2000 else content_str)
    
    except Exception as e:
        st.error(f"Export failed: {str(e)}")
    
    # Share link
    st.markdown("---")
    st.markdown("#### Share")
    
    st.text_input(
        "Report ID",
        value=report.report_id,
        disabled=True,
        help="Use this ID to retrieve the report via API"
    )
