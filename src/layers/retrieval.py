"""
Layer 3: Evidence Retrieval Layer
Hybrid search combining vector (FAISS) and keyword (BM25) search
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np

from rank_bm25 import BM25Okapi

from src.layers.ingestion import DocumentIndex, IndexedChunk
from src.layers.claim_intelligence import Claim
from src.models.embedding_model import EmbeddingModel
from src.config.settings import get_settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class EvidenceResult:
    """Result of evidence retrieval for a claim"""
    claim_id: str
    claim_text: str
    evidence_chunks: List[IndexedChunk]
    scores: List[float]
    retrieval_method: str
    top_evidence: Optional[str] = None
    citation: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "claim_id": self.claim_id,
            "claim_text": self.claim_text,
            "evidence_count": len(self.evidence_chunks),
            "top_score": max(self.scores) if self.scores else 0,
            "retrieval_method": self.retrieval_method,
            "citation": self.citation,
            "evidences": [
                {
                    "chunk_id": c.chunk_id,
                    "document": c.document_name,
                    "page": c.page_number,
                    "content": c.content[:200] + "..." if len(c.content) > 200 else c.content,
                    "score": s
                }
                for c, s in zip(self.evidence_chunks, self.scores)
            ]
        }
    
    def get_combined_evidence(self, max_chunks: int = 3) -> str:
        """Get combined text from top evidence chunks"""
        top_chunks = self.evidence_chunks[:max_chunks]
        return "\n\n".join(c.content for c in top_chunks)
    
    def get_citation_string(self) -> str:
        """Generate citation string for top evidence"""
        if not self.evidence_chunks:
            return "No evidence found"
        
        chunk = self.evidence_chunks[0]
        parts = [chunk.document_name]
        if chunk.page_number:
            parts.append(f"Page {chunk.page_number}")
        if chunk.metadata.get("line_start"):
            parts.append(f"Lines {chunk.metadata['line_start']}-{chunk.metadata.get('line_end', '?')}")
        
        return ", ".join(parts)


class RetrievalLayer:
    """
    Layer 3: Evidence Retrieval
    
    Responsibilities:
    - Vector search using FAISS for semantic similarity
    - Keyword search using BM25 for lexical matching
    - Hybrid search combining both methods
    - Relevance reranking and filtering
    """
    
    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        vector_weight: Optional[float] = None,
        keyword_weight: Optional[float] = None
    ):
        """
        Initialize retrieval layer
        
        Args:
            embedding_model: Model for query embeddings
            top_k: Number of results to retrieve
            similarity_threshold: Minimum similarity score
            vector_weight: Weight for vector search (0-1)
            keyword_weight: Weight for keyword search (0-1)
        """
        settings = get_settings()
        
        self.embedding_model = embedding_model or EmbeddingModel()
        self.top_k = top_k or settings.retrieval_top_k
        self.similarity_threshold = similarity_threshold or settings.similarity_threshold
        self.vector_weight = vector_weight or settings.hybrid_weight_vector
        self.keyword_weight = keyword_weight or settings.hybrid_weight_keyword
        
        self._bm25_index = None
        self._bm25_chunks = None
        
        logger.info(f"Retrieval Layer initialized (top_k={self.top_k}, threshold={self.similarity_threshold})")
    
    def build_bm25_index(self, chunks: List[IndexedChunk]) -> None:
        """
        Build BM25 index for keyword search
        
        Args:
            chunks: List of indexed chunks
        """
        # Tokenize chunks
        tokenized = [chunk.content.lower().split() for chunk in chunks]
        self._bm25_index = BM25Okapi(tokenized)
        self._bm25_chunks = chunks
        logger.info(f"BM25 index built with {len(chunks)} chunks")
    
    def vector_search(
        self,
        query: str,
        doc_index: DocumentIndex,
        top_k: Optional[int] = None
    ) -> List[Tuple[IndexedChunk, float]]:
        """
        Perform vector similarity search
        
        Args:
            query: Search query
            doc_index: Document index with FAISS
            top_k: Number of results
        
        Returns:
            List of (chunk, score) tuples
        """
        k = top_k or self.top_k
        
        # Get query embedding
        query_embedding = self.embedding_model.encode(query)
        
        # Search FAISS index
        results = doc_index.search(query_embedding, k)
        
        return results
    
    def keyword_search(
        self,
        query: str,
        chunks: Optional[List[IndexedChunk]] = None,
        top_k: Optional[int] = None
    ) -> List[Tuple[IndexedChunk, float]]:
        """
        Perform BM25 keyword search
        
        Args:
            query: Search query
            chunks: Chunks to search (uses cached if not provided)
            top_k: Number of results
        
        Returns:
            List of (chunk, score) tuples
        """
        k = top_k or self.top_k
        
        if chunks:
            self.build_bm25_index(chunks)
        
        if not self._bm25_index or not self._bm25_chunks:
            logger.warning("BM25 index not built. Call build_bm25_index first.")
            return []
        
        # Tokenize query
        query_tokens = query.lower().split()
        
        # Get BM25 scores
        scores = self._bm25_index.get_scores(query_tokens)
        
        # Get top-k results
        top_indices = np.argsort(scores)[::-1][:k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append((self._bm25_chunks[idx], float(scores[idx])))
        
        return results
    
    def hybrid_search(
        self,
        query: str,
        doc_index: DocumentIndex,
        top_k: Optional[int] = None
    ) -> List[Tuple[IndexedChunk, float]]:
        """
        Perform hybrid search combining vector and keyword methods
        
        Args:
            query: Search query
            doc_index: Document index
            top_k: Number of final results
        
        Returns:
            List of (chunk, score) tuples with combined scores
        """
        k = top_k or self.top_k
        
        # Ensure BM25 index is built
        if not self._bm25_index:
            self.build_bm25_index(doc_index.chunks)
        
        # Get results from both methods
        vector_results = self.vector_search(query, doc_index, k * 2)
        keyword_results = self.keyword_search(query, top_k=k * 2)
        
        # Normalize and combine scores
        combined = {}
        
        # Process vector results
        if vector_results:
            max_vec_score = max(r[1] for r in vector_results) if vector_results else 1
            for chunk, score in vector_results:
                normalized = score / max_vec_score if max_vec_score > 0 else 0
                combined[chunk.chunk_id] = {
                    "chunk": chunk,
                    "vector_score": normalized,
                    "keyword_score": 0
                }
        
        # Process keyword results
        if keyword_results:
            max_kw_score = max(r[1] for r in keyword_results) if keyword_results else 1
            for chunk, score in keyword_results:
                normalized = score / max_kw_score if max_kw_score > 0 else 0
                if chunk.chunk_id in combined:
                    combined[chunk.chunk_id]["keyword_score"] = normalized
                else:
                    combined[chunk.chunk_id] = {
                        "chunk": chunk,
                        "vector_score": 0,
                        "keyword_score": normalized
                    }
        
        # Calculate final scores
        results = []
        for chunk_id, data in combined.items():
            final_score = (
                self.vector_weight * data["vector_score"] +
                self.keyword_weight * data["keyword_score"]
            )
            results.append((data["chunk"], final_score))
        
        # Sort by score and return top k
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]
    
    def retrieve_evidence(
        self,
        claim: Claim,
        doc_index: DocumentIndex,
        method: str = "hybrid"
    ) -> EvidenceResult:
        """
        Retrieve evidence for a single claim
        
        Args:
            claim: Claim to find evidence for
            doc_index: Document index
            method: Search method ('vector', 'keyword', 'hybrid')
        
        Returns:
            EvidenceResult with retrieved evidence
        """
        # Select search method
        if method == "vector":
            results = self.vector_search(claim.text, doc_index)
        elif method == "keyword":
            if not self._bm25_index:
                self.build_bm25_index(doc_index.chunks)
            results = self.keyword_search(claim.text)
        else:
            results = self.hybrid_search(claim.text, doc_index)
        
        # Filter by threshold
        filtered_results = [
            (chunk, score) for chunk, score in results
            if score >= self.similarity_threshold
        ]
        
        if not filtered_results:
            # If no results above threshold, return top result anyway
            filtered_results = results[:1] if results else []
        
        chunks = [r[0] for r in filtered_results]
        scores = [r[1] for r in filtered_results]
        
        evidence_result = EvidenceResult(
            claim_id=claim.claim_id,
            claim_text=claim.text,
            evidence_chunks=chunks,
            scores=scores,
            retrieval_method=method,
            top_evidence=chunks[0].content if chunks else None,
            citation=None
        )
        
        # Generate citation
        if chunks:
            evidence_result.citation = evidence_result.get_citation_string()
        
        return evidence_result
    
    def retrieve_evidence_batch(
        self,
        claims: List[Claim],
        doc_index: DocumentIndex,
        method: str = "hybrid"
    ) -> List[EvidenceResult]:
        """
        Retrieve evidence for multiple claims
        
        Args:
            claims: List of claims
            doc_index: Document index
            method: Search method
        
        Returns:
            List of EvidenceResult objects
        """
        # Build BM25 index once if using hybrid or keyword
        if method in ["hybrid", "keyword"] and not self._bm25_index:
            self.build_bm25_index(doc_index.chunks)
        
        results = []
        for claim in claims:
            evidence = self.retrieve_evidence(claim, doc_index, method)
            results.append(evidence)
        
        logger.info(f"Retrieved evidence for {len(claims)} claims using {method} search")
        return results
    
    def rerank_by_entity_match(
        self,
        claim: Claim,
        evidence_result: EvidenceResult
    ) -> EvidenceResult:
        """
        Rerank evidence based on entity overlap with claim
        
        Args:
            claim: The claim with entities
            evidence_result: Initial evidence result
        
        Returns:
            Reranked EvidenceResult
        """
        if not claim.entities or not evidence_result.evidence_chunks:
            return evidence_result
        
        claim_entities = set(e.text.lower() for e in claim.entities)
        
        # Calculate entity overlap scores
        reranked = []
        for chunk, base_score in zip(evidence_result.evidence_chunks, evidence_result.scores):
            chunk_text = chunk.content.lower()
            entity_matches = sum(1 for e in claim_entities if e in chunk_text)
            entity_bonus = entity_matches * 0.1  # 10% bonus per matching entity
            
            new_score = min(base_score + entity_bonus, 1.0)
            reranked.append((chunk, new_score))
        
        # Re-sort
        reranked.sort(key=lambda x: x[1], reverse=True)
        
        return EvidenceResult(
            claim_id=evidence_result.claim_id,
            claim_text=evidence_result.claim_text,
            evidence_chunks=[r[0] for r in reranked],
            scores=[r[1] for r in reranked],
            retrieval_method=evidence_result.retrieval_method + "+entity_rerank",
            top_evidence=reranked[0][0].content if reranked else None,
            citation=evidence_result.get_citation_string() if reranked else None
        )
