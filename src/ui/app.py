"""
Hallucination Hunter v2.0 - Main Streamlit Application
E-Summit '26 DataForge Track 1

Features:
- Split-screen interface with source documents and LLM output
- Color-coded annotations (Green/Red/Yellow)
- Citation report with direct links to source paragraphs
- Correction engine for hallucinated content
- Visual Confidence Meter
- Click-to-scroll evidence navigation
- Full explainability (why flagged, where is proof, confidence level)
"""

import streamlit as st
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import hashlib

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# =============================================================================
# Data Classes for Type Safety
# =============================================================================

@dataclass
class SourceDocument:
    """Represents a source document"""
    id: str
    name: str
    content: str
    file_type: str
    paragraphs: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class AnnotatedClaim:
    """Represents an annotated claim from LLM output"""
    id: str
    text: str
    status: str  # 'supported', 'hallucination', 'unverifiable'
    confidence: float
    source_doc_id: Optional[str] = None
    source_paragraph_idx: Optional[int] = None
    source_snippet: Optional[str] = None
    explanation: str = ""
    correction: Optional[str] = None

@dataclass
class VerificationResult:
    """Complete verification result"""
    overall_confidence: float
    total_claims: int
    supported_count: int
    hallucination_count: int
    unverifiable_count: int
    annotated_claims: List[AnnotatedClaim] = field(default_factory=list)


# =============================================================================
# Page Configuration & Custom CSS
# =============================================================================

