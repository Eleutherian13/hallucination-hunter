"""
Benchmark API endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import time
import statistics

from src.layers.ui_integration import get_integration_layer, AuditRequest
from src.config.constants import Domain
from src.utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


class BenchmarkItem(BaseModel):
    """Single benchmark test item"""
    llm_output: str
    source_text: str
    expected_supported: Optional[int] = None
    expected_contradicted: Optional[int] = None


class BenchmarkRequest(BaseModel):
    """Benchmark request body"""
    name: str = Field(default="custom", description="Benchmark name")
    items: List[BenchmarkItem] = Field(...)
    domain: str = Field(default="general")


class BenchmarkResult(BaseModel):
    """Individual benchmark result"""
    item_index: int
    trust_score: float
    total_claims: int
    supported: int
    contradicted: int
    unverifiable: int
    processing_time: float
    accuracy: Optional[float] = None


class BenchmarkSummary(BaseModel):
    """Benchmark summary"""
    name: str
    timestamp: str
    total_items: int
    avg_trust_score: float
    avg_processing_time: float
    min_processing_time: float
    max_processing_time: float
    total_claims_analyzed: int
    overall_supported_ratio: float
    overall_contradicted_ratio: float
    avg_accuracy: Optional[float] = None
    results: List[BenchmarkResult]


@router.post("/benchmark", response_model=BenchmarkSummary)
async def run_benchmark(request: BenchmarkRequest):
    """
    Run benchmark on multiple test items
    
    Useful for evaluating system performance on a dataset.
    """
    try:
        logger.info(f"Starting benchmark '{request.name}' with {len(request.items)} items")
        
        try:
            domain = Domain(request.domain.lower())
        except ValueError:
            domain = Domain.GENERAL
        
        integration = get_integration_layer()
        results = []
        all_claims = 0
        all_supported = 0
        all_contradicted = 0
        accuracies = []
        
        for idx, item in enumerate(request.items):
            start_time = time.time()
            
            audit_request = AuditRequest(
                sources=[{
                    "name": f"source_{idx}.txt",
                    "content": item.source_text,
                    "type": "txt"
                }],
                llm_output=item.llm_output,
                domain=domain,
                generate_corrections=False
            )
            
            report = await integration.run_audit_async(audit_request)
            
            processing_time = time.time() - start_time
            stats = report.to_dict()["statistics"]
            
            # Calculate accuracy if expected values provided
            accuracy = None
            if item.expected_supported is not None and item.expected_contradicted is not None:
                expected_total = item.expected_supported + item.expected_contradicted
                if expected_total > 0:
                    correct = 0
                    if item.expected_supported == stats["supported"]:
                        correct += item.expected_supported
                    if item.expected_contradicted == stats["contradicted"]:
                        correct += item.expected_contradicted
                    accuracy = correct / expected_total
                    accuracies.append(accuracy)
            
            result = BenchmarkResult(
                item_index=idx,
                trust_score=report.trust_score.score,
                total_claims=stats["total_claims"],
                supported=stats["supported"],
                contradicted=stats["contradicted"],
                unverifiable=stats["unverifiable"],
                processing_time=processing_time,
                accuracy=accuracy
            )
            results.append(result)
            
            all_claims += stats["total_claims"]
            all_supported += stats["supported"]
            all_contradicted += stats["contradicted"]
        
        # Calculate summary statistics
        trust_scores = [r.trust_score for r in results]
        processing_times = [r.processing_time for r in results]
        
        summary = BenchmarkSummary(
            name=request.name,
            timestamp=datetime.now().isoformat(),
            total_items=len(request.items),
            avg_trust_score=statistics.mean(trust_scores),
            avg_processing_time=statistics.mean(processing_times),
            min_processing_time=min(processing_times),
            max_processing_time=max(processing_times),
            total_claims_analyzed=all_claims,
            overall_supported_ratio=all_supported / all_claims if all_claims > 0 else 0,
            overall_contradicted_ratio=all_contradicted / all_claims if all_claims > 0 else 0,
            avg_accuracy=statistics.mean(accuracies) if accuracies else None,
            results=results
        )
        
        logger.info(f"Benchmark '{request.name}' complete: avg score {summary.avg_trust_score:.1f}")
        
        return summary
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmark/presets")
async def list_preset_benchmarks():
    """
    List available preset benchmarks
    """
    return {
        "presets": [
            {
                "name": "factual_accuracy",
                "description": "Tests factual claim verification accuracy",
                "items_count": 10
            },
            {
                "name": "medical_claims",
                "description": "Medical domain claim verification",
                "items_count": 15
            },
            {
                "name": "hallucination_detection",
                "description": "Tests detection of fabricated claims",
                "items_count": 20
            }
        ]
    }


@router.post("/benchmark/preset/{preset_name}")
async def run_preset_benchmark(preset_name: str):
    """
    Run a preset benchmark
    
    Note: Preset benchmarks would need actual test data in production.
    """
    presets = {
        "factual_accuracy": {
            "items": [
                BenchmarkItem(
                    llm_output="Paris is the capital of France. The Eiffel Tower was built in 1889.",
                    source_text="Paris is the capital and most populous city of France. The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris, built in 1889.",
                    expected_supported=2,
                    expected_contradicted=0
                ),
                BenchmarkItem(
                    llm_output="The Earth is flat. Water boils at 100°C at sea level.",
                    source_text="The Earth is an oblate spheroid. Water boils at 100 degrees Celsius (212°F) at sea level.",
                    expected_supported=1,
                    expected_contradicted=1
                )
            ],
            "domain": "general"
        },
        "medical_claims": {
            "items": [
                BenchmarkItem(
                    llm_output="Aspirin is used to treat pain and reduce fever. It was invented in 1899.",
                    source_text="Aspirin, also known as acetylsalicylic acid, is a medication used to treat pain, fever, and inflammation. It was first synthesized in 1897 and marketed in 1899.",
                    expected_supported=2,
                    expected_contradicted=0
                )
            ],
            "domain": "medical"
        },
        "hallucination_detection": {
            "items": [
                BenchmarkItem(
                    llm_output="The study found that treatment X increased survival by 75%. Researchers at Harvard conducted this trial.",
                    source_text="The study conducted at Stanford showed that treatment X improved survival rates by 45% compared to placebo.",
                    expected_supported=0,
                    expected_contradicted=2
                )
            ],
            "domain": "scientific"
        }
    }
    
    if preset_name not in presets:
        raise HTTPException(
            status_code=404,
            detail=f"Preset not found. Available: {list(presets.keys())}"
        )
    
    preset = presets[preset_name]
    
    request = BenchmarkRequest(
        name=preset_name,
        items=preset["items"],
        domain=preset["domain"]
    )
    
    return await run_benchmark(request)


@router.get("/benchmark/metrics")
async def get_system_metrics():
    """
    Get system performance metrics
    """
    import psutil
    
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        
        return {
            "cpu_usage_percent": cpu_percent,
            "memory_used_gb": memory.used / (1024**3),
            "memory_available_gb": memory.available / (1024**3),
            "memory_percent": memory.percent,
            "timestamp": datetime.now().isoformat()
        }
    except ImportError:
        return {
            "error": "psutil not installed",
            "timestamp": datetime.now().isoformat()
        }
