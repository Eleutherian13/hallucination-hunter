"""
Layer 5: Drift Mitigation Layer
Handles LLM output stochasticity analysis and confidence adjustment
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

from src.models.drift_detector import DriftDetector, DriftReport, ClaimDrift
from src.layers.verification import VerificationResult
from src.layers.claim_intelligence import Claim
from src.config.settings import get_settings
from src.config.constants import ClaimCategory
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class DriftAdjustedResult:
    """Verification result with drift adjustment applied"""
    original_result: VerificationResult
    drift_analysis: Optional[ClaimDrift]
    adjusted_confidence: float
    drift_penalty: float
    is_stable: bool
    stability_note: str
    
    def to_dict(self) -> Dict:
        return {
            "claim_id": self.original_result.claim_id,
            "category": self.original_result.category.value,
            "original_confidence": self.original_result.confidence,
            "adjusted_confidence": self.adjusted_confidence,
            "drift_penalty": self.drift_penalty,
            "is_stable": self.is_stable,
            "stability_note": self.stability_note
        }


class DriftMitigationLayer:
    """
    Layer 5: Drift Mitigation
    
    Responsibilities:
    - Analyze LLM output consistency across regenerations
    - Calculate drift scores for claims
    - Adjust confidence scores based on stability
    - Flag high-variance claims for review
    """
    
    def __init__(
        self,
        drift_detector: Optional[DriftDetector] = None,
        variance_threshold: Optional[float] = None,
        confidence_penalty: Optional[float] = None
    ):
        """
        Initialize drift mitigation layer
        
        Args:
            drift_detector: Drift detection model
            variance_threshold: Threshold for flagging unstable claims
            confidence_penalty: Penalty factor for high-drift claims
        """
        settings = get_settings()
        
        self.drift_detector = drift_detector or DriftDetector()
        self.variance_threshold = variance_threshold or settings.drift_variance_threshold
        self.confidence_penalty = confidence_penalty or settings.drift_confidence_penalty
        
        self._drift_report: Optional[DriftReport] = None
        
        logger.info(f"Drift Mitigation Layer initialized (threshold: {self.variance_threshold})")
    
    def analyze_drift(
        self,
        original_output: str,
        regenerated_outputs: List[str]
    ) -> DriftReport:
        """
        Analyze drift across multiple LLM regenerations
        
        Args:
            original_output: Original LLM output
            regenerated_outputs: List of regenerated outputs
        
        Returns:
            DriftReport with comprehensive analysis
        """
        self._drift_report = self.drift_detector.analyze_output_drift(
            original_output,
            regenerated_outputs
        )
        
        logger.info(f"Drift analysis complete: {self._drift_report.stable_claims}/{self._drift_report.total_claims} stable claims")
        
        return self._drift_report
    
    def adjust_verification_results(
        self,
        verification_results: List[VerificationResult],
        drift_report: Optional[DriftReport] = None
    ) -> List[DriftAdjustedResult]:
        """
        Adjust verification results based on drift analysis
        
        Args:
            verification_results: Original verification results
            drift_report: Drift report (uses cached if not provided)
        
        Returns:
            List of DriftAdjustedResult with adjusted confidences
        """
        report = drift_report or self._drift_report
        
        adjusted_results = []
        
        for result in verification_results:
            # Find matching drift analysis
            claim_drift = self._find_claim_drift(result.claim_text, report)
            
            if claim_drift and not claim_drift.is_stable:
                # Apply penalty for unstable claims
                penalty = self._calculate_penalty(claim_drift.drift_score)
                adjusted_confidence = result.confidence * (1 - penalty)
                is_stable = False
                stability_note = f"Claim shows variance across regenerations (drift score: {claim_drift.drift_score:.2f})"
            else:
                penalty = 0.0
                adjusted_confidence = result.confidence
                is_stable = True
                stability_note = "Claim is stable across regenerations"
            
            adjusted_results.append(DriftAdjustedResult(
                original_result=result,
                drift_analysis=claim_drift,
                adjusted_confidence=adjusted_confidence,
                drift_penalty=penalty,
                is_stable=is_stable,
                stability_note=stability_note
            ))
        
        return adjusted_results
    
    def _find_claim_drift(
        self,
        claim_text: str,
        report: Optional[DriftReport]
    ) -> Optional[ClaimDrift]:
        """Find drift analysis for a specific claim"""
        if not report:
            return None
        
        # Look for exact or similar match
        for drift in report.claim_drifts:
            if drift.claim == claim_text:
                return drift
        
        # Fuzzy matching if exact not found
        from src.models.embedding_model import EmbeddingModel
        embedding_model = EmbeddingModel()
        
        for drift in report.claim_drifts:
            similarity = embedding_model.similarity(claim_text, drift.claim)
            if similarity > 0.9:
                return drift
        
        return None
    
    def _calculate_penalty(self, drift_score: float) -> float:
        """Calculate confidence penalty based on drift score"""
        if drift_score <= self.variance_threshold:
            return 0.0
        
        # Linear penalty beyond threshold
        excess_drift = drift_score - self.variance_threshold
        penalty = min(excess_drift * self.confidence_penalty * 5, 0.5)
        
        return penalty
    
    def get_high_drift_claims(
        self,
        adjusted_results: List[DriftAdjustedResult]
    ) -> List[DriftAdjustedResult]:
        """Get claims with high drift scores"""
        return [r for r in adjusted_results if not r.is_stable]
    
    def get_stability_summary(
        self,
        adjusted_results: List[DriftAdjustedResult]
    ) -> Dict:
        """Get summary of stability analysis"""
        stable_count = sum(1 for r in adjusted_results if r.is_stable)
        unstable_count = len(adjusted_results) - stable_count
        
        avg_penalty = 0
        if adjusted_results:
            avg_penalty = sum(r.drift_penalty for r in adjusted_results) / len(adjusted_results)
        
        return {
            "total_claims": len(adjusted_results),
            "stable_claims": stable_count,
            "unstable_claims": unstable_count,
            "stability_percentage": (stable_count / len(adjusted_results) * 100) if adjusted_results else 100,
            "average_drift_penalty": avg_penalty,
            "high_drift_claims": [
                r.original_result.claim_text 
                for r in adjusted_results 
                if not r.is_stable
            ][:5]
        }
    
    def should_flag_for_review(
        self,
        adjusted_result: DriftAdjustedResult
    ) -> bool:
        """Determine if a claim should be flagged for human review"""
        # Flag if:
        # 1. High drift
        # 2. Contradicted with low confidence
        # 3. Significant confidence reduction
        
        if not adjusted_result.is_stable:
            return True
        
        if (adjusted_result.original_result.category == ClaimCategory.CONTRADICTED and
            adjusted_result.adjusted_confidence < 0.7):
            return True
        
        confidence_drop = adjusted_result.original_result.confidence - adjusted_result.adjusted_confidence
        if confidence_drop > 0.2:
            return True
        
        return False
    
    def compare_regenerations(
        self,
        original_claims: List[Claim],
        regenerated_claims: List[List[Claim]]
    ) -> Dict:
        """
        Compare claims across regenerations
        
        Args:
            original_claims: Claims from original output
            regenerated_claims: Claims from each regeneration
        
        Returns:
            Comparison report
        """
        comparison = {
            "original_count": len(original_claims),
            "regeneration_counts": [len(c) for c in regenerated_claims],
            "claim_consistency": [],
            "missing_claims": [],
            "new_claims": []
        }
        
        # Check each original claim
        for orig_claim in original_claims:
            found_in = []
            for i, regen_claims in enumerate(regenerated_claims):
                for regen_claim in regen_claims:
                    similarity = self._text_similarity(orig_claim.text, regen_claim.text)
                    if similarity > 0.8:
                        found_in.append(i)
                        break
            
            consistency = len(found_in) / len(regenerated_claims) if regenerated_claims else 0
            comparison["claim_consistency"].append({
                "claim": orig_claim.text[:100],
                "found_in_regenerations": len(found_in),
                "consistency": consistency
            })
            
            if consistency < 0.5:
                comparison["missing_claims"].append(orig_claim.text[:100])
        
        return comparison
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity using word overlap"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
