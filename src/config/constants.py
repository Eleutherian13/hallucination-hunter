"""
System constants for Hallucination Hunter
"""

from enum import Enum
from typing import Dict, List, Tuple


# =============================================================================
# Claim Classification Categories
# =============================================================================

class ClaimCategory(str, Enum):
    """Classification categories for claims"""
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    UNVERIFIABLE = "unverifiable"


class VerificationStatus(str, Enum):
    """Verification status for processing"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Domain(str, Enum):
    """Supported domains for verification"""
    HEALTHCARE = "healthcare"
    LAW = "law"
    FINANCE = "finance"
    GENERAL = "general"


class ExportFormat(str, Enum):
    """Supported export formats"""
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    CSV = "csv"


# =============================================================================
# Color Scheme (RGB Values)
# =============================================================================

class Colors:
    """UI Color definitions"""
    # Primary colors
    PRIMARY = "#2563eb"  # Blue for trust
    PRIMARY_RGB = (37, 99, 235)
    
    # Claim status colors
    SUPPORTED = "#10b981"  # Green
    SUPPORTED_RGB = (16, 185, 129)
    
    CONTRADICTED = "#ef4444"  # Red
    CONTRADICTED_RGB = (239, 68, 68)
    
    UNVERIFIABLE = "#f59e0b"  # Yellow/Amber
    UNVERIFIABLE_RGB = (245, 158, 11)
    
    # Background colors
    BACKGROUND_LIGHT = "#ffffff"
    BACKGROUND_DARK = "#111827"
    
    # Text colors
    TEXT_PRIMARY = "#1f2937"
    TEXT_SECONDARY = "#6b7280"
    
    @classmethod
    def get_claim_color(cls, category: ClaimCategory) -> str:
        """Get color for claim category"""
        color_map = {
            ClaimCategory.SUPPORTED: cls.SUPPORTED,
            ClaimCategory.CONTRADICTED: cls.CONTRADICTED,
            ClaimCategory.UNVERIFIABLE: cls.UNVERIFIABLE,
        }
        return color_map.get(category, cls.TEXT_PRIMARY)


# =============================================================================
# Trust Score Zones
# =============================================================================

class TrustZone:
    """Trust score zone definitions"""
    HIGH = (80, 100, "Good", Colors.SUPPORTED)
    MEDIUM = (50, 80, "Review Needed", Colors.UNVERIFIABLE)
    LOW = (0, 50, "Unreliable", Colors.CONTRADICTED)
    
    @classmethod
    def get_zone(cls, score: float) -> Tuple[int, int, str, str]:
        """Get zone for a trust score"""
        if score >= 80:
            return cls.HIGH
        elif score >= 50:
            return cls.MEDIUM
        else:
            return cls.LOW


# =============================================================================
# Processing Constants
# =============================================================================

# Chunking defaults
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 100
MIN_CHUNK_SIZE = 100
MAX_CHUNK_SIZE = 2000

# Retrieval defaults
DEFAULT_TOP_K = 7
DEFAULT_SIMILARITY_THRESHOLD = 0.5
DEFAULT_HYBRID_WEIGHT_VECTOR = 0.6
DEFAULT_HYBRID_WEIGHT_KEYWORD = 0.4

# Verification thresholds
DEFAULT_ENTAILMENT_THRESHOLD = 0.8
DEFAULT_CONTRADICTION_THRESHOLD = 0.7
DEFAULT_ENTITY_MATCH_THRESHOLD = 0.9

# Drift detection
DEFAULT_DRIFT_REGENERATION_COUNT = 3
DEFAULT_DRIFT_VARIANCE_THRESHOLD = 0.2
DEFAULT_DRIFT_CONFIDENCE_PENALTY = 0.1

# Trust score weights
DEFAULT_WEIGHT_SUPPORTED_RATIO = 0.4
DEFAULT_WEIGHT_AVG_CONFIDENCE = 0.3
DEFAULT_WEIGHT_DRIFT_SCORE = 0.2
DEFAULT_WEIGHT_SEVERITY = 0.1


# =============================================================================
# Model Configurations
# =============================================================================

class ModelConfig:
    """Default model configurations"""
    # NLI Model
    NLI_MODEL_NAME = "microsoft/deberta-v3-base-mnli"
    NLI_MAX_LENGTH = 512
    
    # Embedding Model
    EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION = 384
    
    # Correction Model
    CORRECTION_MODEL_NAME = "t5-small"
    CORRECTION_MAX_LENGTH = 256
    
    # spaCy Model
    SPACY_MODEL_NAME = "en_core_web_sm"


# =============================================================================
# File Type Support
# =============================================================================

SUPPORTED_FILE_TYPES = {
    "pdf": ["application/pdf"],
    "txt": ["text/plain"],
    "docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    "html": ["text/html"],
    "md": ["text/markdown"],
}

MAX_FILE_SIZE_MB = 50
MAX_FILES_PER_UPLOAD = 10


# =============================================================================
# API Constants
# =============================================================================

API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Rate limiting
DEFAULT_RATE_LIMIT_REQUESTS = 100
DEFAULT_RATE_LIMIT_WINDOW = 60  # seconds

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


# =============================================================================
# Domain-Specific Configurations
# =============================================================================

DOMAIN_CONFIGS: Dict[Domain, Dict] = {
    Domain.HEALTHCARE: {
        "entity_types": ["MEDICATION", "DISEASE", "SYMPTOM", "DOSAGE", "LAB_VALUE"],
        "severity_multiplier": 2.0,
        "entity_match_threshold": 0.95,
        "critical_patterns": [
            r"\b\d+\s*(mg|ml|mcg|units?)\b",
            r"\b(type\s*[12]|stage\s*[I-IV])\b",
        ],
    },
    Domain.LAW: {
        "entity_types": ["CASE_CITATION", "STATUTE", "DATE", "PERSON", "ORGANIZATION"],
        "severity_multiplier": 1.8,
        "entity_match_threshold": 0.98,
        "critical_patterns": [
            r"\b\d+\s+U\.?S\.?\s+\d+\b",
            r"\b\d{4}\s+WL\s+\d+\b",
        ],
    },
    Domain.FINANCE: {
        "entity_types": ["MONEY", "PERCENT", "DATE", "ORGANIZATION", "METRIC"],
        "severity_multiplier": 1.9,
        "entity_match_threshold": 0.95,
        "critical_patterns": [
            r"\$[\d,]+\.?\d*",
            r"\b\d+\.?\d*%\b",
        ],
    },
    Domain.GENERAL: {
        "entity_types": ["PERSON", "ORG", "GPE", "DATE", "CARDINAL"],
        "severity_multiplier": 1.0,
        "entity_match_threshold": 0.9,
        "critical_patterns": [],
    },
}


# =============================================================================
# Severity Weights for Entity Types
# =============================================================================

ENTITY_SEVERITY_WEIGHTS: Dict[str, float] = {
    # Healthcare
    "MEDICATION": 2.0,
    "DOSAGE": 2.0,
    "LAB_VALUE": 1.8,
    "DISEASE": 1.5,
    "SYMPTOM": 1.3,
    
    # Law
    "CASE_CITATION": 2.0,
    "STATUTE": 1.8,
    
    # Finance
    "MONEY": 1.8,
    "PERCENT": 1.7,
    
    # General
    "PERSON": 1.2,
    "ORG": 1.2,
    "DATE": 1.3,
    "GPE": 1.1,
    "CARDINAL": 1.4,
}


# =============================================================================
# Confidence Levels
# =============================================================================

class ConfidenceLevel(str, Enum):
    """Human-readable confidence levels"""
    CERTAIN = "certain"
    LIKELY = "likely"
    UNCERTAIN = "uncertain"
    
    @classmethod
    def from_score(cls, score: float) -> "ConfidenceLevel":
        """Convert numeric score to confidence level"""
        if score >= 0.85:
            return cls.CERTAIN
        elif score >= 0.6:
            return cls.LIKELY
        else:
            return cls.UNCERTAIN
