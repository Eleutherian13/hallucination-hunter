"""
Text processing utilities for Hallucination Hunter
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


from dataclasses import field

@dataclass
class TextChunk:
    """Represents a chunk of text with metadata"""
    content: str
    index: int
    start_char: int
    end_char: int
    metadata: Dict = field(default_factory=dict)


class TextProcessor:
    """Handles text processing operations"""
    
    # Common abbreviations that shouldn't be treated as sentence endings
    ABBREVIATIONS = {
        "dr.", "mr.", "mrs.", "ms.", "prof.", "sr.", "jr.",
        "vs.", "etc.", "i.e.", "e.g.", "fig.", "vol.", "no.",
        "inc.", "ltd.", "corp.", "co.", "dept.", "div.",
        "st.", "ave.", "blvd.", "rd.", "apt.", "fl.",
    }
    
    @classmethod
    def clean_text(cls, text: str) -> str:
        """
        Clean and normalize text
        
        - Remove excessive whitespace
        - Normalize line breaks
        - Remove control characters
        """
        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\t', ' ', text)
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Strip leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text.strip()
    
    @classmethod
    def split_sentences(cls, text: str) -> List[str]:
        """
        Split text into sentences with improved handling of edge cases
        """
        # Simple sentence splitting pattern
        # Handles: ., !, ?, and combinations like "..." or "?!"
        pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        
        # First, protect abbreviations
        protected_text = text
        for abbr in cls.ABBREVIATIONS:
            # Replace period with special marker
            protected_text = re.sub(
                re.escape(abbr), 
                abbr.replace('.', '<PERIOD>'), 
                protected_text, 
                flags=re.IGNORECASE
            )
        
        # Split sentences
        sentences = re.split(pattern, protected_text)
        
        # Restore periods in abbreviations
        sentences = [s.replace('<PERIOD>', '.') for s in sentences]
        
        # Clean up and filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    @classmethod
    def chunk_text(
        cls,
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        respect_sentences: bool = True
    ) -> List[TextChunk]:
        """
        Split text into overlapping chunks for processing
        
        Args:
            text: Input text to chunk
            chunk_size: Target size for each chunk (in characters)
            chunk_overlap: Overlap between consecutive chunks
            respect_sentences: Try to break at sentence boundaries
        
        Returns:
            List of TextChunk objects
        """
        if not text:
            return []
        
        text = cls.clean_text(text)
        chunks = []
        
        if respect_sentences:
            sentences = cls.split_sentences(text)
            chunks = cls._chunk_by_sentences(sentences, chunk_size, chunk_overlap, text)
        else:
            chunks = cls._chunk_by_characters(text, chunk_size, chunk_overlap)
        
        return chunks
    
    @classmethod
    def _chunk_by_sentences(
        cls, 
        sentences: List[str], 
        chunk_size: int, 
        overlap: int,
        original_text: str
    ) -> List[TextChunk]:
        """Create chunks respecting sentence boundaries"""
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_start = 0
        
        for sentence in sentences:
            sentence_len = len(sentence)
            
            if current_size + sentence_len > chunk_size and current_chunk:
                # Create chunk from accumulated sentences
                chunk_text = " ".join(current_chunk)
                chunk_end = chunk_start + len(chunk_text)
                
                chunks.append(TextChunk(
                    content=chunk_text,
                    index=len(chunks),
                    start_char=chunk_start,
                    end_char=chunk_end
                ))
                
                # Calculate overlap - keep last sentences that fit within overlap
                overlap_size = 0
                overlap_sentences = []
                for s in reversed(current_chunk):
                    if overlap_size + len(s) <= overlap:
                        overlap_sentences.insert(0, s)
                        overlap_size += len(s) + 1  # +1 for space
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_size = overlap_size
                chunk_start = chunk_end - overlap_size
            
            current_chunk.append(sentence)
            current_size += sentence_len + 1  # +1 for space
        
        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(TextChunk(
                content=chunk_text,
                index=len(chunks),
                start_char=chunk_start,
                end_char=chunk_start + len(chunk_text)
            ))
        
        return chunks
    
    @classmethod
    def _chunk_by_characters(
        cls, 
        text: str, 
        chunk_size: int, 
        overlap: int
    ) -> List[TextChunk]:
        """Create chunks by character count with overlap"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            
            # Try to break at a space
            if end < len(text):
                space_idx = text.rfind(" ", start, end)
                if space_idx > start:
                    end = space_idx
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                chunks.append(TextChunk(
                    content=chunk_text,
                    index=len(chunks),
                    start_char=start,
                    end_char=end
                ))
            
            start = end - overlap
            if start <= chunks[-1].start_char if chunks else 0:
                start = end  # Prevent infinite loop
        
        return chunks
    
    @classmethod
    def extract_sentences_with_positions(cls, text: str) -> List[Dict]:
        """
        Extract sentences with their character positions in the original text
        """
        sentences = cls.split_sentences(text)
        result = []
        current_pos = 0
        
        for sentence in sentences:
            # Find sentence in remaining text
            idx = text.find(sentence, current_pos)
            if idx != -1:
                result.append({
                    "text": sentence,
                    "start": idx,
                    "end": idx + len(sentence)
                })
                current_pos = idx + len(sentence)
        
        return result
    
    @classmethod
    def normalize_whitespace(cls, text: str) -> str:
        """Normalize all whitespace to single spaces"""
        return " ".join(text.split())
    
    @classmethod
    def remove_special_characters(cls, text: str, keep_punctuation: bool = True) -> str:
        """Remove special characters from text"""
        if keep_punctuation:
            pattern = r'[^\w\s.,!?;:\'"()-]'
        else:
            pattern = r'[^\w\s]'
        return re.sub(pattern, '', text)
    
    @classmethod
    def truncate_text(cls, text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to max length, adding suffix if truncated"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    
    @classmethod
    def highlight_text(
        cls, 
        text: str, 
        spans: List[Tuple[int, int]], 
        highlight_template: str = "**{text}**"
    ) -> str:
        """
        Highlight specific spans in text
        
        Args:
            text: Original text
            spans: List of (start, end) tuples to highlight
            highlight_template: Template for highlighting (must contain {text})
        
        Returns:
            Text with highlighted spans
        """
        # Sort spans by start position, reverse order for non-overlapping replacement
        sorted_spans = sorted(spans, key=lambda x: x[0], reverse=True)
        
        result = text
        for start, end in sorted_spans:
            original = result[start:end]
            highlighted = highlight_template.format(text=original)
            result = result[:start] + highlighted + result[end:]
        
        return result
    
    @classmethod
    def calculate_text_similarity(cls, text1: str, text2: str) -> float:
        """
        Calculate simple text similarity using character-level comparison
        Uses SequenceMatcher for basic similarity
        """
        from difflib import SequenceMatcher
        
        # Normalize texts
        t1 = cls.normalize_whitespace(text1.lower())
        t2 = cls.normalize_whitespace(text2.lower())
        
        return SequenceMatcher(None, t1, t2).ratio()
    
    @classmethod
    def find_differences(cls, text1: str, text2: str) -> List[Dict]:
        """
        Find differences between two texts
        
        Returns list of difference operations
        """
        from difflib import SequenceMatcher
        
        matcher = SequenceMatcher(None, text1, text2)
        differences = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                differences.append({
                    'operation': tag,
                    'original': text1[i1:i2],
                    'modified': text2[j1:j2],
                    'original_span': (i1, i2),
                    'modified_span': (j1, j2)
                })
        
        return differences
