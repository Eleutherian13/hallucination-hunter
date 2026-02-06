"""
Health check endpoints
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime

from src.config.settings import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: str
    models_loaded: Dict[str, bool]
    settings: Dict[str, Optional[str]]


class ReadinessResponse(BaseModel):
    """Readiness check response"""
    ready: bool
    models_ready: bool
    database_ready: bool
    cache_ready: bool


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    
    Returns current system status and loaded models
    """
    settings = get_settings()
    
    # Check model status
    models_loaded = {
        "embedding": False,
        "nli": False,
        "correction": False
    }
    
    try:
        from src.layers.ui_integration import get_integration_layer
        layer = get_integration_layer()
        models_loaded["embedding"] = layer.embedding_model._model is not None
        models_loaded["nli"] = layer.nli_model._model is not None
        models_loaded["correction"] = layer.correction.correction_model._model is not None
    except Exception:
        pass
    
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        timestamp=datetime.now().isoformat(),
        models_loaded=models_loaded,
        settings={
            "nli_model": settings.nli_model_name,
            "embedding_model": settings.embedding_model_name,
            "cache_enabled": str(settings.cache_enabled)
        }
    )


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    Readiness check endpoint
    
    Returns whether the system is ready to handle requests
    """
    models_ready = False
    database_ready = True  # No database in current implementation
    cache_ready = True
    
    try:
        from src.layers.ui_integration import get_integration_layer
        layer = get_integration_layer()
        
        # Check if models can load
        layer.embedding_model.load()
        layer.nli_model.load()
        models_ready = True
        
        # Check cache
        from src.utils.caching import get_cache
        cache = get_cache()
        cache_ready = cache is not None
        
    except Exception:
        pass
    
    ready = models_ready and database_ready and cache_ready
    
    return ReadinessResponse(
        ready=ready,
        models_ready=models_ready,
        database_ready=database_ready,
        cache_ready=cache_ready
    )


@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"pong": True, "timestamp": datetime.now().isoformat()}


@router.get("/version")
async def version():
    """Get API version"""
    return {
        "version": "2.0.0",
        "name": "Hallucination Hunter",
        "api_version": "v1"
    }
