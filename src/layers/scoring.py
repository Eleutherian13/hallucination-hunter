"""
Layer 6: Scoring & Decision Layer
Calculates trust scores and aggregates verification results
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from src.layers.verification import VerificationResult
from src.layers.drift import DriftAdjustedResult
from src.layers.claim_intelligence import Claim
from src.config.settings import get_settings
from src.config.constants import ClaimCategory, TrustZone, Domain, DOMAIN_CONFIGS
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class TrustLevel(str, Enum):
    """Trust level categories"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CRITICAL = "critical"


@dataclass
class ScoreBreakdown:
    """Breakdown of trust score components"""
    supported_ratio: float
    supported_contribution: float
    avg_confidence: float
    confidence_contribution: float
    drift_score: float
    drift_contribution: float
    severity_score: float
    severity_contribution: float
    
    def to_dict(self) -> Dict:
        return {
            "supported_ratio": {
                "value": self.supported_ratio,
                "contribution": self.supported_contribution,
                "weight": get_settings().weight_supported_ratio
            },
            "avg_confidence": {
                "value": self.avg_confidence,
                "contribution": self.confidence_contribution,
                "weight": get_settings().weight_avg_confidence
            },
            "drift_score": {
                "value": self.drift_score,
                "contribution": self.drift_contribution,
                "weight": get_settings().weight_drift_score
            },
            "severity_score": {
                "value": self.severity_score,
                "contribution": self.severity_contribution,
                "weight": get_settings().weight_severity
            }
        }


@dataclass
class TrustScore:
    """Complete trust score with breakdown and metadata"""
    score: float
    level: TrustLevel
    breakdown: ScoreBreakdown
    category_counts: Dict[str, int]
    total_claims: int
    flagged_claims: List[str]
    recommendations: List[str]
    zone: Tuple[int, int, str, str]
    
    def to_dict(self) -> Dict:
        return {
            "score": self.score,
            "level": self.level.value,
            "zone": {
                "min": self.zone[0],
                "max": self.zone[1],
                "label": self.zone[2],
                "color": self.zone[3]
            },
            "breakdown": self.breakdown.to_dict(),
            "category_counts": self.category_counts,
            "total_claims": self.total_claims,
            "flagged_claims": self.flagged_claims[:5],  # Limit for display
            "recommendations": self.recommendations
        }


@dataclass
class CategoryStats:
    """Statistics for each claim category"""
    supported: int = 0
    contradicted: int = 0
    unverifiable: int = 0
    
    @property
    def total(self) -> int:
        return self.supported + self.contradicted + self.unverifiable
    
    def get_percentages(self) -> Dict[str, float]:
        if self.total == 0:
            return {"supported": 0, "contradicted": 0, "unverifiable": 0}
        return {
            "supported": self.supported / self.total * 100,
            "contradicted": self.contradicted / self.total * 100,
            "unverifiable": self.unverifiable / self.total * 100
        }


