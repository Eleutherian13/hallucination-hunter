"""
Application settings for Hallucination Hunter
Uses pydantic-settings for environment variable management
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.config.constants import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CONTRADICTION_THRESHOLD,
    DEFAULT_DRIFT_CONFIDENCE_PENALTY,
    DEFAULT_DRIFT_REGENERATION_COUNT,
    DEFAULT_DRIFT_VARIANCE_THRESHOLD,
    DEFAULT_ENTAILMENT_THRESHOLD,
    DEFAULT_ENTITY_MATCH_THRESHOLD,
    DEFAULT_HYBRID_WEIGHT_KEYWORD,
    DEFAULT_HYBRID_WEIGHT_VECTOR,
    DEFAULT_RATE_LIMIT_REQUESTS,
    DEFAULT_RATE_LIMIT_WINDOW,
    DEFAULT_SIMILARITY_THRESHOLD,
    DEFAULT_TOP_K,
    DEFAULT_WEIGHT_AVG_CONFIDENCE,
    DEFAULT_WEIGHT_DRIFT_SCORE,
    DEFAULT_WEIGHT_SEVERITY,
    DEFAULT_WEIGHT_SUPPORTED_RATIO,
    ModelConfig,
)


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ==========================================================================
    # Application Settings
    # ==========================================================================
    app_name: str = "Hallucination Hunter"
    app_version: str = "2.0.0"
    app_env: str = "development"
    debug: bool = True
    
    # ==========================================================================
    # Server Configuration
    # ==========================================================================
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    ui_port: int = 8501
    
    # ==========================================================================
    # Model Configuration
    # ==========================================================================
    nli_model_name: str = ModelConfig.NLI_MODEL_NAME
    nli_device: str = "cpu"
    
    embedding_model_name: str = ModelConfig.EMBEDDING_MODEL_NAME
    embedding_device: str = "cpu"
    
    correction_model_name: str = ModelConfig.CORRECTION_MODEL_NAME
    correction_device: str = "cpu"
    
    # ==========================================================================
    # Processing Configuration
    # ==========================================================================
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    
    retrieval_top_k: int = DEFAULT_TOP_K
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD
    hybrid_weight_vector: float = DEFAULT_HYBRID_WEIGHT_VECTOR
    hybrid_weight_keyword: float = DEFAULT_HYBRID_WEIGHT_KEYWORD
    
    # ==========================================================================
    # Verification Thresholds
    # ==========================================================================
    entailment_threshold: float = DEFAULT_ENTAILMENT_THRESHOLD
    contradiction_threshold: float = DEFAULT_CONTRADICTION_THRESHOLD
    entity_match_threshold: float = DEFAULT_ENTITY_MATCH_THRESHOLD
    
    # ==========================================================================
    # Drift Detection
    # ==========================================================================
    drift_regeneration_count: int = DEFAULT_DRIFT_REGENERATION_COUNT
    drift_variance_threshold: float = DEFAULT_DRIFT_VARIANCE_THRESHOLD
    drift_confidence_penalty: float = DEFAULT_DRIFT_CONFIDENCE_PENALTY
    
    # ==========================================================================
    # Trust Score Weights
    # ==========================================================================
    weight_supported_ratio: float = DEFAULT_WEIGHT_SUPPORTED_RATIO
    weight_avg_confidence: float = DEFAULT_WEIGHT_AVG_CONFIDENCE
    weight_drift_score: float = DEFAULT_WEIGHT_DRIFT_SCORE
    weight_severity: float = DEFAULT_WEIGHT_SEVERITY
    
    # ==========================================================================
    # Database Configuration
    # ==========================================================================
    database_url: str = "sqlite:///./data/hallucination_hunter.db"
    redis_url: Optional[str] = None
    
    # ==========================================================================
    # Caching Configuration
    # ==========================================================================
    cache_enabled: bool = True
    cache_ttl: int = 3600
    cache_dir: str = "./cache"
    
    # ==========================================================================
    # Logging Configuration
    # ==========================================================================
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # ==========================================================================
    # API Security
    # ==========================================================================
    api_key_enabled: bool = False
    api_key_secret: Optional[str] = None
    rate_limit_enabled: bool = True
    rate_limit_requests: int = DEFAULT_RATE_LIMIT_REQUESTS
    rate_limit_window: int = DEFAULT_RATE_LIMIT_WINDOW
    
    # ==========================================================================
    # External Services
    # ==========================================================================
    llm_api_key: Optional[str] = None
    llm_model_name: Optional[str] = None
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.app_env.lower() == "production"
    
    @property
    def base_dir(self) -> Path:
        """Get the base directory of the project"""
        return Path(__file__).parent.parent.parent
    
    @property
    def data_dir(self) -> Path:
        """Get the data directory"""
        data_path = self.base_dir / "data"
        data_path.mkdir(parents=True, exist_ok=True)
        return data_path
    
    @property
    def logs_dir(self) -> Path:
        """Get the logs directory"""
        logs_path = self.base_dir / "logs"
        logs_path.mkdir(parents=True, exist_ok=True)
        return logs_path
    
    @property
    def models_dir(self) -> Path:
        """Get the models cache directory"""
        models_path = self.base_dir / "models"
        models_path.mkdir(parents=True, exist_ok=True)
        return models_path


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance for convenience
settings = get_settings()
