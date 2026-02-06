"""
Layer 4: Verification & Reasoning Layer
NLI-based claim verification with entity consistency checking
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from difflib import SequenceMatcher
import re

from src.layers.claim_intelligence import Claim, Entity
from src.layers.retrieval import EvidenceResult
from src.models.nli_model import NLIModel, NLIResult
from src.config.settings import get_settings
from src.config.constants import ClaimCategory, ConfidenceLevel, Domain, DOMAIN_CONFIGS
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class EntityMatch:
    """Result of entity matching between claim and evidence"""
    claim_entity: Entity
    evidence_match: Optional[str]
    similarity: float
    is_match: bool
    is_contradiction: bool
    details: str
    
    def to_dict(self) -> Dict:
        return {
            "claim_entity": self.claim_entity.to_dict(),
            "evidence_match": self.evidence_match,
            "similarity": self.similarity,
            "is_match": self.is_match,
            "is_contradiction": self.is_contradiction,
            "details": self.details
        }


@dataclass
class VerificationResult:
    """Complete verification result for a claim"""
    claim_id: str
    claim_text: str
    category: ClaimCategory
    confidence: float
    confidence_level: ConfidenceLevel
    nli_result: NLIResult
    entity_matches: List[EntityMatch]
    evidence_used: str
    citation: str
    explanation: str
    
    # Detailed scores
    entity_consistency_score: float = 1.0
    numerical_accuracy_score: float = 1.0
    temporal_consistency_score: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "category": self.category.value,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level.value,
            "entity_consistency": self.entity_consistency_score,
            "numerical_accuracy": self.numerical_accuracy_score,
            "evidence_snippet": self.evidence_used[:300] + "..." if len(self.evidence_used) > 300 else self.evidence_used,
            "citation": self.citation,
            "explanation": self.explanation,
            "nli_scores": {
                "entailment": self.nli_result.entailment_score,
                "contradiction": self.nli_result.contradiction_score,
                "neutral": self.nli_result.neutral_score
            }
        }


class VerificationLayer:
    """
    Layer 4: Verification & Reasoning
    
    Responsibilities:
    - NLI classification (entailment/contradiction/neutral)
    - Entity consistency checking
    - Numerical verification
    - Temporal logic checking
    - Multi-evidence aggregation
    """
    
    def __init__(
        self,
        nli_model: Optional[NLIModel] = None,
        domain: Domain = Domain.GENERAL,
        entity_match_threshold: Optional[float] = None
    ):
        """
        Initialize verification layer
        
        Args:
            nli_model: NLI model for classification
            domain: Domain for specialized verification
            entity_match_threshold: Threshold for entity matching
        """
        settings = get_settings()
        
        self.nli_model = nli_model or NLIModel()
        self.domain = domain
        self.domain_config = DOMAIN_CONFIGS.get(domain, DOMAIN_CONFIGS[Domain.GENERAL])
        self.entity_match_threshold = entity_match_threshold or settings.entity_match_threshold
        
        logger.info(f"Verification Layer initialized (domain: {domain.value})")
    
    def verify_claim(
        self,
        claim: Claim,
        evidence: EvidenceResult
    ) -> VerificationResult:
        """
        Verify a single claim against evidence
        
        Args:
            claim: The claim to verify
            evidence: Retrieved evidence for the claim
        
        Returns:
            VerificationResult with classification and details
        """
        # Get combined evidence text
        evidence_text = evidence.get_combined_evidence(max_chunks=3)
        
        if not evidence_text:
            return self._create_unverifiable_result(claim, evidence, "No evidence found")
        
        # Run NLI classification
        nli_result = self.nli_model.classify_with_multiple_evidences(
            claim.text,
            [c.content for c in evidence.evidence_chunks[:3]],
            aggregation="max"
        )
        
        # Check entity consistency
        entity_matches = self._check_entity_consistency(claim, evidence_text)
        entity_score = self._calculate_entity_score(entity_matches)
        
        # Check for numerical contradictions
        numerical_score = self._check_numerical_consistency(claim, evidence_text)
        
        # Determine final category with fusion
        final_category, final_confidence = self._fuse_signals(
            nli_result,
            entity_score,
            numerical_score,
            entity_matches
        )
        
        # Generate explanation
        explanation = self._generate_explanation(
            claim,
            final_category,
            nli_result,
            entity_matches,
            evidence_text
        )
        
        return VerificationResult(
            claim_id=claim.claim_id,
            claim_text=claim.text,
            category=final_category,
            confidence=final_confidence,
            confidence_level=ConfidenceLevel.from_score(final_confidence),
            nli_result=nli_result,
            entity_matches=entity_matches,
            evidence_used=evidence_text,
            citation=evidence.citation or "No citation available",
            explanation=explanation,
            entity_consistency_score=entity_score,
            numerical_accuracy_score=numerical_score
        )
    
    def _check_entity_consistency(
        self,
        claim: Claim,
        evidence: str
    ) -> List[EntityMatch]:
        """Check if entities in claim match evidence"""
        matches = []
        evidence_lower = evidence.lower()
        
        for entity in claim.entities:
            entity_lower = entity.text.lower()
            
            # Direct match check
            if entity_lower in evidence_lower:
                matches.append(EntityMatch(
                    claim_entity=entity,
                    evidence_match=entity.text,
                    similarity=1.0,
                    is_match=True,
                    is_contradiction=False,
                    details="Exact match found in evidence"
                ))
            else:
                # Fuzzy match
                best_match, best_score = self._find_similar_entity(entity.text, evidence)
                
                if best_score >= self.entity_match_threshold:
                    matches.append(EntityMatch(
                        claim_entity=entity,
                        evidence_match=best_match,
                        similarity=best_score,
                        is_match=True,
                        is_contradiction=False,
                        details=f"Similar match: '{best_match}' (similarity: {best_score:.2f})"
                    ))
                elif best_score >= 0.5:
                    # Potential contradiction
                    matches.append(EntityMatch(
                        claim_entity=entity,
                        evidence_match=best_match,
                        similarity=best_score,
                        is_match=False,
                        is_contradiction=True,
                        details=f"Possible entity mismatch: claim has '{entity.text}', evidence has '{best_match}'"
                    ))
                else:
                    matches.append(EntityMatch(
                        claim_entity=entity,
                        evidence_match=None,
                        similarity=0,
                        is_match=False,
                        is_contradiction=False,
                        details=f"Entity '{entity.text}' not found in evidence"
                    ))
        
        return matches
    
    def _find_similar_entity(self, entity: str, text: str) -> Tuple[str, float]:
        """Find the most similar string in text to entity"""
        words = text.split()
        best_match = ""
        best_score = 0
        
        # Check single words and n-grams
        for n in range(1, min(4, len(words) + 1)):
            for i in range(len(words) - n + 1):
                candidate = " ".join(words[i:i + n])
                score = SequenceMatcher(None, entity.lower(), candidate.lower()).ratio()
                if score > best_score:
                    best_score = score
                    best_match = candidate
        
        return best_match, best_score
    
    def _check_numerical_consistency(self, claim: Claim, evidence: str) -> float:
        """Check if numbers in claim match evidence"""
        # Extract numbers from claim and evidence
        claim_numbers = re.findall(r'\b\d+\.?\d*\b', claim.text)
        evidence_numbers = re.findall(r'\b\d+\.?\d*\b', evidence)
        
        if not claim_numbers:
            return 1.0  # No numbers to check
        
        matches = 0
        for num in claim_numbers:
            if num in evidence_numbers:
                matches += 1
        
        return matches / len(claim_numbers)
    
    def _calculate_entity_score(self, matches: List[EntityMatch]) -> float:
        """Calculate overall entity consistency score"""
        if not matches:
            return 1.0
        
        total_weight = sum(m.claim_entity.severity_weight for m in matches)
        weighted_score = sum(
            m.similarity * m.claim_entity.severity_weight
            for m in matches if m.is_match
        )
        
        return weighted_score / total_weight if total_weight > 0 else 1.0
    
    def _fuse_signals(
        self,
        nli_result: NLIResult,
        entity_score: float,
        numerical_score: float,
        entity_matches: List[EntityMatch]
    ) -> Tuple[ClaimCategory, float]:
        """
        Fuse multiple signals to determine final classification
        
        Decision logic:
        1. If NLI says entailment AND entity/numerical scores are high -> SUPPORTED
        2. If NLI says contradiction OR significant entity mismatch -> CONTRADICTED
        3. Otherwise -> UNVERIFIABLE
        """
        has_entity_contradiction = any(m.is_contradiction for m in entity_matches)
        
        # Strong entailment with good entity matching
        if (nli_result.entailment_score > 0.8 and 
            entity_score > 0.9 and 
            numerical_score > 0.8 and
            not has_entity_contradiction):
            return ClaimCategory.SUPPORTED, min(nli_result.entailment_score, entity_score)
        
        # Clear contradiction from NLI
        if nli_result.contradiction_score > 0.7:
            return ClaimCategory.CONTRADICTED, nli_result.contradiction_score
        
        # Entity contradiction
        if has_entity_contradiction and entity_score < 0.7:
            # Combine NLI and entity signals
            contradiction_confidence = max(
                nli_result.contradiction_score,
                1 - entity_score
            )
            return ClaimCategory.CONTRADICTED, contradiction_confidence
        
        # Numerical mismatch
        if numerical_score < 0.5:
            return ClaimCategory.CONTRADICTED, 0.7
        
        # Moderate support
        if (nli_result.entailment_score > 0.6 and 
            entity_score > 0.7 and
            not has_entity_contradiction):
            return ClaimCategory.SUPPORTED, nli_result.entailment_score * entity_score
        
        # Default to unverifiable
        return ClaimCategory.UNVERIFIABLE, max(nli_result.neutral_score, 0.5)
    
    def _generate_explanation(
        self,
        claim: Claim,
        category: ClaimCategory,
        nli_result: NLIResult,
        entity_matches: List[EntityMatch],
        evidence: str
    ) -> str:
        """Generate human-readable explanation for the classification"""
        if category == ClaimCategory.SUPPORTED:
            explanation = f"The claim is supported by the evidence. "
            if nli_result.entailment_score > 0.9:
                explanation += "Strong semantic alignment detected. "
            matched_entities = [m for m in entity_matches if m.is_match]
            if matched_entities:
                entities = [m.claim_entity.text for m in matched_entities[:3]]
                explanation += f"Key entities verified: {', '.join(entities)}."
        
        elif category == ClaimCategory.CONTRADICTED:
            explanation = "The claim contradicts the evidence. "
            if nli_result.contradiction_score > 0.7:
                explanation += "Semantic contradiction detected. "
            contradictions = [m for m in entity_matches if m.is_contradiction]
            if contradictions:
                for m in contradictions[:2]:
                    explanation += f"Entity mismatch: claim says '{m.claim_entity.text}' but evidence has '{m.evidence_match}'. "
        
        else:
            explanation = "The claim cannot be fully verified from the available evidence. "
            unmatched = [m for m in entity_matches if not m.is_match and not m.is_contradiction]
            if unmatched:
                entities = [m.claim_entity.text for m in unmatched[:3]]
                explanation += f"Missing information for: {', '.join(entities)}."
        
        return explanation.strip()
    
    def _create_unverifiable_result(
        self,
        claim: Claim,
        evidence: EvidenceResult,
        reason: str
    ) -> VerificationResult:
        """Create an unverifiable result when evidence is insufficient"""
        return VerificationResult(
            claim_id=claim.claim_id,
            claim_text=claim.text,
            category=ClaimCategory.UNVERIFIABLE,
            confidence=0.5,
            confidence_level=ConfidenceLevel.UNCERTAIN,
            nli_result=NLIResult(
                category=ClaimCategory.UNVERIFIABLE,
                confidence=0.5,
                confidence_level=ConfidenceLevel.UNCERTAIN,
                entailment_score=0,
                contradiction_score=0,
                neutral_score=1,
                raw_scores={}
            ),
            entity_matches=[],
            evidence_used="",
            citation="No citation available",
            explanation=reason,
            entity_consistency_score=0,
            numerical_accuracy_score=0
        )
    
    def verify_claims_batch(
        self,
        claims: List[Claim],
        evidences: List[EvidenceResult]
    ) -> List[VerificationResult]:
        """
        Verify multiple claims
        
        Args:
            claims: List of claims
            evidences: List of evidence results (same order as claims)
        
        Returns:
            List of VerificationResult objects
        """
        if len(claims) != len(evidences):
            raise ValueError("Claims and evidences must have same length")
        
        results = []
        for claim, evidence in zip(claims, evidences):
            result = self.verify_claim(claim, evidence)
            results.append(result)
        
        logger.info(f"Verified {len(claims)} claims")
        return results
    
    def set_domain(self, domain: Domain) -> None:
        """Update domain configuration"""
        self.domain = domain
        self.domain_config = DOMAIN_CONFIGS.get(domain, DOMAIN_CONFIGS[Domain.GENERAL])
        self.entity_match_threshold = self.domain_config.get(
            "entity_match_threshold",
            self.entity_match_threshold
        )
        logger.info(f"Domain updated to: {domain.value}")
