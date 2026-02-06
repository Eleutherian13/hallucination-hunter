"""
Layer 2: Claim Intelligence Layer
Handles claim decomposition, entity extraction, and fact identification
"""

import re
import uuid
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

import spacy

from src.config.settings import get_settings
from src.config.constants import Domain, DOMAIN_CONFIGS, ENTITY_SEVERITY_WEIGHTS
from src.config.prompts import PromptTemplates
from src.utils.text_processing import TextProcessor
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class ClaimType(str, Enum):
    """Types of claims"""
    FACTUAL = "factual"
    NUMERICAL = "numerical"
    ENTITY = "entity"
    TEMPORAL = "temporal"
    CAUSAL = "causal"
    COMPARATIVE = "comparative"


@dataclass
class Entity:
    """Extracted entity from text"""
    text: str
    label: str
    start: int
    end: int
    severity_weight: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "label": self.label,
            "start": self.start,
            "end": self.end,
            "severity_weight": self.severity_weight
        }


@dataclass
class Claim:
    """Represents an atomic factual claim"""
    claim_id: str
    text: str
    source_sentence: str
    source_start: int
    source_end: int
    claim_type: ClaimType
    entities: List[Entity]
    is_atomic: bool
    sub_claims: List["Claim"] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "source_sentence": self.source_sentence,
            "source_start": self.source_start,
            "source_end": self.source_end,
            "claim_type": self.claim_type.value,
            "entities": [e.to_dict() for e in self.entities],
            "is_atomic": self.is_atomic,
            "sub_claims": [c.to_dict() for c in self.sub_claims]
        }
    
    @property
    def max_severity_weight(self) -> float:
        """Get maximum severity weight from entities"""
        if not self.entities:
            return 1.0
        return max(e.severity_weight for e in self.entities)


