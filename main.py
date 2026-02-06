#!/usr/bin/env python
"""
Main entry point for Hallucination Hunter
Run: python main.py [command]

Commands:
    ui      - Start Streamlit UI
    api     - Start FastAPI server
    demo    - Run a quick demo
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def start_ui():
    """Start the Streamlit UI"""
    import subprocess
    app_path = Path(__file__).parent / "src" / "ui" / "app.py"
    subprocess.run(["streamlit", "run", str(app_path)])


def start_api(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Start the FastAPI server"""
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload
    )


def run_demo():
    """Run a quick demo of the system"""
    print("=" * 60)
    print("🔍 Hallucination Hunter Demo")
    print("=" * 60)
    
    from src import create_audit
    
    # Sample source document
    source_text = """
    The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris, 
    France. It is named after the engineer Gustave Eiffel, whose company designed and 
    built the tower. Constructed from 1887 to 1889 as the centerpiece of the 1889 
    World's Fair. The tower is 330 metres tall. The Eiffel Tower is the most-visited 
    paid monument in the world; 6.91 million people ascended it in 2015.
    """
    
    # Sample LLM output with some errors
    llm_output = """
    The Eiffel Tower is located in Paris, France. It was built in 1889 and stands 
    at 324 meters tall. The tower was designed by Gustave Eiffel for the World's Fair.
    It receives approximately 7 million visitors each year.
    """
    
    print("\n📄 Source Document:")
    print("-" * 40)
    print(source_text.strip())
    
    print("\n🤖 LLM Output to Verify:")
    print("-" * 40)
    print(llm_output.strip())
    
    print("\n⏳ Running audit...")
    print("-" * 40)
    
    try:
        report = create_audit(
            sources=[{"name": "source.txt", "content": source_text, "type": "txt"}],
            llm_output=llm_output,
            domain="general"
        )
        
        print(f"\n📊 Results:")
        print("-" * 40)
        print(f"Trust Score: {report.trust_score.score:.1f}/100 ({report.trust_score.level.value})")
        
        stats = report.to_dict()["statistics"]
        print(f"Total Claims: {stats['total_claims']}")
        print(f"  ✅ Supported: {stats['supported']}")
        print(f"  ❌ Contradicted: {stats['contradicted']}")
        print(f"  ❓ Unverifiable: {stats['unverifiable']}")
        
        print("\n📝 Claim Details:")
        print("-" * 40)
        for ac in report.annotated_claims:
            status = "✅" if ac.verification.category.value == "supported" else "❌" if ac.verification.category.value == "contradicted" else "❓"
            print(f"\n{status} {ac.claim.text}")
            print(f"   Category: {ac.verification.category.value}")
            print(f"   Confidence: {ac.verification.confidence:.0%}")
            print(f"   Citation: {ac.verification.citation}")
            if ac.correction:
                print(f"   Correction: {ac.correction.corrected_claim}")
        
        print("\n💡 Recommendations:")
        print("-" * 40)
        for rec in report.trust_score.recommendations:
            print(f"  • {rec}")
        
        print("\n" + "=" * 60)
        print("Demo complete!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Hallucination Hunter - AI-assisted fact-checking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py ui              # Start Streamlit UI
    python main.py api             # Start FastAPI server
    python main.py api --port 8080 # Start API on custom port
    python main.py demo            # Run quick demo
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # UI command
    ui_parser = subparsers.add_parser("ui", help="Start Streamlit UI")
    
    # API command
    api_parser = subparsers.add_parser("api", help="Start FastAPI server")
    api_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    api_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    api_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run quick demo")
    
    args = parser.parse_args()
    
    if args.command == "ui":
        start_ui()
    elif args.command == "api":
        start_api(args.host, args.port, args.reload)
    elif args.command == "demo":
        run_demo()
    else:
        parser.print_help()
        print("\nRun with 'ui', 'api', or 'demo' command.")


if __name__ == "__main__":
    main()
