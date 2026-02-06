"""
Layer 8: UI & API Integration Layer
Provides interfaces for Streamlit UI and FastAPI endpoints
"""

from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import asyncio
from datetime import datetime

from src.layers.ingestion import IngestionLayer, DocumentIndex
from src.layers.claim_intelligence import ClaimIntelligenceLayer, Claim
from src.layers.retrieval import RetrievalLayer, EvidenceResult
from src.layers.verification import VerificationLayer, VerificationResult
from src.layers.drift import DriftMitigationLayer, DriftAdjustedResult
from src.layers.scoring import ScoringLayer, TrustScore
from src.layers.correction import CorrectionLayer, AuditReport, AnnotatedClaim
from src.config.constants import Domain, ExportFormat, ClaimCategory
from src.config.settings import get_settings
from src.utils.logging_config import get_logger, get_audit_logger
from src.models.embedding_model import EmbeddingModel
from src.models.nli_model import NLIModel

logger = get_logger(__name__)


@dataclass
class AuditRequest:
    """Request for audit operation"""
    sources: List[Dict]  # [{path, content, name, type}]
    llm_output: str
    domain: Domain = Domain.GENERAL
    run_drift_check: bool = False
    regenerated_outputs: Optional[List[str]] = None
    generate_corrections: bool = True
    
    def validate(self) -> bool:
        if not self.sources:
            return False
        if not self.llm_output or len(self.llm_output) < 10:
            return False
        return True


@dataclass
class AuditProgress:
    """Progress tracking for audit operation"""
    stage: str
    progress: float
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "stage": self.stage,
            "progress": self.progress,
            "message": self.message,
            "timestamp": self.timestamp.isoformat()
        }


