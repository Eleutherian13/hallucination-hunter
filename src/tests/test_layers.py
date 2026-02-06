"""
Unit tests for layers
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass


class TestIngestionLayer:
    """Tests for ingestion layer"""
    
    def test_ingestion_layer_initialization(self):
        """Test ingestion layer initialization"""
        from src.layers.ingestion import IngestionLayer
        
        with patch("src.layers.ingestion.EmbeddingModel"):
            layer = IngestionLayer()
            assert layer is not None
    
    @patch("src.layers.ingestion.EmbeddingModel")
    @patch("src.layers.ingestion.DocumentParser")
    def test_process_documents(self, mock_parser, mock_embedding):
        """Test document processing"""
        from src.layers.ingestion import IngestionLayer
        
        mock_parser_instance = Mock()
        mock_parser_instance.parse.return_value = "Document content"
        mock_parser.return_value = mock_parser_instance
        
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_embedding.return_value = mock_model
        
        layer = IngestionLayer()
        
        sources = [{"name": "test.txt", "content": "Test content", "type": "txt"}]
        result = layer.process_documents(sources)
        
        assert result is not None


class TestClaimIntelligenceLayer:
    """Tests for claim intelligence layer"""
    
    def test_claim_intelligence_initialization(self):
        """Test claim intelligence layer initialization"""
        from src.layers.claim_intelligence import ClaimIntelligenceLayer
        
        with patch("src.layers.claim_intelligence.spacy.load"):
            layer = ClaimIntelligenceLayer()
            assert layer is not None
    
    @patch("src.layers.claim_intelligence.spacy.load")
    def test_extract_claims(self, mock_spacy):
        """Test claim extraction"""
        from src.layers.claim_intelligence import ClaimIntelligenceLayer
        
        mock_nlp = Mock()
        mock_doc = Mock()
        mock_sent = Mock()
        mock_sent.text = "This is a test sentence."
        mock_sent.__iter__ = Mock(return_value=iter([]))
        mock_doc.sents = [mock_sent]
        mock_doc.ents = []
        mock_nlp.return_value = mock_doc
        mock_spacy.return_value = mock_nlp
        
        layer = ClaimIntelligenceLayer()
        
        text = "This is a test sentence."
        claims = layer.extract_claims(text)
        
        assert isinstance(claims, list)


class TestRetrievalLayer:
    """Tests for retrieval layer"""
    
    def test_retrieval_layer_initialization(self):
        """Test retrieval layer initialization"""
        from src.layers.retrieval import RetrievalLayer
        
        with patch("src.layers.retrieval.EmbeddingModel"):
            layer = RetrievalLayer()
            assert layer is not None
    
    @patch("src.layers.retrieval.EmbeddingModel")
    def test_hybrid_search(self, mock_embedding):
        """Test hybrid search"""
        from src.layers.retrieval import RetrievalLayer
        
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_model.load.return_value = None
        mock_embedding.return_value = mock_model
        
        layer = RetrievalLayer()
        
        # Test would require mock DocumentIndex
        assert layer is not None


class TestVerificationLayer:
    """Tests for verification layer"""
    
    def test_verification_layer_initialization(self):
        """Test verification layer initialization"""
        from src.layers.verification import VerificationLayer
        
        with patch("src.layers.verification.NLIModel"):
            layer = VerificationLayer()
            assert layer is not None
    
    @patch("src.layers.verification.NLIModel")
    def test_verify_claim(self, mock_nli):
        """Test claim verification"""
        from src.layers.verification import VerificationLayer
        from src.config.constants import ClaimCategory
        
        mock_model = Mock()
        mock_model.classify_with_multiple_evidence.return_value = {
            "label": "entailment",
            "confidence": 0.9
        }
        mock_nli.return_value = mock_model
        
        layer = VerificationLayer()
        
        # Create mock claim and evidence
        mock_claim = Mock()
        mock_claim.claim_id = "test_1"
        mock_claim.text = "Test claim"
        mock_claim.entities = []
        mock_claim.numerical_values = []
        
        mock_evidence = Mock()
        mock_evidence.texts = ["Test evidence"]
        mock_evidence.citations = ["Source, page 1"]
        mock_evidence.scores = [0.9]
        
        result = layer.verify_claim(mock_claim, mock_evidence)
        
        assert result is not None
        assert hasattr(result, "category")


class TestScoringLayer:
    """Tests for scoring layer"""
    
    def test_scoring_layer_initialization(self):
        """Test scoring layer initialization"""
        from src.layers.scoring import ScoringLayer
        from src.config.constants import Domain
        
        layer = ScoringLayer(domain=Domain.GENERAL)
        assert layer is not None
    
    def test_calculate_trust_score_empty(self):
        """Test trust score with no results"""
        from src.layers.scoring import ScoringLayer
        
        layer = ScoringLayer()
        score = layer.calculate_trust_score([])
        
        assert score.score == 0
        assert score.total_claims == 0
    
    def test_calculate_trust_score_with_results(self):
        """Test trust score calculation"""
        from src.layers.scoring import ScoringLayer, TrustLevel
        from src.config.constants import ClaimCategory
        
        layer = ScoringLayer()
        
        # Mock verification results
        mock_results = []
        for i in range(5):
            result = Mock()
            result.claim_id = f"claim_{i}"
            result.claim_text = f"Claim {i}"
            result.category = ClaimCategory.SUPPORTED if i < 3 else ClaimCategory.CONTRADICTED
            result.confidence = 0.8
            mock_results.append(result)
        
        score = layer.calculate_trust_score(mock_results)
        
        assert score.total_claims == 5
        assert score.category_counts["supported"] == 3
        assert score.category_counts["contradicted"] == 2


class TestDriftMitigationLayer:
    """Tests for drift mitigation layer"""
    
    def test_drift_layer_initialization(self):
        """Test drift mitigation layer initialization"""
        from src.layers.drift import DriftMitigationLayer
        
        with patch("src.layers.drift.DriftDetector"):
            layer = DriftMitigationLayer()
            assert layer is not None


class TestCorrectionLayer:
    """Tests for correction layer"""
    
    def test_correction_layer_initialization(self):
        """Test correction layer initialization"""
        from src.layers.correction import CorrectionLayer
        
        with patch("src.layers.correction.CorrectionModel"):
            layer = CorrectionLayer()
            assert layer is not None
    
    def test_export_json(self):
        """Test JSON export"""
        from src.layers.correction import CorrectionLayer, AuditReport
        from src.layers.scoring import TrustScore, TrustLevel, ScoreBreakdown
        from datetime import datetime
        
        with patch("src.layers.correction.CorrectionModel"):
            layer = CorrectionLayer()
            
            # Create mock report
            breakdown = ScoreBreakdown(
                supported_ratio=0.6,
                supported_contribution=24,
                avg_confidence=0.8,
                confidence_contribution=24,
                drift_score=0.1,
                drift_contribution=18,
                severity_score=0.2,
                severity_contribution=8
            )
            
            trust_score = TrustScore(
                score=74,
                level=TrustLevel.MEDIUM,
                breakdown=breakdown,
                category_counts={"supported": 3, "contradicted": 1, "unverifiable": 1},
                total_claims=5,
                flagged_claims=["Test claim"],
                recommendations=["Review contradicted claims"],
                zone=(70, 100, "High Trust", "#10b981")
            )
            
            report = AuditReport(
                report_id="test-123",
                timestamp=datetime.now(),
                llm_output="Test output",
                trust_score=trust_score,
                annotated_claims=[],
                summary="Test summary",
                document_sources=["test.pdf"]
            )
            
            json_output = layer.export_json(report)
            
            assert "test-123" in json_output
            assert "trust_score" in json_output
