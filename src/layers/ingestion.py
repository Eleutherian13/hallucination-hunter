"""
Layer 1: Input & Ingestion Layer
Handles document parsing, chunking, embedding, and indexing
"""

import uuid
from typing import Dict, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
import numpy as np

import faiss

from src.utils.file_handlers import DocumentParser, ParsedDocument, DocumentChunkLocator
from src.utils.text_processing import TextProcessor, TextChunk
from src.models.embedding_model import EmbeddingModel
from src.config.settings import get_settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class IndexedChunk:
    """A chunk with its embedding and metadata"""
    chunk_id: str
    content: str
    embedding: np.ndarray
    document_id: str
    document_name: str
    chunk_index: int
    start_char: int
    end_char: int
    page_number: Optional[int] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "document_id": self.document_id,
            "document_name": self.document_name,
            "chunk_index": self.chunk_index,
            "page_number": self.page_number,
            "start_char": self.start_char,
            "end_char": self.end_char
        }


@dataclass
class DocumentIndex:
    """Index containing all processed documents and their chunks"""
    index_id: str
    documents: Dict[str, ParsedDocument]
    chunks: List[IndexedChunk]
    faiss_index: faiss.IndexFlatIP
    embedding_dimension: int
    total_chunks: int
    total_documents: int
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[IndexedChunk]:
        """Get a chunk by its ID"""
        for chunk in self.chunks:
            if chunk.chunk_id == chunk_id:
                return chunk
        return None
    
    def get_chunks_by_document(self, document_id: str) -> List[IndexedChunk]:
        """Get all chunks for a specific document"""
        return [c for c in self.chunks if c.document_id == document_id]
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5
    ) -> List[tuple]:
        """
        Search for similar chunks
        
        Returns:
            List of (chunk, score) tuples
        """
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Normalize for cosine similarity
        faiss.normalize_L2(query_embedding)
        
        scores, indices = self.faiss_index.search(query_embedding, top_k)
        
        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < len(self.chunks) and idx >= 0:
                results.append((self.chunks[idx], float(score)))
        
        return results


