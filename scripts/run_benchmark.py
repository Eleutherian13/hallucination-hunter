#!/usr/bin/env python
"""
Run benchmark suite for Hallucination Hunter
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src import create_audit
from src.config.constants import Domain


# Benchmark test cases
BENCHMARK_CASES = [
    {
        "name": "Factual Accuracy - Eiffel Tower",
        "source": """
        The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris, 
        France. It is named after the engineer Gustave Eiffel, whose company designed and 
        built the tower. Constructed from 1887 to 1889, it was the tallest man-made structure 
        in the world until 1930. The tower is 330 metres tall.
        """,
        "llm_output": """
        The Eiffel Tower is located in Paris, France. It was built by Gustave Eiffel 
        and completed in 1889. The tower stands at 324 meters tall and was the tallest 
        structure in the world until 1931.
        """,
        "domain": "general",
        "expected_contradicted": 2  # Height is wrong, date is slightly off
    },
    {
        "name": "Complete Hallucination",
        "source": """
        Water is composed of hydrogen and oxygen atoms. The chemical formula is H2O.
        Water freezes at 0 degrees Celsius and boils at 100 degrees Celsius at sea level.
        """,
        "llm_output": """
        Water is composed of helium and neon atoms. The chemical formula is HeNe.
        Water freezes at 10 degrees Celsius and boils at 200 degrees Celsius.
        """,
        "domain": "scientific",
        "expected_contradicted": 4
    },
    {
        "name": "Fully Supported Claims",
        "source": """
        The Sun is the star at the center of the Solar System. It is a nearly perfect 
        ball of hot plasma. The Sun's core temperature is approximately 15 million degrees 
        Celsius. The Sun is about 4.6 billion years old.
        """,
        "llm_output": """
        The Sun is located at the center of our Solar System. It is made of hot plasma 
        and has a core temperature of about 15 million degrees Celsius. The Sun is 
        approximately 4.6 billion years old.
        """,
        "domain": "scientific",
        "expected_contradicted": 0
    }
]


def run_benchmark():
    """Run the benchmark suite"""
    print("=" * 70)
    print("🔍 Hallucination Hunter Benchmark Suite")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test cases: {len(BENCHMARK_CASES)}")
    print()
    
    results = []
    total_start = time.time()
    
    for i, case in enumerate(BENCHMARK_CASES, 1):
        print(f"Running test {i}/{len(BENCHMARK_CASES)}: {case['name']}")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            report = create_audit(
                sources=[{
                    "name": "source.txt",
                    "content": case["source"],
                    "type": "txt"
                }],
                llm_output=case["llm_output"],
                domain=case["domain"]
            )
            
            elapsed = time.time() - start_time
            stats = report.to_dict()["statistics"]
            
            accuracy = 1.0
            if case.get("expected_contradicted") is not None:
                if stats["contradicted"] == case["expected_contradicted"]:
                    accuracy = 1.0
                else:
                    accuracy = 1 - abs(stats["contradicted"] - case["expected_contradicted"]) / max(stats["total_claims"], 1)
            
            result = {
                "name": case["name"],
                "trust_score": report.trust_score.score,
                "total_claims": stats["total_claims"],
                "supported": stats["supported"],
                "contradicted": stats["contradicted"],
                "unverifiable": stats["unverifiable"],
                "processing_time": elapsed,
                "accuracy": accuracy,
                "status": "success"
            }
            
            print(f"  Trust Score: {report.trust_score.score:.1f}/100")
            print(f"  Claims: {stats['total_claims']} (S:{stats['supported']}, C:{stats['contradicted']}, U:{stats['unverifiable']})")
            print(f"  Time: {elapsed:.2f}s")
            print(f"  Accuracy: {accuracy:.1%}")
            
        except Exception as e:
            elapsed = time.time() - start_time
            result = {
                "name": case["name"],
                "status": "error",
                "error": str(e),
                "processing_time": elapsed
            }
            print(f"  ❌ Error: {e}")
        
        results.append(result)
        print()
    
    total_elapsed = time.time() - total_start
    
    # Summary
    print("=" * 70)
    print("📊 Benchmark Summary")
    print("=" * 70)
    
    successful = [r for r in results if r["status"] == "success"]
    
    if successful:
        avg_score = sum(r["trust_score"] for r in successful) / len(successful)
        avg_time = sum(r["processing_time"] for r in successful) / len(successful)
        avg_accuracy = sum(r.get("accuracy", 0) for r in successful) / len(successful)
        total_claims = sum(r["total_claims"] for r in successful)
        
        print(f"Successful tests: {len(successful)}/{len(results)}")
        print(f"Average trust score: {avg_score:.1f}/100")
        print(f"Average processing time: {avg_time:.2f}s")
        print(f"Average accuracy: {avg_accuracy:.1%}")
        print(f"Total claims analyzed: {total_claims}")
        print(f"Total time: {total_elapsed:.2f}s")
    
    # Save results
    output_path = Path(__file__).parent.parent / "data" / "benchmark_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_time": total_elapsed,
            "results": results
        }, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