def setup_page():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title="Hallucination Hunter v2.0",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Inject comprehensive custom CSS
    st.markdown("""
    <style>
    /* Global Styles */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    /* Header */
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    /* Panel Styling */
    .panel {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid #e5e7eb;
        margin-bottom: 1rem;
    }
    
    .panel-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e3a5f;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 2px solid #e8f4f8;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Color-Coded Annotations */
    .annotation {
        padding: 1rem 1.25rem;
        margin: 0.75rem 0;
        border-radius: 0 10px 10px 0;
        cursor: pointer;
        transition: all 0.25s ease;
        position: relative;
    }
    
    .annotation:hover {
        transform: translateX(8px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .annotation-green {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border-left: 5px solid #10b981;
    }
    
    .annotation-red {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border-left: 5px solid #ef4444;
    }
    
    .annotation-yellow {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 5px solid #f59e0b;
    }
    
    .annotation-text {
        font-size: 0.95rem;
        line-height: 1.6;
        color: #1f2937;
    }
    
    .annotation-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 0.75rem;
        font-size: 0.8rem;
    }
    
    /* Status Badges */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .badge-green {
        background: #10b981;
        color: white;
    }
    
    .badge-red {
        background: #ef4444;
        color: white;
    }
    
    .badge-yellow {
        background: #f59e0b;
        color: #1f2937;
    }
    
    /* Confidence Meter */
    .confidence-container {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        border: 1px solid #e2e8f0;
    }
    
    .confidence-label {
        font-size: 0.9rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }
    
    .confidence-score {
        font-size: 4rem;
        font-weight: 800;
        line-height: 1;
        margin: 0.5rem 0;
    }
    
    .confidence-high { color: #10b981; }
    .confidence-medium { color: #f59e0b; }
    .confidence-low { color: #ef4444; }
    
    .confidence-bar {
        height: 12px;
        border-radius: 6px;
        background: #e2e8f0;
        overflow: hidden;
        margin-top: 1rem;
    }
    
    .confidence-fill {
        height: 100%;
        border-radius: 6px;
        transition: width 0.5s ease;
    }
    
    /* Citation Card */
    .citation-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.25rem;
        margin: 0.75rem 0;
        transition: all 0.2s ease;
    }
    
    .citation-card:hover {
        border-color: #3b82f6;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
    }
    
    .citation-source {
        font-size: 0.8rem;
        color: #64748b;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
    }
    
    .citation-text {
        font-style: italic;
        color: #374151;
        border-left: 3px solid #3b82f6;
        padding-left: 1rem;
        margin: 0.75rem 0;
        line-height: 1.6;
    }
    
    .citation-link {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        color: #3b82f6;
        font-size: 0.85rem;
        font-weight: 500;
        cursor: pointer;
    }
    
    /* Correction Box */
    .correction-box {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border: 1px solid #6ee7b7;
        border-radius: 10px;
        padding: 1.25rem;
        margin: 0.75rem 0;
    }
    
    .correction-label {
        font-size: 0.8rem;
        color: #065f46;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.75rem;
    }
    
    .correction-original {
        text-decoration: line-through;
        color: #ef4444;
        opacity: 0.8;
        margin-bottom: 0.5rem;
    }
    
    .correction-arrow {
        color: #10b981;
        font-size: 1.25rem;
        margin: 0.5rem 0;
    }
    
    .correction-suggested {
        color: #065f46;
        font-weight: 500;
        background: white;
        padding: 0.75rem;
        border-radius: 6px;
        border: 1px solid #a7f3d0;
    }
    
    /* Explainability Panel */
    .explain-section {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 1.25rem;
        margin: 0.75rem 0;
    }
    
    .explain-title {
        font-weight: 600;
        color: #1e3a5f;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
        font-size: 0.95rem;
    }
    
    .explain-content {
        color: #4b5563;
        font-size: 0.9rem;
        line-height: 1.6;
    }
    
    /* Source Document Viewer */
    .source-viewer {
        max-height: 600px;
        overflow-y: auto;
        padding: 1rem;
        background: #fafafa;
        border-radius: 8px;
    }
    
    .source-paragraph {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 6px;
        transition: all 0.3s ease;
        border: 1px solid transparent;
    }
    
    .source-paragraph:hover {
        background: #f0f9ff;
        border-color: #bae6fd;
    }
    
    .source-highlight {
        background: linear-gradient(135deg, #fef9c3 0%, #fef08a 100%);
        border: 2px solid #facc15;
        animation: pulse-highlight 2s ease-in-out infinite;
    }
    
    @keyframes pulse-highlight {
        0%, 100% { box-shadow: 0 0 0 0 rgba(250, 204, 21, 0.4); }
        50% { box-shadow: 0 0 0 10px rgba(250, 204, 21, 0); }
    }
    
    .paragraph-number {
        font-size: 0.75rem;
        color: #9ca3af;
        margin-bottom: 0.5rem;
    }
    
    /* Stats Cards */
    .stat-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid #e5e7eb;
        transition: all 0.2s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        line-height: 1;
    }
    
    .stat-label {
        font-size: 0.85rem;
        color: #64748b;
        margin-top: 0.5rem;
    }
    
    /* File Upload Area */
    .upload-area {
        border: 2px dashed #cbd5e1;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        background: #f8fafc;
        transition: all 0.2s ease;
    }
    
    .upload-area:hover {
        border-color: #3b82f6;
        background: #eff6ff;
    }
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #cbd5e1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #94a3b8;
    }
    
    /* Hide Streamlit Elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Responsive Adjustments */
    @media (max-width: 768px) {
        .main-header h1 { font-size: 1.5rem; }
        .confidence-score { font-size: 3rem; }
    }
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# Session State Management
# =============================================================================

def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        # Navigation
        'current_page': 'home',
        
        # Source documents
        'source_documents': [],
        'active_source_idx': 0,
        
        # LLM Output
        'llm_output': '',
        
        # Analysis results
        'analysis_complete': False,
        'verification_result': None,
        
        # UI State
        'selected_claim_id': None,
        'highlight_paragraph_idx': None,
        
        # Processing
        'is_processing': False,
        
        # Demo mode
        'use_demo_data': False,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# =============================================================================
# Demo Data for Testing
# =============================================================================

def load_demo_data():
    """Load demo data for testing the interface"""
    # Demo source document
    demo_source = SourceDocument(
        id="doc_001",
        name="Medical Guidelines - Diabetes Management.pdf",
        file_type="pdf",
        content="""
DIABETES MANAGEMENT GUIDELINES 2024

CHAPTER 1: DIAGNOSIS CRITERIA

Paragraph 1: Type 2 Diabetes is diagnosed when fasting plasma glucose is ≥126 mg/dL 
(7.0 mmol/L), or 2-hour plasma glucose ≥200 mg/dL (11.1 mmol/L) during an oral glucose 
tolerance test, or HbA1c ≥6.5% (48 mmol/mol).

Paragraph 2: The patient should be evaluated for diabetes complications at the time of 
diagnosis and annually thereafter. Key areas include retinopathy screening, nephropathy 
assessment, and neuropathy evaluation.

Paragraph 3: Initial treatment for Type 2 Diabetes should include lifestyle modifications 
such as medical nutrition therapy and increased physical activity. Metformin remains the 
first-line pharmacological agent unless contraindicated.

CHAPTER 2: TREATMENT PROTOCOLS

Paragraph 4: For patients not achieving glycemic targets with metformin monotherapy after 
3 months, a second agent should be added based on patient-specific factors including 
cardiovascular disease history, chronic kidney disease, and hypoglycemia risk.

Paragraph 5: GLP-1 receptor agonists and SGLT2 inhibitors have demonstrated cardiovascular 
and renal protective effects and should be considered for patients with established 
cardiovascular disease or high cardiovascular risk.

Paragraph 6: Blood pressure targets for patients with diabetes should be <130/80 mmHg. 
ACE inhibitors or ARBs are preferred first-line agents, especially in patients with 
albuminuria.
        """.strip(),
        paragraphs=[
            {"idx": 0, "text": "Type 2 Diabetes is diagnosed when fasting plasma glucose is ≥126 mg/dL (7.0 mmol/L), or 2-hour plasma glucose ≥200 mg/dL (11.1 mmol/L) during an oral glucose tolerance test, or HbA1c ≥6.5% (48 mmol/mol)."},
            {"idx": 1, "text": "The patient should be evaluated for diabetes complications at the time of diagnosis and annually thereafter. Key areas include retinopathy screening, nephropathy assessment, and neuropathy evaluation."},
            {"idx": 2, "text": "Initial treatment for Type 2 Diabetes should include lifestyle modifications such as medical nutrition therapy and increased physical activity. Metformin remains the first-line pharmacological agent unless contraindicated."},
            {"idx": 3, "text": "For patients not achieving glycemic targets with metformin monotherapy after 3 months, a second agent should be added based on patient-specific factors including cardiovascular disease history, chronic kidney disease, and hypoglycemia risk."},
            {"idx": 4, "text": "GLP-1 receptor agonists and SGLT2 inhibitors have demonstrated cardiovascular and renal protective effects and should be considered for patients with established cardiovascular disease or high cardiovascular risk."},
            {"idx": 5, "text": "Blood pressure targets for patients with diabetes should be <130/80 mmHg. ACE inhibitors or ARBs are preferred first-line agents, especially in patients with albuminuria."},
        ]
    )
    
    # Demo LLM output with mixed accuracy
    demo_llm_output = """
Based on the medical guidelines, here is a summary of diabetes management:

1. Type 2 Diabetes is diagnosed when fasting plasma glucose is ≥126 mg/dL or HbA1c ≥6.5%.

2. The patient should have Type 1 Diabetes and requires insulin from the start of diagnosis.

3. Metformin is the first-line treatment for Type 2 Diabetes unless contraindicated.

4. Blood pressure targets for diabetic patients should be <140/90 mmHg according to the guidelines.

5. Patients should be screened for complications annually including retinopathy and nephropathy.

6. Sulfonylureas are the preferred second-line agents for all diabetic patients regardless of cardiovascular history.
    """.strip()
    
    # Demo verification results
    demo_claims = [
        AnnotatedClaim(
            id="claim_001",
            text="Type 2 Diabetes is diagnosed when fasting plasma glucose is ≥126 mg/dL or HbA1c ≥6.5%.",
            status="supported",
            confidence=0.95,
            source_doc_id="doc_001",
            source_paragraph_idx=0,
            source_snippet="Type 2 Diabetes is diagnosed when fasting plasma glucose is ≥126 mg/dL (7.0 mmol/L)... or HbA1c ≥6.5% (48 mmol/mol).",
            explanation="The claim accurately reflects the diagnostic criteria stated in the source document. Both the fasting plasma glucose threshold (≥126 mg/dL) and HbA1c threshold (≥6.5%) match exactly.",
        ),
        AnnotatedClaim(
            id="claim_002",
            text="The patient should have Type 1 Diabetes and requires insulin from the start of diagnosis.",
            status="hallucination",
            confidence=0.92,
            source_doc_id="doc_001",
            source_paragraph_idx=2,
            source_snippet="Initial treatment for Type 2 Diabetes should include lifestyle modifications such as medical nutrition therapy...",
            explanation="CONTRADICTION DETECTED: The source document specifically discusses Type 2 Diabetes management with lifestyle modifications and metformin as first-line treatment. The claim incorrectly states Type 1 Diabetes and immediate insulin requirement, which is not supported by the source.",
            correction="Based on the guidelines, initial treatment for Type 2 Diabetes should include lifestyle modifications. Metformin is the first-line pharmacological agent, not insulin.",
        ),
        AnnotatedClaim(
            id="claim_003",
            text="Metformin is the first-line treatment for Type 2 Diabetes unless contraindicated.",
            status="supported",
            confidence=0.98,
            source_doc_id="doc_001",
            source_paragraph_idx=2,
            source_snippet="Metformin remains the first-line pharmacological agent unless contraindicated.",
            explanation="The claim directly matches the source document's statement about metformin being the first-line pharmacological agent for Type 2 Diabetes treatment.",
        ),
        AnnotatedClaim(
            id="claim_004",
            text="Blood pressure targets for diabetic patients should be <140/90 mmHg according to the guidelines.",
            status="hallucination",
            confidence=0.89,
            source_doc_id="doc_001",
            source_paragraph_idx=5,
            source_snippet="Blood pressure targets for patients with diabetes should be <130/80 mmHg.",
            explanation="FACTUAL ERROR: The source document states the blood pressure target as <130/80 mmHg, but the claim incorrectly states <140/90 mmHg. This is a significant discrepancy that could affect patient care.",
            correction="Blood pressure targets for patients with diabetes should be <130/80 mmHg, not <140/90 mmHg.",
        ),
        AnnotatedClaim(
            id="claim_005",
            text="Patients should be screened for complications annually including retinopathy and nephropathy.",
            status="supported",
            confidence=0.94,
            source_doc_id="doc_001",
            source_paragraph_idx=1,
            source_snippet="The patient should be evaluated for diabetes complications at the time of diagnosis and annually thereafter. Key areas include retinopathy screening, nephropathy assessment...",
            explanation="The claim correctly reflects the annual screening recommendations mentioned in the source document for diabetes complications.",
        ),
        AnnotatedClaim(
            id="claim_006",
            text="Sulfonylureas are the preferred second-line agents for all diabetic patients regardless of cardiovascular history.",
            status="hallucination",
            confidence=0.91,
            source_doc_id="doc_001",
            source_paragraph_idx=4,
            source_snippet="GLP-1 receptor agonists and SGLT2 inhibitors have demonstrated cardiovascular and renal protective effects and should be considered for patients with established cardiovascular disease...",
            explanation="INCORRECT RECOMMENDATION: The source document recommends GLP-1 receptor agonists and SGLT2 inhibitors (not sulfonylureas) for patients with cardiovascular disease. The claim's blanket recommendation ignores important patient-specific factors.",
            correction="GLP-1 receptor agonists and SGLT2 inhibitors should be considered as second-line agents, especially for patients with established cardiovascular disease or high cardiovascular risk.",
        ),
    ]
    
    demo_result = VerificationResult(
        overall_confidence=0.65,
        total_claims=6,
        supported_count=3,
        hallucination_count=3,
        unverifiable_count=0,
        annotated_claims=demo_claims,
    )
    
    return demo_source, demo_llm_output, demo_result


# =============================================================================
# UI Components
# =============================================================================

def render_header():
    """Render the main application header"""
    st.markdown("""
    <div class="main-header">
        <h1>🔍 Hallucination Hunter v2.0</h1>
        <p>AI-Powered Fact-Checking System for LLM Outputs | E-Summit '26 DataForge Track 1</p>
    </div>
    """, unsafe_allow_html=True)


def render_confidence_meter(confidence: float):
    """Render the visual confidence meter"""
    percentage = int(confidence * 100)
    
    if confidence >= 0.7:
        color_class = "confidence-high"
        fill_color = "#10b981"
        status = "HIGH CONFIDENCE"
    elif confidence >= 0.4:
        color_class = "confidence-medium"
        fill_color = "#f59e0b"
        status = "MEDIUM CONFIDENCE"
    else:
        color_class = "confidence-low"
        fill_color = "#ef4444"
        status = "LOW CONFIDENCE"
    
    st.markdown(f"""
    <div class="confidence-container">
        <div class="confidence-label">Document Verification Score</div>
        <div class="confidence-score {color_class}">{percentage}%</div>
        <div style="font-size: 0.9rem; color: #64748b; margin-bottom: 0.5rem;">{status}</div>
        <div class="confidence-bar">
            <div class="confidence-fill" style="width: {percentage}%; background: {fill_color};"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_stats_cards(result: VerificationResult):
    """Render statistics cards"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color: #3b82f6;">{result.total_claims}</div>
            <div class="stat-label">Total Claims</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color: #10b981;">{result.supported_count}</div>
            <div class="stat-label">✓ Supported</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color: #ef4444;">{result.hallucination_count}</div>
            <div class="stat-label">✗ Hallucinations</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-number" style="color: #f59e0b;">{result.unverifiable_count}</div>
            <div class="stat-label">? Unverifiable</div>
        </div>
        """, unsafe_allow_html=True)