class ScoringLayer:
    """
    Layer 6: Scoring & Decision
    
    Responsibilities:
    - Calculate overall trust score (0-100)
    - Weight different verification signals
    - Apply domain-specific severity weights
    - Generate recommendations based on scores
    - Aggregate results for reporting
    """
    
    def __init__(
        self,
        domain: Domain = Domain.GENERAL,
        weight_supported: Optional[float] = None,
        weight_confidence: Optional[float] = None,
        weight_drift: Optional[float] = None,
        weight_severity: Optional[float] = None
    ):
        """
        Initialize scoring layer
        
        Args:
            domain: Domain for severity weighting
            weight_supported: Weight for supported ratio
            weight_confidence: Weight for average confidence
            weight_drift: Weight for drift score
            weight_severity: Weight for severity
        """
        settings = get_settings()
        
        self.domain = domain
        self.domain_config = DOMAIN_CONFIGS.get(domain, DOMAIN_CONFIGS[Domain.GENERAL])
        
        self.weight_supported = weight_supported or settings.weight_supported_ratio
        self.weight_confidence = weight_confidence or settings.weight_avg_confidence
        self.weight_drift = weight_drift or settings.weight_drift_score
        self.weight_severity = weight_severity or settings.weight_severity
        
        logger.info(f"Scoring Layer initialized (domain: {domain.value})")
    
    def calculate_trust_score(
        self,
        verification_results: List[VerificationResult],
        drift_adjusted_results: Optional[List[DriftAdjustedResult]] = None,
        claims: Optional[List[Claim]] = None
    ) -> TrustScore:
        """
        Calculate comprehensive trust score
        
        Args:
            verification_results: List of verification results
            drift_adjusted_results: Optional drift-adjusted results
            claims: Optional original claims for severity calculation
        
        Returns:
            TrustScore with full breakdown
        """
        if not verification_results:
            return self._empty_trust_score()
        
        # Calculate category statistics
        stats = self._calculate_category_stats(verification_results)
        
        # Calculate component scores
        supported_ratio = stats.supported / stats.total if stats.total > 0 else 0
        
        # Average confidence (use drift-adjusted if available)
        if drift_adjusted_results:
            avg_confidence = sum(r.adjusted_confidence for r in drift_adjusted_results) / len(drift_adjusted_results)
            drift_score = sum(r.drift_penalty for r in drift_adjusted_results) / len(drift_adjusted_results)
        else:
            avg_confidence = sum(r.confidence for r in verification_results) / len(verification_results)
            drift_score = 0
        
        # Calculate severity score
        severity_score = self._calculate_severity_score(verification_results, claims)
        
        # Calculate weighted score
        score_components = (
            supported_ratio * self.weight_supported +
            avg_confidence * self.weight_confidence +
            (1 - drift_score) * self.weight_drift +
            (1 - severity_score) * self.weight_severity
        )
        
        # Scale to 0-100
        final_score = score_components * 100
        final_score = max(0, min(100, final_score))
        
        # Determine trust level
        level = self._determine_trust_level(final_score, stats)
        
        # Create breakdown
        breakdown = ScoreBreakdown(
            supported_ratio=supported_ratio,
            supported_contribution=supported_ratio * self.weight_supported * 100,
            avg_confidence=avg_confidence,
            confidence_contribution=avg_confidence * self.weight_confidence * 100,
            drift_score=drift_score,
            drift_contribution=(1 - drift_score) * self.weight_drift * 100,
            severity_score=severity_score,
            severity_contribution=(1 - severity_score) * self.weight_severity * 100
        )
        
        # Get flagged claims
        flagged = self._get_flagged_claims(verification_results)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(final_score, stats, verification_results)
        
        # Get zone
        zone = TrustZone.get_zone(final_score)
        
        return TrustScore(
            score=round(final_score, 1),
            level=level,
            breakdown=breakdown,
            category_counts={
                "supported": stats.supported,
                "contradicted": stats.contradicted,
                "unverifiable": stats.unverifiable
            },
            total_claims=stats.total,
            flagged_claims=flagged,
            recommendations=recommendations,
            zone=zone
        )
    
    def _calculate_category_stats(self, results: List[VerificationResult]) -> CategoryStats:
        """Calculate statistics for each category"""
        stats = CategoryStats()
        
        for result in results:
            if result.category == ClaimCategory.SUPPORTED:
                stats.supported += 1
            elif result.category == ClaimCategory.CONTRADICTED:
                stats.contradicted += 1
            else:
                stats.unverifiable += 1
        
        return stats
    
    def _calculate_severity_score(
        self,
        results: List[VerificationResult],
        claims: Optional[List[Claim]]
    ) -> float:
        """Calculate weighted severity score for contradictions"""
        if not claims:
            # Use simple count-based severity
            contradicted = [r for r in results if r.category == ClaimCategory.CONTRADICTED]
            if not contradicted or not results:
                return 0
            return len(contradicted) / len(results)
        
        # Use claim severity weights
        total_severity = 0
        contradicted_severity = 0
        
        claim_map = {c.claim_id: c for c in claims}
        
        for result in results:
            claim = claim_map.get(result.claim_id)
            if claim:
                weight = claim.max_severity_weight * self.domain_config.get("severity_multiplier", 1.0)
                total_severity += weight
                if result.category == ClaimCategory.CONTRADICTED:
                    contradicted_severity += weight
        
        if total_severity == 0:
            return 0
        
        return contradicted_severity / total_severity
    
    def _determine_trust_level(self, score: float, stats: CategoryStats) -> TrustLevel:
        """Determine trust level from score and statistics"""
        if score >= 80 and stats.contradicted == 0:
            return TrustLevel.HIGH
        elif score >= 50:
            return TrustLevel.MEDIUM
        elif stats.contradicted > stats.total * 0.3:
            return TrustLevel.CRITICAL
        else:
            return TrustLevel.LOW
    
    def _get_flagged_claims(self, results: List[VerificationResult]) -> List[str]:
        """Get list of claims that need attention"""
        flagged = []
        
        for result in results:
            if result.category == ClaimCategory.CONTRADICTED:
                flagged.append(result.claim_text)
            elif (result.category == ClaimCategory.UNVERIFIABLE and 
                  result.confidence < 0.6):
                flagged.append(result.claim_text)
        
        return flagged
    
    def _generate_recommendations(
        self,
        score: float,
        stats: CategoryStats,
        results: List[VerificationResult]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if stats.contradicted > 0:
            recommendations.append(
                f"Review {stats.contradicted} contradicted claim(s) and consider corrections."
            )
        
        if stats.unverifiable > stats.total * 0.3:
            recommendations.append(
                "Many claims lack sufficient evidence. Consider adding more source documents."
            )
        
        if score < 50:
            recommendations.append(
                "Low trust score indicates significant issues. Manual review strongly recommended."
            )
        
        low_confidence = [r for r in results if r.confidence < 0.6]
        if len(low_confidence) > 3:
            recommendations.append(
                f"{len(low_confidence)} claims have low confidence scores. Consider reviewing these."
            )
        
        if not recommendations:
            if score >= 80:
                recommendations.append("Document passes verification with high confidence.")
            else:
                recommendations.append("Document passes verification. Minor review suggested.")
        
        return recommendations
    
    def _empty_trust_score(self) -> TrustScore:
        """Return empty trust score when no results"""
        return TrustScore(
            score=0,
            level=TrustLevel.LOW,
            breakdown=ScoreBreakdown(
                supported_ratio=0, supported_contribution=0,
                avg_confidence=0, confidence_contribution=0,
                drift_score=0, drift_contribution=0,
                severity_score=0, severity_contribution=0
            ),
            category_counts={"supported": 0, "contradicted": 0, "unverifiable": 0},
            total_claims=0,
            flagged_claims=[],
            recommendations=["No claims to verify."],
            zone=TrustZone.LOW
        )
    
    def compare_scores(
        self,
        score1: TrustScore,
        score2: TrustScore
    ) -> Dict:
        """Compare two trust scores"""
        return {
            "score_difference": score1.score - score2.score,
            "level_changed": score1.level != score2.level,
            "supported_difference": (
                score1.category_counts.get("supported", 0) - 
                score2.category_counts.get("supported", 0)
            ),
            "contradicted_difference": (
                score1.category_counts.get("contradicted", 0) - 
                score2.category_counts.get("contradicted", 0)
            ),
            "improvement": score1.score > score2.score
        }
    
    def get_score_trend(self, scores: List[TrustScore]) -> Dict:
        """Analyze trend across multiple scores"""
        if len(scores) < 2:
            return {"trend": "insufficient_data"}
        
        score_values = [s.score for s in scores]
        avg_change = sum(
            score_values[i] - score_values[i-1] 
            for i in range(1, len(score_values))
        ) / (len(score_values) - 1)
        
        if avg_change > 2:
            trend = "improving"
        elif avg_change < -2:
            trend = "declining"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "average_change": avg_change,
            "current_score": score_values[-1],
            "initial_score": score_values[0],
            "total_change": score_values[-1] - score_values[0]
        }
