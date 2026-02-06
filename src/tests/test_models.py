"""
Tests for ML models - NLI, Embedding, Correction, Drift
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock


class TestNLIModel:
    """Tests for NLI classification model"""
    
    def test_nli_model_initialization(self):
        """Test NLI model lazy loading"""
        from src.models.nli_model import NLIModel
        
        model = NLIModel()
        assert model._model is None
        assert model._loaded is False
    
    @patch("src.models.nli_model.AutoModelForSequenceClassification")
    @patch("src.models.nli_model.AutoTokenizer")
    def test_nli_classify(self, mock_tokenizer, mock_model):
        """Test NLI classification"""
        from src.models.nli_model import NLIModel
        from src.config.constants import ClaimCategory
        import torch
        
        # Setup mocks
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_tokenizer_instance.return_value = {"input_ids": torch.tensor([[1, 2, 3]])}
        mock_tokenizer_instance.to.return_value = mock_tokenizer_instance
        
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_model_instance.return_value = MagicMock(
            logits=torch.tensor([[0.1, 0.1, 0.9]])  # High entailment
        )
        
        model = NLIModel()
        result = model.classify(
            claim="Paris is a city in France.",
            evidence="Paris is the capital of France."
        )
        
        assert result.category in [ClaimCategory.SUPPORTED, ClaimCategory.CONTRADICTED, ClaimCategory.UNVERIFIABLE]
        assert 0 <= result.confidence <= 1
    
    @patch("src.models.nli_model.AutoModelForSequenceClassification")
    @patch("src.models.nli_model.AutoTokenizer")
    def test_nli_classify_batch(self, mock_tokenizer, mock_model):
        """Test batch NLI classification"""
        from src.models.nli_model import NLIModel
        import torch
        
        # Setup mocks
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_tokenizer_instance.return_value = {"input_ids": torch.tensor([[1, 2, 3], [4, 5, 6]])}
        mock_tokenizer_instance.to.return_value = mock_tokenizer_instance
        
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_model_instance.return_value = MagicMock(
            logits=torch.tensor([[0.1, 0.1, 0.9], [0.9, 0.05, 0.05]])
        )
        
        model = NLIModel()
        results = model.classify_batch(
            claims=["Claim 1", "Claim 2"],
            evidences=["Evidence 1", "Evidence 2"]
        )
        
        assert len(results) == 2


class TestEmbeddingModel:
    """Tests for embedding model"""
    
    def test_embedding_model_initialization(self):
        """Test embedding model lazy loading"""
        from src.models.embedding_model import EmbeddingModel
        
        model = EmbeddingModel()
        assert model._model is None
    
    @patch("src.models.embedding_model.SentenceTransformer")
    def test_embedding_encode(self, mock_st):
        """Test text encoding"""
        from src.models.embedding_model import EmbeddingModel
        
        mock_model = Mock()
        mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3]])
        mock_model.get_sentence_embedding_dimension.return_value = 3
        mock_st.return_value = mock_model
        
        model = EmbeddingModel()
        embeddings = model.encode("Test text")
        
        assert isinstance(embeddings, np.ndarray)
    
    @patch("src.models.embedding_model.SentenceTransformer")
    def test_embedding_similarity(self, mock_st):
        """Test similarity calculation"""
        from src.models.embedding_model import EmbeddingModel
        
        mock_model = Mock()
        mock_model.encode.side_effect = [
            np.array([[1.0, 0.0, 0.0]]),
            np.array([[0.9, 0.1, 0.0]])
        ]
        mock_model.get_sentence_embedding_dimension.return_value = 3
        mock_st.return_value = mock_model
        
        model = EmbeddingModel()
        similarity = model.similarity("Text A", "Text B")
        
        assert 0 <= similarity <= 1


class TestCorrectionModel:
    """Tests for correction model"""
    
    def test_correction_model_initialization(self):
        """Test correction model lazy loading"""
        from src.models.correction_model import CorrectionModel
        
        model = CorrectionModel()
        assert model._model is None
        assert model._loaded is False
    
    @patch("src.models.correction_model.T5ForConditionalGeneration")
    @patch("src.models.correction_model.T5Tokenizer")
    def test_generate_correction(self, mock_tokenizer, mock_model):
        """Test correction generation"""
        from src.models.correction_model import CorrectionModel
        import torch
        
        # Setup mocks
        mock_tokenizer_instance = MagicMock()
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_tokenizer_instance.return_value = MagicMock()
        mock_tokenizer_instance.return_value.to.return_value = mock_tokenizer_instance.return_value
        mock_tokenizer_instance.decode.return_value = "Corrected claim text"
        
        mock_model_instance = MagicMock()
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_model_instance.generate.return_value = torch.tensor([[1, 2, 3]])
        
        model = CorrectionModel()
        result = model.generate_correction(
            claim="Wrong claim",
            evidence="Correct evidence"
        )
        
        assert result.corrected_claim is not None
        assert result.original_claim == "Wrong claim"


class TestDriftDetector:
    """Tests for drift detection"""
    
    @patch("src.models.drift_detector.EmbeddingModel")
    def test_drift_detector_initialization(self, mock_embedding):
        """Test drift detector initialization"""
        from src.models.drift_detector import DriftDetector
        
        detector = DriftDetector()
        assert detector is not None
    
    @patch("src.models.drift_detector.EmbeddingModel")
    def test_analyze_claim_drift(self, mock_embedding):
        """Test claim drift analysis"""
        from src.models.drift_detector import DriftDetector
        
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([[0.5, 0.5, 0.5]])
        mock_model._cosine_similarity = lambda a, b: 0.9
        mock_embedding.return_value = mock_model
        
        detector = DriftDetector()
        result = detector.analyze_claim_drift(
            claim="Test claim",
            variants=["Variant 1", "Variant 2"]
        )
        
        assert result.claim == "Test claim"
        assert 0 <= result.drift_score <= 1