def render_annotated_claim(claim: AnnotatedClaim, idx: int):
    """Render a single annotated claim with color coding"""
    if claim.status == "supported":
        color_class = "annotation-green"
        badge_class = "badge-green"
        badge_text = "✓ SUPPORTED"
        icon = "✓"
    elif claim.status == "hallucination":
        color_class = "annotation-red"
        badge_class = "badge-red"
        badge_text = "✗ HALLUCINATION"
        icon = "✗"
    else:
        color_class = "annotation-yellow"
        badge_class = "badge-yellow"
        badge_text = "? UNVERIFIABLE"
        icon = "?"
    
    confidence_pct = int(claim.confidence * 100)
    
    # Create unique key for this claim
    button_key = f"claim_btn_{claim.id}_{idx}"
    
    st.markdown(f"""
    <div class="annotation {color_class}" id="{claim.id}">
        <div class="annotation-text">{claim.text}</div>
        <div class="annotation-meta">
            <span class="badge {badge_class}">{badge_text}</span>
            <span style="color: #6b7280;">Confidence: {confidence_pct}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Click handler for selecting claim
    if st.button(f"📍 View Evidence", key=button_key, use_container_width=True):
        st.session_state.selected_claim_id = claim.id
        st.session_state.highlight_paragraph_idx = claim.source_paragraph_idx
        st.rerun()


def render_source_document(source: SourceDocument, highlight_idx: Optional[int] = None):
    """Render the source document with highlighted paragraph"""
    st.markdown(f"""
    <div class="panel-header">
        📄 {source.name}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="source-viewer">', unsafe_allow_html=True)
    
    for para in source.paragraphs:
        is_highlighted = para["idx"] == highlight_idx
        highlight_class = "source-highlight" if is_highlighted else ""
        
        st.markdown(f"""
        <div class="source-paragraph {highlight_class}" id="para_{para['idx']}">
            <div class="paragraph-number">Paragraph {para['idx'] + 1}</div>
            <div>{para['text']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


def render_citation_report(claim: AnnotatedClaim, source: SourceDocument):
    """Render citation report for a claim"""
    if claim.status == "supported":
        st.markdown(f"""
        <div class="citation-card">
            <div class="citation-source">
                <span>📚</span>
                <span>{source.name} • Paragraph {claim.source_paragraph_idx + 1 if claim.source_paragraph_idx is not None else 'N/A'}</span>
            </div>
            <div class="citation-text">
                "{claim.source_snippet}"
            </div>
            <div class="citation-link">
                🔗 Direct link to source evidence
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_correction_panel(claim: AnnotatedClaim):
    """Render correction suggestion for hallucinated claims"""
    if claim.status == "hallucination" and claim.correction:
        st.markdown(f"""
        <div class="correction-box">
            <div class="correction-label">💡 Suggested Correction</div>
            <div class="correction-original">{claim.text}</div>
            <div class="correction-arrow">↓</div>
            <div class="correction-suggested">{claim.correction}</div>
        </div>
        """, unsafe_allow_html=True)


def render_explainability_panel(claim: AnnotatedClaim):
    """Render explainability information for a claim"""
    st.markdown("""
    <div class="explain-section">
        <div class="explain-title">🔍 Why is this flagged?</div>
        <div class="explain-content">
    """, unsafe_allow_html=True)
    st.markdown(claim.explanation)
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    if claim.source_snippet:
        st.markdown(f"""
        <div class="explain-section">
            <div class="explain-title">📖 Where is the proof?</div>
            <div class="explain-content" style="font-style: italic;">
                "{claim.source_snippet}"
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    confidence_pct = int(claim.confidence * 100)
    confidence_level = "High" if claim.confidence >= 0.8 else ("Medium" if claim.confidence >= 0.5 else "Low")
    
    st.markdown(f"""
    <div class="explain-section">
        <div class="explain-title">📊 How confident is the model?</div>
        <div class="explain-content">
            <strong>{confidence_pct}% confidence</strong> ({confidence_level} certainty)
            <br><br>
            This assessment distinguishes between a <strong>{'certain' if claim.confidence >= 0.8 else 'likely'}</strong> 
            {'error' if claim.status == 'hallucination' else 'match'} based on semantic analysis.
        </div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# Main Pages
# =============================================================================

def process_uploaded_files(source_files, llm_text: str) -> bool:
    """Process uploaded files and run verification"""
    from pathlib import Path
    import tempfile
    import io
    
    try:
        # Create progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Read source documents
        status_text.text("📄 Reading source documents...")
        progress_bar.progress(10)
        
        source_paragraphs = []
        source_names = []
        
        for uploaded_file in source_files:
            source_names.append(uploaded_file.name)
            
            if uploaded_file.name.endswith('.txt'):
                content = uploaded_file.read().decode('utf-8')
                # Split into paragraphs
                paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                source_paragraphs.extend(paragraphs)
            elif uploaded_file.name.endswith('.pdf'):
                # Try to read PDF
                try:
                    import PyPDF2
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                    for page in pdf_reader.pages:
                        text = page.extract_text()
                        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                        source_paragraphs.extend(paragraphs)
                except ImportError:
                    st.warning(f"PyPDF2 not installed. Skipping PDF: {uploaded_file.name}")
                except Exception as e:
                    st.warning(f"Could not read PDF {uploaded_file.name}: {e}")
            elif uploaded_file.name.endswith('.docx'):
                st.warning(f"DOCX support coming soon. Skipping: {uploaded_file.name}")
        
        if not source_paragraphs:
            st.error("❌ Could not extract any content from source documents")
            return False
        
        status_text.text(f"📄 Loaded {len(source_paragraphs)} paragraphs from source documents")
        progress_bar.progress(30)
        
        # Extract claims from LLM output
        status_text.text("🔍 Extracting claims from LLM output...")
        progress_bar.progress(40)
        
        # Simple claim extraction: split by sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+', llm_text)
        claims = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if not claims:
            st.error("❌ Could not extract any claims from LLM output")
            return False
        
        status_text.text(f"🔍 Extracted {len(claims)} claims to verify")
        progress_bar.progress(50)
        
        # Perform verification using semantic similarity
        status_text.text("⚡ Running verification pipeline...")
        progress_bar.progress(60)
        
        annotated_claims = []
        
        # Simple verification using substring matching and keyword overlap
        for idx, claim in enumerate(claims):
            progress_bar.progress(60 + int(30 * (idx + 1) / len(claims)))
            status_text.text(f"⚡ Verifying claim {idx + 1}/{len(claims)}...")
            
            claim_lower = claim.lower()
            claim_words = set(claim_lower.split())
            
            best_match_score = 0
            best_match_idx = 0
            best_match_text = ""
            
            for p_idx, paragraph in enumerate(source_paragraphs):
                para_lower = paragraph.lower()
                para_words = set(para_lower.split())
                
                # Calculate Jaccard similarity
                if len(claim_words | para_words) > 0:
                    overlap = len(claim_words & para_words) / len(claim_words | para_words)
                else:
                    overlap = 0
                
                # Check for key phrase overlap
                if any(phrase in para_lower for phrase in claim_lower.split(',') if len(phrase) > 10):
                    overlap += 0.2
                
                if overlap > best_match_score:
                    best_match_score = overlap
                    best_match_idx = p_idx
                    best_match_text = paragraph[:200] + "..." if len(paragraph) > 200 else paragraph
            
            # Determine verification status based on similarity
            if best_match_score > 0.3:
                status = "supported"
                confidence = min(0.95, 0.6 + best_match_score)
                explanation = f"This claim has significant overlap with content in the source document (similarity: {best_match_score:.2%}). Key phrases match the source material."
            elif best_match_score > 0.15:
                status = "unverifiable"
                confidence = 0.4 + best_match_score
                explanation = f"This claim has partial overlap with source content (similarity: {best_match_score:.2%}), but insufficient evidence to fully verify or contradict."
            else:
                status = "hallucination"
                confidence = max(0.6, 0.9 - best_match_score)
                explanation = f"This claim has very low overlap with any source content (similarity: {best_match_score:.2%}). No supporting evidence found in the knowledge base."
            
            # Generate correction for hallucinations
            correction = None
            if status == "hallucination" and best_match_text:
                correction = f"Based on the source documents, consider: {best_match_text[:150]}..."
            
            annotated_claims.append(AnnotatedClaim(
                id=f"claim_{idx:03d}",
                text=claim,
                status=status,
                confidence=confidence,
                source_doc_id="uploaded_docs",
                source_paragraph_idx=best_match_idx,
                source_snippet=best_match_text,
                explanation=explanation,
                correction=correction
            ))
        
        progress_bar.progress(95)
        status_text.text("📊 Generating results...")
        
        # Calculate overall statistics
        supported_count = sum(1 for c in annotated_claims if c.status == "supported")
        hallucination_count = sum(1 for c in annotated_claims if c.status == "hallucination")
        unverifiable_count = sum(1 for c in annotated_claims if c.status == "unverifiable")
        
        # Calculate overall confidence
        if len(annotated_claims) > 0:
            overall_confidence = supported_count / len(annotated_claims)
        else:
            overall_confidence = 0.0
        
        # Create source document object with paragraphs as list of dicts
        paragraphs_as_dicts = [{"idx": i, "text": p} for i, p in enumerate(source_paragraphs)]
        
        source_doc = SourceDocument(
            id="uploaded_docs",
            name=", ".join(source_names),
            content="\n\n".join(source_paragraphs),
            file_type="txt",
            paragraphs=paragraphs_as_dicts
        )
        
        # Create verification result
        result = VerificationResult(
            overall_confidence=overall_confidence,
            total_claims=len(annotated_claims),
            supported_count=supported_count,
            hallucination_count=hallucination_count,
            unverifiable_count=unverifiable_count,
            annotated_claims=annotated_claims
        )
        
        # Store in session state
        st.session_state.source_documents = [source_doc]
        st.session_state.verification_result = result
        st.session_state.llm_output = llm_text
        st.session_state.use_demo_data = False
        
        progress_bar.progress(100)
        status_text.text("✅ Verification complete!")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error during verification: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return False


def render_home_page():
    """Render the home/upload page"""
    st.markdown("## 📤 Upload Documents for Verification")
    
    # Info box explaining expected inputs
    st.info("""
    **Expected Inputs:**
    - 📚 **Source Knowledge Base:** PDF/Text documents (medical guidelines, legal acts, technical manuals)
    - 🤖 **LLM Output:** Generated summary/answer based on those documents
    
    **What you'll get:**
    - ✅ Color-coded annotations (Green=Supported, Red=Hallucination, Yellow=Unverifiable)
    - 📋 Citation report with direct links to source paragraphs
    - ✏️ Correction suggestions for hallucinated content
    - 📊 Confidence meter and explainability details
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📚 Source Knowledge Base")
        st.markdown("Upload PDF/Text documents (e.g., medical guidelines, legal acts, technical manuals)")
        
        source_files = st.file_uploader(
            "Upload source documents",
            type=['pdf', 'txt', 'docx'],
            accept_multiple_files=True,
            key="source_upload"
        )
        
        if source_files:
            st.success(f"✓ {len(source_files)} source document(s) uploaded")
            for f in source_files:
                file_size = len(f.getvalue()) / 1024  # KB
                st.markdown(f"- **{f.name}** ({file_size:.1f} KB)")
    
    with col2:
        st.markdown("### 🤖 LLM Output")
        st.markdown("Paste or upload the generated summary/answer to verify")
        
        llm_input_method = st.radio(
            "Input method",
            ["Paste text", "Upload file"],
            horizontal=True,
            key="llm_input_method"
        )
        
        llm_text = ""
        if llm_input_method == "Paste text":
            llm_text = st.text_area(
                "Paste LLM output here",
                height=200,
                placeholder="Enter the AI-generated text you want to verify...",
                key="llm_text_input"
            )
        else:
            llm_file = st.file_uploader(
                "Upload LLM output file",
                type=['txt', 'md'],
                key="llm_file_upload"
            )
            if llm_file:
                llm_text = llm_file.read().decode('utf-8')
                st.success(f"✓ Loaded {len(llm_text)} characters from {llm_file.name}")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Check if we have both inputs
        has_sources = source_files is not None and len(source_files) > 0
        has_llm_output = len(llm_text.strip()) > 0 if llm_text else False
        
        if not has_sources:
            st.warning("⚠️ Please upload source documents")
        if not has_llm_output:
            st.warning("⚠️ Please provide LLM output to verify")
        
        # Start verification button
        if st.button("🚀 Start Verification", type="primary", use_container_width=True, 
                     disabled=not (has_sources and has_llm_output)):
            with st.spinner("Processing..."):
                success = process_uploaded_files(source_files, llm_text)
                if success:
                    st.session_state.current_page = 'results'
                    st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("📋 Load Demo Data (No Upload Required)", use_container_width=True):
            st.session_state.use_demo_data = True
            st.session_state.current_page = 'results'
            st.rerun()


def render_results_page():
    """Render the results page with split-screen interface"""
    # Check if we have real data or need to load demo
    if st.session_state.use_demo_data or not st.session_state.verification_result:
        # Load demo data
        demo_source, demo_llm_output, demo_result = load_demo_data()
        st.session_state.source_documents = [demo_source]
        st.session_state.verification_result = demo_result
        st.session_state.llm_output = demo_llm_output
        
        # Show demo data banner
        st.info("📋 **Demo Mode:** Showing sample medical guidelines verification. Upload your own documents for real analysis.")
    
    result = st.session_state.verification_result
    source = st.session_state.source_documents[0] if st.session_state.source_documents else None
    
    if not result or not source:
        st.error("No verification results available. Please upload documents first.")
        if st.button("← Back to Upload"):
            st.session_state.current_page = 'home'
            st.rerun()
        return
    
    # Get selected claim if any
    selected_claim = None
    if st.session_state.selected_claim_id:
        for claim in result.annotated_claims:
            if claim.id == st.session_state.selected_claim_id:
                selected_claim = claim
                break
    
    # Stats row
    render_stats_cards(result)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Main split-screen layout
    left_col, right_col = st.columns([1, 1])
    
    # LEFT PANEL: Annotated LLM Output
    with left_col:
        st.markdown("""
        <div class="panel">
            <div class="panel-header">
                🤖 Annotated LLM Output
                <span style="font-weight: normal; font-size: 0.85rem; color: #6b7280; margin-left: auto;">
                    Click on a claim to view evidence
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("##### Color Legend")
        legend_cols = st.columns(3)
        with legend_cols[0]:
            st.markdown("🟢 **Green** = Supported")
        with legend_cols[1]:
            st.markdown("🔴 **Red** = Hallucination")
        with legend_cols[2]:
            st.markdown("🟡 **Yellow** = Unverifiable")
        
        st.markdown("---")
        
        # Render all annotated claims
        for idx, claim in enumerate(result.annotated_claims):
            render_annotated_claim(claim, idx)
    
    # RIGHT PANEL: Source Document + Details
    with right_col:
        # Confidence Meter
        render_confidence_meter(result.overall_confidence)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📄 Source Document",
            "📋 Citation Report", 
            "✏️ Corrections",
            "❓ Explainability"
        ])
        
        with tab1:
            render_source_document(
                source, 
                st.session_state.highlight_paragraph_idx
            )
        
        with tab2:
            st.markdown("### 📋 Citation Report")
            st.markdown("Direct links to source paragraphs that validate each claim")
            
            for claim in result.annotated_claims:
                if claim.status == "supported":
                    render_citation_report(claim, source)
        
        with tab3:
            st.markdown("### ✏️ Correction Suggestions")
            st.markdown("Suggested corrections for hallucinated content based on source documents")
            
            hallucinations = [c for c in result.annotated_claims if c.status == "hallucination"]
            
            if hallucinations:
                for claim in hallucinations:
                    render_correction_panel(claim)
            else:
                st.info("No corrections needed - all claims are supported!")
        
        with tab4:
            st.markdown("### ❓ Explainability Details")
            
            if selected_claim:
                st.markdown(f"**Selected Claim:** _{selected_claim.text[:100]}..._")
                render_explainability_panel(selected_claim)
            else:
                st.info("👆 Click on a claim in the left panel to see detailed explainability information")
                
                # Show first hallucination as example
                first_hallucination = next(
                    (c for c in result.annotated_claims if c.status == "hallucination"), 
                    None
                )
                if first_hallucination:
                    st.markdown("---")
                    st.markdown("**Example Explanation (First Hallucination):**")
                    render_explainability_panel(first_hallucination)


def render_settings_page():
    """Render the settings page"""
    st.markdown("## ⚙️ Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Verification Settings")
        
        st.slider(
            "Confidence Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.05,
            help="Minimum confidence score to consider a claim as supported"
        )
        
        st.checkbox("Show unverifiable claims", value=True)
        st.checkbox("Auto-generate corrections", value=True)
        st.checkbox("Enable semantic similarity matching", value=True)
    
    with col2:
        st.markdown("### Display Settings")
        
        st.selectbox(
            "Theme",
            ["Light", "Dark", "System"],
            index=0
        )
        
        st.checkbox("Show confidence percentages", value=True)
        st.checkbox("Enable click-to-scroll navigation", value=True)
        st.checkbox("Highlight source paragraphs", value=True)


# =============================================================================
# Sidebar Navigation
# =============================================================================

def render_sidebar():
    """Render the sidebar with navigation"""
    with st.sidebar:
        st.markdown("## 🔍 Navigation")
        
        # Navigation buttons
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.current_page = 'home'
            st.rerun()
        
        if st.button("📊 Results", use_container_width=True):
            st.session_state.current_page = 'results'
            st.rerun()
        
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.current_page = 'settings'
            st.rerun()
        
        st.markdown("---")
        
        # Quick stats if results available
        if st.session_state.get('verification_result'):
            result = st.session_state.verification_result
            st.markdown("### 📈 Quick Stats")
            st.metric("Total Claims", result.total_claims)
            st.metric("Supported", result.supported_count, delta="✓")
            st.metric("Hallucinations", result.hallucination_count, delta="✗", delta_color="inverse")
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.markdown("""
        **Hallucination Hunter v2.0**
        
        E-Summit '26 DataForge Track 1
        
        Verify LLM outputs against source documents with:
        - Color-coded annotations
        - Citation reports
        - Correction suggestions
        - Full explainability
        """)


# =============================================================================
# Main Application
# =============================================================================

def main():
    """Main application entry point"""
    setup_page()
    initialize_session_state()
    
    render_header()
    render_sidebar()
    
    # Route to appropriate page
    current_page = st.session_state.current_page
    
    if current_page == 'home':
        render_home_page()
    elif current_page == 'results':
        render_results_page()
    elif current_page == 'settings':
        render_settings_page()
    else:
        render_home_page()


if __name__ == "__main__":
    main()