class UIIntegrationLayer:
    """
    Layer 8: UI & API Integration
    
    Responsibilities:
    - Orchestrate all layers for complete audit pipeline
    - Provide progress callbacks for UI
    - Handle async operations for API
    - Manage caching and session state
    - Format outputs for different consumers
    """
    
    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        nli_model: Optional[NLIModel] = None
    ):
        """
        Initialize UI integration layer with shared models
        
        Args:
            embedding_model: Shared embedding model
            nli_model: Shared NLI model
        """
        # Initialize shared models
        self.embedding_model = embedding_model or EmbeddingModel()
        self.nli_model = nli_model or NLIModel()
        
        # Initialize layers
        self.ingestion = IngestionLayer(embedding_model=self.embedding_model)
        self.claim_intelligence = ClaimIntelligenceLayer()
        self.retrieval = RetrievalLayer(embedding_model=self.embedding_model)
        self.verification = VerificationLayer(nli_model=self.nli_model)
        self.drift = DriftMitigationLayer()
        self.scoring = ScoringLayer()
        self.correction = CorrectionLayer()
        
        # State
        self._current_index: Optional[DocumentIndex] = None
        self._progress_callback: Optional[Callable] = None
        
        logger.info("UI Integration Layer initialized")
    
    def set_progress_callback(self, callback: Callable[[AuditProgress], None]) -> None:
        """Set callback for progress updates"""
        self._progress_callback = callback
    
    def _report_progress(self, stage: str, progress: float, message: str) -> None:
        """Report progress to callback"""
        if self._progress_callback:
            self._progress_callback(AuditProgress(stage, progress, message))
    
    def run_audit(
        self,
        request: AuditRequest
    ) -> AuditReport:
        """
        Run complete audit pipeline
        
        Args:
            request: Audit request with sources and LLM output
        
        Returns:
            Complete AuditReport
        """
        audit_logger = get_audit_logger()
        start_time = datetime.now()
        
        try:
            # Stage 1: Document Ingestion
            self._report_progress("ingestion", 0.1, "Processing source documents...")
            doc_index = self.ingestion.process_documents(request.sources)
            self._current_index = doc_index
            self._report_progress("ingestion", 0.2, f"Indexed {doc_index.total_chunks} chunks from {doc_index.total_documents} documents")
            
            # Stage 2: Claim Extraction
            self._report_progress("claims", 0.25, "Extracting claims from LLM output...")
            self.claim_intelligence.set_domain(request.domain)
            claims = self.claim_intelligence.extract_claims(request.llm_output)
            self._report_progress("claims", 0.35, f"Extracted {len(claims)} claims")
            
            audit_logger.log_verification_start(
                document_id=doc_index.index_id,
                claim_count=len(claims)
            )
            
            # Stage 3: Evidence Retrieval
            self._report_progress("retrieval", 0.4, "Retrieving evidence for claims...")
            evidences = self.retrieval.retrieve_evidence_batch(
                claims,
                doc_index,
                method="hybrid"
            )
            self._report_progress("retrieval", 0.5, "Evidence retrieval complete")
            
            # Stage 4: Verification
            self._report_progress("verification", 0.55, "Verifying claims against evidence...")
            self.verification.set_domain(request.domain)
            verification_results = self.verification.verify_claims_batch(claims, evidences)
            self._report_progress("verification", 0.7, "Verification complete")
            
            # Stage 5: Drift Check (optional)
            drift_adjusted: Optional[List[DriftAdjustedResult]] = None
            if request.run_drift_check and request.regenerated_outputs:
                self._report_progress("drift", 0.75, "Analyzing output drift...")
                drift_report = self.drift.analyze_drift(
                    request.llm_output,
                    request.regenerated_outputs
                )
                drift_adjusted = self.drift.adjust_verification_results(
                    verification_results,
                    drift_report
                )
                self._report_progress("drift", 0.8, f"Drift analysis complete: {drift_report.overall_drift_score:.2f}")
            
            # Stage 6: Scoring
            self._report_progress("scoring", 0.85, "Calculating trust score...")
            trust_score = self.scoring.calculate_trust_score(
                verification_results,
                drift_adjusted,
                claims
            )
            self._report_progress("scoring", 0.9, f"Trust score: {trust_score.score}/100")
            
            # Stage 7: Corrections
            corrections = {}
            if request.generate_corrections:
                self._report_progress("correction", 0.92, "Generating corrections...")
                corrections = self.correction.generate_corrections(verification_results)
            
            # Stage 8: Create Report
            self._report_progress("report", 0.95, "Generating report...")
            annotated_claims = self.correction.create_annotated_claims(
                claims,
                verification_results,
                corrections
            )
            
            document_sources = [
                doc.metadata.filename
                for doc in doc_index.documents.values()
            ]
            
            report = self.correction.create_audit_report(
                llm_output=request.llm_output,
                trust_score=trust_score,
                annotated_claims=annotated_claims,
                document_sources=document_sources
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            audit_logger.log_verification_complete(
                document_id=doc_index.index_id,
                trust_score=trust_score.score,
                duration_seconds=duration
            )
            
            self._report_progress("complete", 1.0, f"Audit complete in {duration:.2f}s")
            
            return report
            
        except Exception as e:
            logger.error(f"Audit failed: {e}")
            audit_logger.log_error(
                document_id=self._current_index.index_id if self._current_index else "unknown",
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise
    
    async def run_audit_async(
        self,
        request: AuditRequest
    ) -> AuditReport:
        """
        Async version of run_audit for API use
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.run_audit, request)
    
    def get_annotated_text_html(
        self,
        llm_output: str,
        annotated_claims: List[AnnotatedClaim]
    ) -> str:
        """
        Generate HTML with color-annotated text
        
        Args:
            llm_output: Original LLM output
            annotated_claims: List of annotated claims
        
        Returns:
            HTML string with highlighted claims
        """
        # Sort claims by position (if available)
        sorted_claims = sorted(
            annotated_claims,
            key=lambda c: c.claim.source_start,
            reverse=True
        )
        
        result = llm_output
        
        for ac in sorted_claims:
            claim_text = ac.claim.text
            color = ac.color
            category = ac.verification.category.value
            confidence = ac.verification.confidence
            
            # Create highlighted span
            tooltip = f"{category.title()} ({confidence:.0%})"
            highlighted = f'<span class="claim-highlight {category}" style="background-color: {color}20; border-bottom: 2px solid {color}; cursor: pointer;" title="{tooltip}" data-claim-id="{ac.claim.claim_id}">{claim_text}</span>'
            
            # Replace in text (be careful with overlapping)
            result = result.replace(claim_text, highlighted, 1)
        
        return result
    
    def export_report(
        self,
        report: AuditReport,
        format: ExportFormat,
        output_path: Optional[Union[str, Path]] = None
    ) -> Union[str, bytes]:
        """
        Export report in specified format
        
        Args:
            report: Audit report
            format: Export format
            output_path: Optional output file path
        
        Returns:
            Exported content
        """
        return self.correction.export(report, format, output_path)
    
    def get_claim_details(
        self,
        claim_id: str,
        annotated_claims: List[AnnotatedClaim]
    ) -> Optional[Dict]:
        """
        Get detailed information for a specific claim
        
        Args:
            claim_id: Claim identifier
            annotated_claims: List of annotated claims
        
        Returns:
            Detailed claim information
        """
        for ac in annotated_claims:
            if ac.claim.claim_id == claim_id:
                return {
                    "claim": ac.claim.to_dict(),
                    "verification": ac.verification.to_dict(),
                    "correction": ac.correction.to_dict() if ac.correction else None,
                    "color": ac.color,
                    "evidence": {
                        "text": ac.verification.evidence_used,
                        "citation": ac.verification.citation
                    }
                }
        return None
    
    def get_evidence_for_claim(
        self,
        claim_id: str,
        annotated_claims: List[AnnotatedClaim]
    ) -> Optional[Dict]:
        """
        Get evidence snippet for UI display
        """
        for ac in annotated_claims:
            if ac.claim.claim_id == claim_id:
                return {
                    "evidence_text": ac.verification.evidence_used,
                    "citation": ac.verification.citation,
                    "document": ac.verification.citation.split(",")[0] if ac.verification.citation else "Unknown",
                    "confidence": ac.verification.confidence
                }
        return None
    
    def filter_claims_by_category(
        self,
        annotated_claims: List[AnnotatedClaim],
        category: Optional[ClaimCategory] = None
    ) -> List[AnnotatedClaim]:
        """
        Filter claims by category
        """
        if category is None:
            return annotated_claims
        return [c for c in annotated_claims if c.verification.category == category]
    
    def get_statistics(self, report: AuditReport) -> Dict:
        """
        Get comprehensive statistics for UI display
        """
        stats = report.to_dict()["statistics"]
        
        # Add percentages
        total = stats["total_claims"]
        if total > 0:
            stats["supported_pct"] = stats["supported"] / total * 100
            stats["contradicted_pct"] = stats["contradicted"] / total * 100
            stats["unverifiable_pct"] = stats["unverifiable"] / total * 100
        else:
            stats["supported_pct"] = 0
            stats["contradicted_pct"] = 0
            stats["unverifiable_pct"] = 0
        
        # Add trust score info
        stats["trust_score"] = report.trust_score.score
        stats["trust_level"] = report.trust_score.level.value
        stats["recommendations"] = report.trust_score.recommendations
        
        return stats
    
    def update_claim_feedback(
        self,
        claim_id: str,
        new_category: ClaimCategory,
        notes: Optional[str] = None
    ) -> None:
        """
        Record user feedback on a claim
        
        Args:
            claim_id: Claim identifier
            new_category: User-corrected category
            notes: Optional user notes
        """
        audit_logger = get_audit_logger()
        audit_logger.log_user_feedback(
            document_id=self._current_index.index_id if self._current_index else "unknown",
            claim_id=claim_id,
            original_category="unknown",  # Would need to track this
            new_category=new_category.value,
            notes=notes
        )
    
    def preload_models(self) -> None:
        """
        Preload all models for faster first inference
        """
        logger.info("Preloading models...")
        self.embedding_model.load()
        self.nli_model.load()
        self.correction.correction_model.load()
        logger.info("Models preloaded successfully")
    
    def unload_models(self) -> None:
        """
        Unload models to free memory
        """
        self.embedding_model.unload()
        self.nli_model.unload()
        self.correction.correction_model.unload()
        logger.info("Models unloaded")


# Singleton instance
_integration_layer: Optional[UIIntegrationLayer] = None


def get_integration_layer() -> UIIntegrationLayer:
    """Get singleton integration layer instance"""
    global _integration_layer
    if _integration_layer is None:
        _integration_layer = UIIntegrationLayer()
    return _integration_layer
