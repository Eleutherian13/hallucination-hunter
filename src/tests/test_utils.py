"""
Tests for utility modules
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os


class TestTextProcessor:
    """Tests for text processing utilities"""
    
    def test_text_processor_initialization(self):
        """Test TextProcessor instantiation"""
        from src.utils.text_processing import TextProcessor
        
        processor = TextProcessor()
        assert processor is not None
    
    def test_split_sentences(self):
        """Test sentence splitting"""
        from src.utils.text_processing import TextProcessor
        
        processor = TextProcessor()
        text = "This is sentence one. This is sentence two. And here's another!"
        
        sentences = processor.split_sentences(text)
        assert len(sentences) >= 2
    
    def test_chunk_text(self):
        """Test text chunking"""
        from src.utils.text_processing import TextProcessor
        
        processor = TextProcessor()
        text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 20
        
        chunks = processor.chunk_text(text, chunk_size=100, chunk_overlap=20)
        assert len(chunks) > 0
        assert all(chunk.content for chunk in chunks)
    
    def test_normalize_whitespace(self):
        """Test whitespace normalization"""
        from src.utils.text_processing import TextProcessor
        
        processor = TextProcessor()
        text = "  Hello   World  \n\n Test  "
        
        normalized = processor.normalize_whitespace(text)
        assert "  " not in normalized.strip()  # No double spaces in middle


class TestFileHandlers:
    """Tests for file handling utilities"""
    
    def test_document_parser_initialization(self):
        """Test DocumentParser instantiation"""
        from src.utils.file_handlers import DocumentParser
        
        parser = DocumentParser()
        assert parser is not None
    
    def test_file_handler_supported_check(self):
        """Test checking supported extensions"""
        from src.utils.file_handlers import FileHandler
        
        # Should have common extensions
        assert ".txt" in FileHandler.SUPPORTED_EXTENSIONS
        assert ".pdf" in FileHandler.SUPPORTED_EXTENSIONS
    
    def test_parse_txt_file(self):
        """Test parsing text file"""
        from src.utils.file_handlers import DocumentParser
        
        parser = DocumentParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test content for parsing")
            temp_path = f.name
        
        try:
            result = parser.parse(file_path=temp_path)
            assert result is not None
            assert "Test content" in result.content
        finally:
            os.unlink(temp_path)


class TestCaching:
    """Tests for caching utilities"""
    
    def test_cache_manager_initialization(self):
        """Test CacheManager instantiation"""
        from src.utils.caching import CacheManager
        
        cache = CacheManager()
        assert cache is not None
    
    def test_cache_set_get(self):
        """Test basic cache operations"""
        from src.utils.caching import CacheManager
        
        cache = CacheManager()
        
        cache.set("test_key", "test_value")
        result = cache.get("test_key")
        
        assert result == "test_value"
    
    def test_cache_miss(self):
        """Test cache miss returns None"""
        from src.utils.caching import CacheManager
        
        cache = CacheManager()
        
        result = cache.get("nonexistent_key")
        assert result is None


class TestValidation:
    """Tests for input validation"""
    
    def test_validation_result_success(self):
        """Test ValidationResult success factory"""
        from src.utils.validation import ValidationResult
        
        result = ValidationResult.success()
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validation_result_failure(self):
        """Test ValidationResult failure factory"""
        from src.utils.validation import ValidationResult
        
        result = ValidationResult.failure(errors=["Error 1", "Error 2"])
        assert result.is_valid is False
        assert len(result.errors) == 2
    
    def test_input_validator_file_validation(self):
        """Test file validation"""
        from src.utils.validation import InputValidator
        
        validator = InputValidator()
        
        # Test with valid file path
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Valid content")
            temp_path = f.name
        
        try:
            result = validator.validate_file(file_path=temp_path)
            assert result.is_valid
        finally:
            os.unlink(temp_path)
    
    def test_input_validator_text_input(self):
        """Test text input validation"""
        from src.utils.validation import InputValidator
        
        validator = InputValidator()
        
        # Valid output
        result = validator.validate_text_input("This is a valid LLM output with multiple sentences.")
        assert result.is_valid
        
        # Invalid empty output
        result = validator.validate_text_input("")
        assert not result.is_valid


class TestLogging:
    """Tests for logging configuration"""
    
    def test_get_logger(self):
        """Test logger creation"""
        from src.utils.logging_config import get_logger
        
        logger = get_logger("test_module")
        assert logger is not None
        assert logger.name == "test_module"


class TestConstants:
    """Tests for configuration constants"""
    
    def test_domain_enum(self):
        """Test Domain enum values"""
        from src.config.constants import Domain
        
        assert Domain.GENERAL.value == "general"
        assert Domain.FINANCE.value == "finance"
        assert Domain.LAW.value == "law"
    
    def test_claim_category_enum(self):
        """Test ClaimCategory enum values"""
        from src.config.constants import ClaimCategory
        
        assert ClaimCategory.SUPPORTED.value == "supported"
        assert ClaimCategory.CONTRADICTED.value == "contradicted"
        assert ClaimCategory.UNVERIFIABLE.value == "unverifiable"
    
    def test_model_config(self):
        """Test model configuration constants"""
        from src.config.constants import ModelConfig
        
        assert ModelConfig.NLI_MODEL_NAME is not None
        assert ModelConfig.EMBEDDING_MODEL_NAME is not None
        assert ModelConfig.CORRECTION_MODEL_NAME is not None


class TestSettings:
    """Tests for application settings"""
    
    def test_settings_loading(self):
        """Test settings are loaded correctly"""
        from src.config.settings import get_settings
        
        settings = get_settings()
        
        assert settings.app_name == "Hallucination Hunter"
        assert settings.app_version == "2.0.0"
    
    def test_settings_model_names(self):
        """Test model name settings"""
        from src.config.settings import get_settings
        
        settings = get_settings()
        
        assert "deberta" in settings.nli_model_name.lower()
        assert "minilm" in settings.embedding_model_name.lower() or "sentence-transformers" in settings.embedding_model_name.lower()
