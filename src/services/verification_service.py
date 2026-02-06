"""
Verification Service for Hallucination Hunter
Integrates the backend pipeline with the Streamlit frontend
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import hashlib
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.settings import Settings
from src.utils.text_processing import TextProcessor
from src.utils.file_handlers import FileHandler
from src.layers.ingestion import IngestionLayer
from src.layers.claim_intelligence import ClaimIntelligenceLayer
from src.layers.retrieval import RetrievalLayer
from src.layers.verification import VerificationLayer
from src.layers.scoring import ScoringLayer
from src.layers.correction import CorrectionLayer


@dataclass
class ProcessedSource:
    """Processed source document"""
    id: str
    name: str
    content: str
    file_type: str
    chunks: List[Dict[str, Any]] = field(default_factory=list)
    paragraphs: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class VerifiedClaim:
    """Verified claim with all metadata"""
    id: str
    text: str
    status: str  # 'supported', 'hallucination', 'unverifiable'
    confidence: float
    source_doc_id: Optional[str] = None
    source_paragraph_idx: Optional[int] = None
    source_snippet: Optional[str] = None
    explanation: str = ""
    correction: Optional[str] = None
    entities: List[str] = field(default_factory=list)


@dataclass
class VerificationReport:
    """Complete verification report"""
    overall_confidence: float
    total_claims: int
    supported_count: int
    hallucination_count: int
    unverifiable_count: int
    claims: List[VerifiedClaim] = field(default_factory=list)
    processing_time: float = 0.0
    source_documents: List[ProcessedSource] = field(default_factory=list)


class VerificationService:
    """
    Main service for document verification.
    Integrates all pipeline layers for end-to-end processing.
    """
    
    def __init__(self):
        """Initialize the verification service"""
        self.settings = Settings()
        self.text_processor = TextProcessor
        self.file_handler = FileHandler()
        
        # Initialize layers (lazy loading)
        self._ingestion_layer: Optional[IngestionLayer] = None
        self._claim_layer: Optional[ClaimIntelligenceLayer] = None
        self._retrieval_layer: Optional[RetrievalLayer] = None
        self._verification_layer: Optional[VerificationLayer] = None
        self._scoring_layer: Optional[ScoringLayer] = None
        self._correction_layer: Optional[CorrectionLayer] = None
    
    @property
    def ingestion_layer(self) -> IngestionLayer:
        if self._ingestion_layer is None:
            self._ingestion_layer = IngestionLayer()
        return self._ingestion_layer
    
    @property
    def claim_layer(self) -> ClaimIntelligenceLayer:
        if self._claim_layer is None:
            self._claim_layer = ClaimIntelligenceLayer()
        return self._claim_layer
    
    @property
    def retrieval_layer(self) -> RetrievalLayer:
        if self._retrieval_layer is None:
            self._retrieval_layer = RetrievalLayer()
        return self._retrieval_layer
    
    @property
    def verification_layer(self) -> VerificationLayer:
        if self._verification_layer is None:
            self._verification_layer = VerificationLayer()
        return self._verification_layer
    
    @property
    def scoring_layer(self) -> ScoringLayer:
        if self._scoring_layer is None:
            self._scoring_layer = ScoringLayer()
        return self._scoring_layer
    
    @property
    def correction_layer(self) -> CorrectionLayer:
        if self._correction_layer is None:
            self._correction_layer = CorrectionLayer()
        return self._correction_layer
    
    def process_source_document(
        self,
        content: str,
        filename: str,
        file_type: str = "txt"
    ) -> ProcessedSource:
        """
        Process a source document for indexing.
        
        Args:
            content: Document content
            filename: Name of the file
            file_type: Type of file (pdf, txt, docx)
        
        Returns:
            ProcessedSource with chunks and paragraphs
        """
        # Generate document ID
        doc_id = hashlib.md5(f"{filename}:{content[:100]}".encode()).hexdigest()[:12]
        
        # Clean text
        cleaned_content = self.text_processor.clean_text(content)
        
        # Split into paragraphs
        paragraphs = []
        para_texts = [p.strip() for p in cleaned_content.split('\n\n') if p.strip()]
        
        for idx, para_text in enumerate(para_texts):
            if len(para_text) > 20:  # Skip very short paragraphs
                paragraphs.append({
                    'idx': idx,
                    'text': para_text,
                    'doc_id': doc_id
                })
        
        # Create chunks for retrieval
        chunks = []
        sentences = self.text_processor.split_sentences(cleaned_content)
        
        chunk_size = self.settings.chunk_size
        chunk_overlap = self.settings.chunk_overlap
        
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_len = len(sentence)
            
            if current_length + sentence_len > chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'doc_id': doc_id,
                    'doc_name': filename
                })
                
                # Overlap: keep last few sentences
                overlap_sentences = current_chunk[-2:] if len(current_chunk) > 2 else current_chunk[-1:]
                current_chunk = overlap_sentences
                current_length = sum(len(s) for s in current_chunk)
            
            current_chunk.append(sentence)
            current_length += sentence_len
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'doc_id': doc_id,
                'doc_name': filename
            })
        
        return ProcessedSource(
            id=doc_id,
            name=filename,
            content=cleaned_content,
            file_type=file_type,
            chunks=chunks,
            paragraphs=paragraphs
        )
    
    def extract_claims_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract claims from LLM output text.
        
        Args:
            text: LLM generated text
        
        Returns:
            List of extracted claims with metadata
        """
        claims = self.claim_layer.extract_claims(text)
        
        result = []
        for i, claim in enumerate(claims):
            claim_id = f"claim_{i:03d}"
            result.append({
                'id': claim_id,
                'text': claim.text,
                'type': claim.claim_type.value if hasattr(claim.claim_type, 'value') else str(claim.claim_type),
                'entities': [e.text for e in claim.entities] if claim.entities else [],
                'importance': claim.importance_score
            })
        
        return result
    
    def verify_claim(
        self,
        claim_text: str,
        source_chunks: List[Dict[str, Any]],
        source_paragraphs: List[Dict[str, Any]]
    ) -> Tuple[str, float, Optional[str], Optional[int], str]:
        """
        Verify a single claim against source documents.
        
        Args:
            claim_text: The claim to verify
            source_chunks: Source document chunks for retrieval
            source_paragraphs: Source document paragraphs
        
        Returns:
            Tuple of (status, confidence, source_snippet, paragraph_idx, explanation)
        """
        # Find most relevant chunks
        relevant_chunks = self._find_relevant_chunks(claim_text, source_chunks)
        
        if not relevant_chunks:
            return (
                'unverifiable',
                0.3,
                None,
                None,
                "No relevant source material found to verify this claim."
            )
        
        # Get the best matching chunk
        best_chunk = relevant_chunks[0]
        source_snippet = best_chunk['text'][:200] + "..." if len(best_chunk['text']) > 200 else best_chunk['text']
        
        # Find matching paragraph index
        paragraph_idx = self._find_paragraph_index(source_snippet, source_paragraphs)
        
        # Verify using NLI
        verification_result = self.verification_layer.verify_claim(
            claim_text,
            [chunk['text'] for chunk in relevant_chunks[:3]]
        )
        
        # Determine status
        if verification_result.category == 'entailment':
            status = 'supported'
            explanation = f"This claim is factually supported by the source document. The source states: \"{source_snippet[:100]}...\""
        elif verification_result.category == 'contradiction':
            status = 'hallucination'
            explanation = f"CONTRADICTION DETECTED: This claim contradicts information in the source document. The source states: \"{source_snippet[:100]}...\""
        else:
            status = 'unverifiable'
            explanation = "There is not enough information in the source documents to verify or refute this claim."
        
        return (
            status,
            verification_result.confidence,
            source_snippet,
            paragraph_idx,
            explanation
        )
    
    def _find_relevant_chunks(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Find most relevant chunks for a query using simple keyword matching."""
        if not chunks:
            return []
        
        # Simple keyword-based relevance scoring
        query_words = set(query.lower().split())
        
        scored_chunks = []
        for chunk in chunks:
            chunk_words = set(chunk['text'].lower().split())
            overlap = len(query_words & chunk_words)
            score = overlap / max(len(query_words), 1)
            scored_chunks.append((score, chunk))
        
        # Sort by score and return top_k
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [chunk for score, chunk in scored_chunks[:top_k] if score > 0]
    
    def _find_paragraph_index(
        self,
        snippet: str,
        paragraphs: List[Dict[str, Any]]
    ) -> Optional[int]:
        """Find the paragraph index that contains the snippet."""
        snippet_lower = snippet.lower()[:50]
        
        for para in paragraphs:
            if snippet_lower in para['text'].lower():
                return para['idx']
        
        # Return first paragraph as fallback
        return 0 if paragraphs else None
    
    def generate_correction(
        self,
        claim_text: str,
        source_snippet: str
    ) -> Optional[str]:
        """Generate a correction for a hallucinated claim."""
        try:
            correction = self.correction_layer.generate_correction(
                claim_text,
                source_snippet
            )
            return correction.corrected_text if correction else None
        except Exception:
            # Fallback: suggest using the source text
            return f"Based on the source document: {source_snippet[:150]}..."
    
    def run_full_verification(
        self,
        source_documents: List[ProcessedSource],
        llm_output: str,
        progress_callback: Optional[callable] = None
    ) -> VerificationReport:
        """
        Run full verification pipeline.
        
        Args:
            source_documents: List of processed source documents
            llm_output: The LLM generated text to verify
            progress_callback: Optional callback for progress updates
        
        Returns:
            Complete verification report
        """
        start_time = time.time()
        
        def update_progress(step: str, pct: float):
            if progress_callback:
                progress_callback(step, pct)
        
        update_progress("Extracting claims...", 0.1)
        
        # Extract claims from LLM output
        claims_data = self.extract_claims_from_text(llm_output)
        
        if not claims_data:
            return VerificationReport(
                overall_confidence=1.0,
                total_claims=0,
                supported_count=0,
                hallucination_count=0,
                unverifiable_count=0,
                claims=[],
                processing_time=time.time() - start_time,
                source_documents=source_documents
            )
        
        update_progress("Building source index...", 0.2)
        
        # Combine all source chunks and paragraphs
        all_chunks = []
        all_paragraphs = []
        for doc in source_documents:
            all_chunks.extend(doc.chunks)
            all_paragraphs.extend(doc.paragraphs)
        
        update_progress("Verifying claims...", 0.3)
        
        # Verify each claim
        verified_claims = []
        supported_count = 0
        hallucination_count = 0
        unverifiable_count = 0
        
        for i, claim_data in enumerate(claims_data):
            progress = 0.3 + (0.5 * (i + 1) / len(claims_data))
            update_progress(f"Verifying claim {i+1}/{len(claims_data)}...", progress)
            
            # Verify the claim
            status, confidence, source_snippet, para_idx, explanation = self.verify_claim(
                claim_data['text'],
                all_chunks,
                all_paragraphs
            )
            
            # Generate correction if hallucination
            correction = None
            if status == 'hallucination' and source_snippet:
                update_progress(f"Generating correction for claim {i+1}...", progress + 0.02)
                correction = self.generate_correction(claim_data['text'], source_snippet)
            
            # Find source document ID
            source_doc_id = None
            if all_chunks and source_snippet:
                for doc in source_documents:
                    for chunk in doc.chunks:
                        if source_snippet[:50] in chunk['text']:
                            source_doc_id = doc.id
                            break
                    if source_doc_id:
                        break
            
            verified_claim = VerifiedClaim(
                id=claim_data['id'],
                text=claim_data['text'],
                status=status,
                confidence=confidence,
                source_doc_id=source_doc_id,
                source_paragraph_idx=para_idx,
                source_snippet=source_snippet,
                explanation=explanation,
                correction=correction,
                entities=claim_data.get('entities', [])
            )
            
            verified_claims.append(verified_claim)
            
            if status == 'supported':
                supported_count += 1
            elif status == 'hallucination':
                hallucination_count += 1
            else:
                unverifiable_count += 1
        
        update_progress("Calculating trust score...", 0.9)
        
        # Calculate overall confidence
        if verified_claims:
            supported_ratio = supported_count / len(verified_claims)
            avg_confidence = sum(c.confidence for c in verified_claims) / len(verified_claims)
            overall_confidence = (supported_ratio * 0.7) + (avg_confidence * 0.3)
        else:
            overall_confidence = 1.0
        
        update_progress("Complete!", 1.0)
        
        return VerificationReport(
            overall_confidence=overall_confidence,
            total_claims=len(verified_claims),
            supported_count=supported_count,
            hallucination_count=hallucination_count,
            unverifiable_count=unverifiable_count,
            claims=verified_claims,
            processing_time=time.time() - start_time,
            source_documents=source_documents
        )


# Singleton instance
_verification_service: Optional[VerificationService] = None


def get_verification_service() -> VerificationService:
    """Get or create the verification service singleton."""
    global _verification_service
    if _verification_service is None:
        _verification_service = VerificationService()
    return _verification_service
