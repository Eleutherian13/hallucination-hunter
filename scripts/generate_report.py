#!/usr/bin/env python
"""
Generate audit report from command line
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src import create_audit
from src.config.constants import Domain, ExportFormat
from src.layers.ui_integration import get_integration_layer


def main():
    parser = argparse.ArgumentParser(
        description="Generate audit report for LLM output"
    )
    
    parser.add_argument(
        "--sources",
        "-s",
        nargs="+",
        required=True,
        help="Source document files"
    )
    
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="LLM output file or text"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path"
    )
    
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "html", "csv", "pdf"],
        default="json",
        help="Output format"
    )
    
    parser.add_argument(
        "--domain",
        "-d",
        choices=[d.value for d in Domain],
        default="general",
        help="Domain for verification"
    )
    
    args = parser.parse_args()
    
    # Load sources
    sources = []
    for source_path in args.sources:
        path = Path(source_path)
        if path.exists():
            with open(path, "rb") as f:
                content = f.read()
            sources.append({
                "name": path.name,
                "content": content,
                "type": path.suffix.lstrip(".")
            })
        else:
            print(f"Warning: Source file not found: {source_path}")
    
    if not sources:
        print("Error: No valid source files provided")
        sys.exit(1)
    
    # Load LLM output
    input_path = Path(args.input)
    if input_path.exists():
        with open(input_path, "r", encoding="utf-8") as f:
            llm_output = f.read()
    else:
        llm_output = args.input
    
    # Run audit
    print(f"Running audit with {len(sources)} source(s)...")
    
    try:
        report = create_audit(
            sources=sources,
            llm_output=llm_output,
            domain=args.domain
        )
        
        print(f"Trust Score: {report.trust_score.score:.1f}/100")
        
        # Export
        integration = get_integration_layer()
        export_format = ExportFormat(args.format)
        
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = Path(f"audit_report.{args.format}")
        
        content = integration.export_report(report, export_format, output_path)
        
        print(f"Report saved to: {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
