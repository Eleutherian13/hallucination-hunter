"""
Layers module for Hallucination Hunter 8-layer architecture
"""

from src.layers.ingestion import IngestionLayer, DocumentIndex
from src.layers.claim_intelligence import ClaimIntelligenceLayer, Claim
from src.layers.retrieval import RetrievalLayer, EvidenceResult
from src.layers.verification import VerificationLayer, VerificationResult
from src.layers.drift import DriftMitigationLayer
from src.layers.scoring import ScoringLayer, TrustScore
from src.layers.correction import CorrectionLayer
from src.layers.ui_integration import UIIntegrationLayer