class IngestionLayer:
    """
    Layer 1: Input & Ingestion
    
    Responsibilities:
    - Parse documents (PDF, TXT, DOCX, HTML)
    - Chunk text with configurable size and overlap
    - Generate embeddings for chunks
    - Build FAISS index for fast retrieval
    """
    
    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ):
        """
        Initialize ingestion layer
        
        Args:
            embedding_model: Model for generating embeddings
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
        """
        settings = get_settings()
        
        self.embedding_model = embedding_model or EmbeddingModel()
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        self.parser = DocumentParser()
        self.text_processor = TextProcessor()
        
        logger.info(f"Ingestion Layer initialized (chunk_size={self.chunk_size}, overlap={self.chunk_overlap})")
    
    def process_document(
        self,
        file_path: Optional[Union[str, Path]] = None,
        file_content: Optional[bytes] = None,
        file_name: Optional[str] = None,
        file_type: Optional[str] = None,
        document_id: Optional[str] = None
    ) -> tuple:
        """
        Process a single document
        
        Args:
            file_path: Path to the document
            file_content: Document content as bytes
            file_name: Original filename
            file_type: File extension
            document_id: Custom document ID (auto-generated if not provided)
        
        Returns:
            Tuple of (ParsedDocument, List[IndexedChunk])
        """
        # Parse document
        parsed = self.parser.parse(
            file_path=file_path,
            file_content=file_content,
            file_name=file_name,
            file_type=file_type
        )
        
        document_id = document_id or str(uuid.uuid4())
        
        # Chunk the document
        text_chunks = self.text_processor.chunk_text(
            parsed.content,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            respect_sentences=True
        )
        
        # Generate embeddings
        chunk_texts = [c.content for c in text_chunks]
        embeddings = self.embedding_model.encode(chunk_texts)
        
        # Create indexed chunks with location info
        locator = DocumentChunkLocator(parsed)
        indexed_chunks = []
        
        for i, (chunk, embedding) in enumerate(zip(text_chunks, embeddings)):
            location = locator.find_location(chunk.content)
            
            indexed_chunk = IndexedChunk(
                chunk_id=f"{document_id}_chunk_{i}",
                content=chunk.content,
                embedding=embedding,
                document_id=document_id,
                document_name=parsed.metadata.filename,
                chunk_index=i,
                start_char=chunk.start_char,
                end_char=chunk.end_char,
                page_number=location.get("page") if location else None,
                metadata={
                    "line_start": location.get("start_line") if location else None,
                    "line_end": location.get("end_line") if location else None
                }
            )
            indexed_chunks.append(indexed_chunk)
        
        logger.info(f"Processed document '{parsed.metadata.filename}': {len(indexed_chunks)} chunks")
        
        return parsed, indexed_chunks
    
    def process_documents(
        self,
        documents: List[Dict]
    ) -> DocumentIndex:
        """
        Process multiple documents and create an index
        
        Args:
            documents: List of document dicts with 'path', 'content', 'name', 'type' keys
        
        Returns:
            DocumentIndex with all processed documents
        """
        all_chunks = []
        parsed_docs = {}
        
        for doc in documents:
            doc_id = str(uuid.uuid4())
            
            parsed, chunks = self.process_document(
                file_path=doc.get("path"),
                file_content=doc.get("content"),
                file_name=doc.get("name"),
                file_type=doc.get("type"),
                document_id=doc_id
            )
            
            parsed_docs[doc_id] = parsed
            all_chunks.extend(chunks)
        
        # Build FAISS index
        index = self._build_faiss_index(all_chunks)
        
        doc_index = DocumentIndex(
            index_id=str(uuid.uuid4()),
            documents=parsed_docs,
            chunks=all_chunks,
            faiss_index=index,
            embedding_dimension=self.embedding_model.dimension,
            total_chunks=len(all_chunks),
            total_documents=len(parsed_docs)
        )
        
        logger.info(f"Created index with {doc_index.total_documents} documents, {doc_index.total_chunks} chunks")
        
        return doc_index
    
    def _build_faiss_index(self, chunks: List[IndexedChunk]) -> faiss.IndexFlatIP:
        """Build FAISS index from chunks"""
        if not chunks:
            return faiss.IndexFlatIP(self.embedding_model.dimension)
        
        # Stack embeddings
        embeddings = np.vstack([c.embedding for c in chunks]).astype('float32')
        
        # Normalize for cosine similarity (Inner Product)
        faiss.normalize_L2(embeddings)
        
        # Create index
        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)
        
        return index
    
    def process_llm_output(self, text: str) -> Dict:
        """
        Process LLM-generated output text
        
        Args:
            text: LLM output text
        
        Returns:
            Dict with processed text and metadata
        """
        cleaned = self.text_processor.clean_text(text)
        sentences = self.text_processor.split_sentences(cleaned)
        
        return {
            "original": text,
            "cleaned": cleaned,
            "sentences": sentences,
            "sentence_count": len(sentences),
            "character_count": len(cleaned)
        }
    
    def add_document_to_index(
        self,
        index: DocumentIndex,
        file_path: Optional[Union[str, Path]] = None,
        file_content: Optional[bytes] = None,
        file_name: Optional[str] = None,
        file_type: Optional[str] = None
    ) -> DocumentIndex:
        """
        Add a new document to an existing index
        
        Returns:
            Updated DocumentIndex
        """
        doc_id = str(uuid.uuid4())
        parsed, new_chunks = self.process_document(
            file_path=file_path,
            file_content=file_content,
            file_name=file_name,
            file_type=file_type,
            document_id=doc_id
        )
        
        # Add to documents
        index.documents[doc_id] = parsed
        
        # Add chunks to index
        if new_chunks:
            new_embeddings = np.vstack([c.embedding for c in new_chunks]).astype('float32')
            faiss.normalize_L2(new_embeddings)
            index.faiss_index.add(new_embeddings)
            
            index.chunks.extend(new_chunks)
            index.total_chunks = len(index.chunks)
            index.total_documents = len(index.documents)
        
        return index
