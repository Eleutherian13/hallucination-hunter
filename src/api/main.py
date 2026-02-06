"""
FastAPI main application for Hallucination Hunter
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.api.routes import audit, benchmark, health
from src.config.settings import get_settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Hallucination Hunter API...")
    
    # Preload models if debug mode is off (production)
    if not settings.debug:
        from src.layers.ui_integration import get_integration_layer
        layer = get_integration_layer()
        layer.preload_models()
        logger.info("Models preloaded")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Hallucination Hunter API...")


# Create FastAPI app
app = FastAPI(
    title="Hallucination Hunter API",
    description="AI-assisted fact-checking system for LLM outputs",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(audit.router, prefix="/api", tags=["Audit"])
app.include_router(benchmark.router, prefix="/api", tags=["Benchmark"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Hallucination Hunter API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs"
    }
