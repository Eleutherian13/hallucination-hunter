"""
Audit API endpoints
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import base64
import uuid
import json

from src.layers.ui_integration import UIIntegrationLayer, AuditRequest, get_integration_layer
from src.layers.correction import AuditReport
from src.config.constants import Domain, ExportFormat, ClaimCategory
from src.utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


# Request/Response Models
class DocumentInput(BaseModel):
    """Document input for API"""
    name: str
    content: str
    doc_type: str = "txt"


class AuditRequestModel(BaseModel):
    """Audit request body"""
    llm_output: str = Field(..., min_length=10, description="LLM output to verify")
    documents: List[DocumentInput] = Field(..., description="Source documents")
    domain: str = Field(default="general", description="Domain for verification")
    run_drift_check: bool = Field(default=False, description="Run drift analysis")
    regenerated_outputs: Optional[List[str]] = Field(default=None, description="Regenerated outputs for drift")
    generate_corrections: bool = Field(default=True, description="Generate corrections")


class ClaimResponse(BaseModel):
    """Individual claim response"""
    claim_id: str
    text: str
    category: str
    confidence: float
    citation: str
    explanation: str
    correction: Optional[str] = None


class AuditResponseModel(BaseModel):
    """Audit response"""
    report_id: str
    timestamp: str
    trust_score: float
    trust_level: str
    total_claims: int
    supported: int
    contradicted: int
    unverifiable: int
    claims: List[ClaimResponse]
    recommendations: List[str]
    summary: str


class QuickCheckRequest(BaseModel):
    """Quick single-claim check request"""
    claim: str
    context: str


class QuickCheckResponse(BaseModel):
    """Quick check response"""
    claim: str
    category: str
    confidence: float
    explanation: str


# In-memory report storage (use proper database in production)
_reports: Dict[str, AuditReport] = {}


@router.post("/audit", response_model=AuditResponseModel)
async def run_audit(request: AuditRequestModel):
    """
    Run full audit on LLM output
    
    Verifies claims in the LLM output against provided source documents.
    """
    try:
        logger.info(f"Starting audit with {len(request.documents)} documents")
        
        # Convert domain
        try:
            domain = Domain(request.domain.lower())
        except ValueError:
            domain = Domain.GENERAL
        
        # Prepare sources
        sources = [
            {
                "name": doc.name,
                "content": doc.content,
                "type": doc.doc_type
            }
            for doc in request.documents
        ]
        
        # Create audit request
        audit_request = AuditRequest(
            sources=sources,
            llm_output=request.llm_output,
            domain=domain,
            run_drift_check=request.run_drift_check,
            regenerated_outputs=request.regenerated_outputs,
            generate_corrections=request.generate_corrections
        )
        
        # Run audit
        integration = get_integration_layer()
        report = await integration.run_audit_async(audit_request)
        
        # Store report
        _reports[report.report_id] = report
        
        # Format response
        claims = []
        for ac in report.annotated_claims:
            claims.append(ClaimResponse(
                claim_id=ac.claim.claim_id,
                text=ac.claim.text,
                category=ac.verification.category.value,
                confidence=ac.verification.confidence,
                citation=ac.verification.citation,
                explanation=ac.verification.explanation,
                correction=ac.correction.corrected_claim if ac.correction else None
            ))
        
        stats = report.to_dict()["statistics"]
        
        return AuditResponseModel(
            report_id=report.report_id,
            timestamp=report.timestamp.isoformat(),
            trust_score=report.trust_score.score,
            trust_level=report.trust_score.level.value,
            total_claims=stats["total_claims"],
            supported=stats["supported"],
            contradicted=stats["contradicted"],
            unverifiable=stats["unverifiable"],
            claims=claims,
            recommendations=report.trust_score.recommendations,
            summary=report.summary
        )
        
    except Exception as e:
        logger.error(f"Audit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit/upload")
async def run_audit_with_files(
    llm_output: str = Form(...),
    domain: str = Form(default="general"),
    files: List[UploadFile] = File(...)
):
    """
    Run audit with file uploads
    
    Alternative endpoint that accepts file uploads instead of content strings.
    """
    try:
        # Read file contents
        sources = []
        for file in files:
            content = await file.read()
            filename = file.filename or "unnamed_file.txt"
            file_ext = filename.split(".")[-1] if "." in filename else "txt"
            sources.append({
                "name": filename,
                "content": content,
                "type": file_ext
            })
        
        try:
            domain_enum = Domain(domain.lower())
        except ValueError:
            domain_enum = Domain.GENERAL
        
        audit_request = AuditRequest(
            sources=sources,
            llm_output=llm_output,
            domain=domain_enum
        )
        
        integration = get_integration_layer()
        report = await integration.run_audit_async(audit_request)
        
        _reports[report.report_id] = report
        
        return integration.correction.format_api_response(report)
        
    except Exception as e:
        logger.error(f"Upload audit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/{report_id}")
async def get_report(report_id: str):
    """
    Get existing audit report by ID
    """
    if report_id not in _reports:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = _reports[report_id]
    integration = get_integration_layer()
    return integration.correction.format_api_response(report)


@router.get("/audit/{report_id}/export/{format}")
async def export_report(report_id: str, format: str):
    """
    Export report in specified format
    
    Supported formats: json, html, csv, pdf
    """
    if report_id not in _reports:
        raise HTTPException(status_code=404, detail="Report not found")
    
    try:
        export_format = ExportFormat(format.lower())
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid format. Supported: {[f.value for f in ExportFormat]}"
        )
    
    report = _reports[report_id]
    integration = get_integration_layer()
    content = integration.export_report(report, export_format)
    
    if export_format == ExportFormat.PDF:
        if isinstance(content, bytes):
            content_bytes = content
        elif isinstance(content, str):
            content_bytes = content.encode('utf-8')
        else:
            content_bytes = str(content).encode('utf-8')
        return {
            "format": "pdf",
            "content_base64": base64.b64encode(content_bytes).decode()
        }
    
    return {
        "format": format,
        "content": content
    }


@router.post("/audit/quick-check", response_model=QuickCheckResponse)
async def quick_check(request: QuickCheckRequest):
    """
    Quick verification of a single claim against context
    
    Lightweight endpoint for single claim verification without full report generation.
    """
    try:
        from src.models.nli_model import NLIModel
        from src.config.constants import ClaimCategory
        
        nli_model = NLIModel()
        result = nli_model.classify(
            claim=request.claim,
            evidence=request.context
        )
        
        category_map = {
            ClaimCategory.SUPPORTED: "supported",
            ClaimCategory.CONTRADICTED: "contradicted",
            ClaimCategory.UNVERIFIABLE: "unverifiable"
        }
        
        category = category_map.get(result.category, "unverifiable")
        
        explanations = {
            "supported": "The claim is supported by the provided context.",
            "contradicted": "The claim contradicts information in the provided context.",
            "unverifiable": "The claim cannot be verified from the provided context."
        }
        
        return QuickCheckResponse(
            claim=request.claim,
            category=category,
            confidence=result.confidence,
            explanation=explanations[category]
        )
        
    except Exception as e:
        logger.error(f"Quick check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/{report_id}/claim/{claim_id}")
async def get_claim_details(report_id: str, claim_id: str):
    """
    Get detailed information for a specific claim
    """
    if report_id not in _reports:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = _reports[report_id]
    integration = get_integration_layer()
    
    details = integration.get_claim_details(claim_id, report.annotated_claims)
    
    if not details:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    return details


@router.post("/audit/{report_id}/claim/{claim_id}/feedback")
async def submit_feedback(
    report_id: str,
    claim_id: str,
    new_category: str = Form(...),
    notes: Optional[str] = Form(default=None)
):
    """
    Submit user feedback on a claim verification
    """
    if report_id not in _reports:
        raise HTTPException(status_code=404, detail="Report not found")
    
    try:
        category = ClaimCategory(new_category.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Options: {[c.value for c in ClaimCategory]}"
        )
    
    integration = get_integration_layer()
    integration.update_claim_feedback(claim_id, category, notes)
    
    return {"status": "feedback_recorded", "claim_id": claim_id}


@router.get("/reports")
async def list_reports(limit: int = 10, offset: int = 0):
    """
    List all available reports
    """
    report_list = []
    for rid, report in list(_reports.items())[offset:offset+limit]:
        report_list.append({
            "report_id": rid,
            "timestamp": report.timestamp.isoformat(),
            "trust_score": report.trust_score.score,
            "total_claims": len(report.annotated_claims)
        })
    
    return {
        "total": len(_reports),
        "limit": limit,
        "offset": offset,
        "reports": report_list
    }