class ClaimIntelligenceLayer:
    """
    Layer 2: Claim Intelligence
    
    Responsibilities:
    - Split text into sentences
    - Decompose sentences into atomic claims
    - Extract entities (people, numbers, dates, etc.)
    - Classify claim types
    - Identify critical claims for domain
    """
    
    def __init__(
        self,
        domain: Domain = Domain.GENERAL,
        spacy_model: Optional[str] = None
    ):
        """
        Initialize claim intelligence layer
        
        Args:
            domain: Domain for specialized processing
            spacy_model: spaCy model name
        """
        settings = get_settings()
        self.domain = domain
        self.domain_config = DOMAIN_CONFIGS.get(domain, DOMAIN_CONFIGS[Domain.GENERAL])
        
        # Load spaCy model
        model_name = spacy_model or "en_core_web_sm"
        try:
            self.nlp = spacy.load(model_name)
        except OSError:
            logger.warning(f"spaCy model {model_name} not found. Downloading...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", model_name], check=True)
            self.nlp = spacy.load(model_name)
        
        self.text_processor = TextProcessor()
        
        logger.info(f"Claim Intelligence Layer initialized (domain: {domain.value})")
    
    def extract_claims(self, text: str) -> List[Claim]:
        """
        Extract all claims from text
        
        Args:
            text: LLM-generated text
        
        Returns:
            List of extracted claims
        """
        claims = []
        
        # Split into sentences
        sentences = self.text_processor.split_sentences(text)
        
        current_pos = 0
        for sentence in sentences:
            # Find position in original text
            start_pos = text.find(sentence, current_pos)
            end_pos = start_pos + len(sentence) if start_pos >= 0 else current_pos + len(sentence)
            
            # Process sentence
            sentence_claims = self._process_sentence(sentence, start_pos, end_pos)
            claims.extend(sentence_claims)
            
            current_pos = end_pos
        
        logger.info(f"Extracted {len(claims)} claims from text")
        return claims
    
    def _process_sentence(
        self,
        sentence: str,
        start_pos: int,
        end_pos: int
    ) -> List[Claim]:
        """Process a single sentence into claims"""
        claims = []
        
        # Parse with spaCy
        doc = self.nlp(sentence)
        
        # Extract entities
        entities = self._extract_entities(doc)
        
        # Determine claim type
        claim_type = self._classify_claim_type(doc, entities)
        
        # Check if sentence should be decomposed
        sub_claims_texts = self._decompose_sentence(doc)
        
        if len(sub_claims_texts) <= 1:
            # Single atomic claim
            claim = Claim(
                claim_id=str(uuid.uuid4()),
                text=sentence,
                source_sentence=sentence,
                source_start=start_pos,
                source_end=end_pos,
                claim_type=claim_type,
                entities=entities,
                is_atomic=True
            )
            claims.append(claim)
        else:
            # Multiple sub-claims
            sub_claims = []
            for sub_text in sub_claims_texts:
                sub_doc = self.nlp(sub_text)
                sub_entities = self._extract_entities(sub_doc)
                sub_type = self._classify_claim_type(sub_doc, sub_entities)
                
                sub_claim = Claim(
                    claim_id=str(uuid.uuid4()),
                    text=sub_text,
                    source_sentence=sentence,
                    source_start=start_pos,
                    source_end=end_pos,
                    claim_type=sub_type,
                    entities=sub_entities,
                    is_atomic=True
                )
                sub_claims.append(sub_claim)
                claims.append(sub_claim)
            
            # Also add the parent claim for context
            parent = Claim(
                claim_id=str(uuid.uuid4()),
                text=sentence,
                source_sentence=sentence,
                source_start=start_pos,
                source_end=end_pos,
                claim_type=claim_type,
                entities=entities,
                is_atomic=False,
                sub_claims=sub_claims
            )
            # We don't add parent to claims list to avoid duplication
        
        return claims
    
    def _extract_entities(self, doc) -> List[Entity]:
        """Extract named entities from spaCy doc"""
        entities = []
        
        for ent in doc.ents:
            severity = ENTITY_SEVERITY_WEIGHTS.get(ent.label_, 1.0)
            
            entity = Entity(
                text=ent.text,
                label=ent.label_,
                start=ent.start_char,
                end=ent.end_char,
                severity_weight=severity
            )
            entities.append(entity)
        
        # Extract numbers not caught by NER
        for token in doc:
            if token.like_num and not any(
                e.start <= token.idx < e.end for e in entities
            ):
                entities.append(Entity(
                    text=token.text,
                    label="CARDINAL",
                    start=token.idx,
                    end=token.idx + len(token.text),
                    severity_weight=ENTITY_SEVERITY_WEIGHTS.get("CARDINAL", 1.4)
                ))
        
        # Domain-specific pattern matching
        text = doc.text
        for pattern in self.domain_config.get("critical_patterns", []):
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Check if already covered by an entity
                if not any(e.start <= match.start() < e.end for e in entities):
                    entities.append(Entity(
                        text=match.group(),
                        label="CRITICAL",
                        start=match.start(),
                        end=match.end(),
                        severity_weight=self.domain_config.get("severity_multiplier", 1.5)
                    ))
        
        return entities
    
    def _classify_claim_type(self, doc, entities: List[Entity]) -> ClaimType:
        """Classify the type of claim"""
        text = doc.text.lower()
        
        # Check for numerical claims
        has_numbers = any(e.label in ["CARDINAL", "MONEY", "PERCENT", "QUANTITY"] for e in entities)
        if has_numbers:
            return ClaimType.NUMERICAL
        
        # Check for temporal claims
        has_dates = any(e.label in ["DATE", "TIME"] for e in entities)
        if has_dates:
            return ClaimType.TEMPORAL
        
        # Check for comparative claims
        comparative_words = ["more", "less", "greater", "fewer", "higher", "lower", "better", "worse"]
        if any(word in text for word in comparative_words):
            return ClaimType.COMPARATIVE
        
        # Check for causal claims
        causal_words = ["because", "therefore", "thus", "hence", "causes", "leads to", "results in"]
        if any(word in text for word in causal_words):
            return ClaimType.CAUSAL
        
        # Check for entity-centric claims
        has_named_entities = any(e.label in ["PERSON", "ORG", "GPE", "PRODUCT"] for e in entities)
        if has_named_entities:
            return ClaimType.ENTITY
        
        return ClaimType.FACTUAL
    
    def _decompose_sentence(self, doc) -> List[str]:
        """
        Decompose a complex sentence into atomic claims
        
        Uses syntactic analysis to split compound sentences
        """
        text = doc.text
        sub_claims = []
        
        # Check for conjunctions
        conjunctions = ["and", "but", "or", "while", "whereas", "although"]
        has_conjunction = any(token.text.lower() in conjunctions for token in doc)
        
        if not has_conjunction:
            return [text]
        
        # Simple decomposition by conjunctions
        # More sophisticated decomposition could use dependency parsing
        current_claim = []
        
        for token in doc:
            if token.text.lower() in ["and", "but"] and token.dep_ == "cc":
                if current_claim:
                    claim_text = " ".join(t.text for t in current_claim).strip()
                    if claim_text and len(claim_text) > 10:
                        sub_claims.append(claim_text)
                    current_claim = []
            else:
                current_claim.append(token)
        
        if current_claim:
            claim_text = " ".join(t.text for t in current_claim).strip()
            if claim_text and len(claim_text) > 10:
                sub_claims.append(claim_text)
        
        # If decomposition failed or produced too few parts, return original
        if len(sub_claims) <= 1:
            return [text]
        
        return sub_claims
    
    def set_domain(self, domain: Domain) -> None:
        """Update domain configuration"""
        self.domain = domain
        self.domain_config = DOMAIN_CONFIGS.get(domain, DOMAIN_CONFIGS[Domain.GENERAL])
        logger.info(f"Domain updated to: {domain.value}")
    
    def get_critical_claims(self, claims: List[Claim]) -> List[Claim]:
        """
        Filter claims to get only critical ones based on domain
        
        Args:
            claims: All extracted claims
        
        Returns:
            List of claims with high severity weights
        """
        severity_threshold = 1.5
        return [c for c in claims if c.max_severity_weight >= severity_threshold]
    
    def get_claims_by_type(
        self,
        claims: List[Claim],
        claim_type: ClaimType
    ) -> List[Claim]:
        """Filter claims by type"""
        return [c for c in claims if c.claim_type == claim_type]
    
    def get_entity_summary(self, claims: List[Claim]) -> Dict:
        """
        Get summary of all entities across claims
        
        Returns:
            Dict with entity statistics
        """
        all_entities = []
        for claim in claims:
            all_entities.extend(claim.entities)
        
        entity_counts = {}
        for entity in all_entities:
            if entity.label not in entity_counts:
                entity_counts[entity.label] = []
            entity_counts[entity.label].append(entity.text)
        
        return {
            "total_entities": len(all_entities),
            "entity_types": {k: len(v) for k, v in entity_counts.items()},
            "unique_entities": {k: list(set(v)) for k, v in entity_counts.items()}
        }
