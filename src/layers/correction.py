"""
Layer 7: Correction & Output Layer
Generates corrections, reports, and formatted outputs
"""

import json
from typing import Dict, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import io

from src.layers.verification import VerificationResult
from src.layers.scoring import TrustScore
from src.layers.claim_intelligence import Claim
from src.models.correction_model import CorrectionModel, CorrectionResult
from src.config.settings import get_settings
from src.config.constants import ClaimCategory, ExportFormat, Colors
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class AnnotatedClaim:
    """Claim with verification result and correction"""
    claim: Claim
    verification: VerificationResult
    correction: Optional[CorrectionResult]
    color: str
    
    def to_dict(self) -> Dict:
        return {
            "claim_id": self.claim.claim_id,
            "text": self.claim.text,
            "category": self.verification.category.value,
            "confidence": self.verification.confidence,
            "color": self.color,
            "citation": self.verification.citation,
            "explanation": self.verification.explanation,
            "correction": self.correction.to_dict() if self.correction else None
        }


@dataclass
class AuditReport:
    """Complete audit report for an LLM output"""
    report_id: str
    timestamp: datetime
    llm_output: str
    trust_score: TrustScore
    annotated_claims: List[AnnotatedClaim]
    summary: str
    document_sources: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "report_id": self.report_id,
            "timestamp": self.timestamp.isoformat(),
            "trust_score": self.trust_score.to_dict(),
            "summary": self.summary,
            "document_sources": self.document_sources,
            "claims": [c.to_dict() for c in self.annotated_claims],
            "statistics": {
                "total_claims": len(self.annotated_claims),
                "supported": sum(1 for c in self.annotated_claims if c.verification.category == ClaimCategory.SUPPORTED),
                "contradicted": sum(1 for c in self.annotated_claims if c.verification.category == ClaimCategory.CONTRADICTED),
                "unverifiable": sum(1 for c in self.annotated_claims if c.verification.category == ClaimCategory.UNVERIFIABLE)
            }
        }


class CorrectionLayer:
    """
    Layer 7: Correction & Output
    
    Responsibilities:
    - Generate corrections for contradicted claims
    - Create annotated text with color coding
    - Generate reports in multiple formats (PDF, HTML, JSON)
    - Format API responses
    """
    
    def __init__(
        self,
        correction_model: Optional[CorrectionModel] = None
    ):
        """
        Initialize correction layer
        
        Args:
            correction_model: Model for generating corrections
        """
        self.correction_model = correction_model or CorrectionModel()
        
        logger.info("Correction Layer initialized")
    
    def generate_corrections(
        self,
        verification_results: List[VerificationResult],
        generate_for_all: bool = False
    ) -> Dict[str, CorrectionResult]:
        """
        Generate corrections for claims
        
        Args:
            verification_results: Verification results
            generate_for_all: Generate for all claims (not just contradicted)
        
        Returns:
            Dict mapping claim_id to CorrectionResult
        """
        corrections = {}
        
        for result in verification_results:
            # Only generate corrections for contradicted claims (unless generate_for_all)
            if result.category == ClaimCategory.CONTRADICTED or generate_for_all:
                try:
                    correction = self.correction_model.generate_correction_with_explanation(
                        claim=result.claim_text,
                        evidence=result.evidence_used,
                        category=result.category.value,
                        confidence=result.confidence
                    )
                    corrections[result.claim_id] = correction
                except Exception as e:
                    logger.warning(f"Failed to generate correction for claim {result.claim_id}: {e}")
        
        logger.info(f"Generated {len(corrections)} corrections")
        return corrections
    
    def create_annotated_claims(
        self,
        claims: List[Claim],
        verification_results: List[VerificationResult],
        corrections: Optional[Dict[str, CorrectionResult]] = None
    ) -> List[AnnotatedClaim]:
        """
        Create annotated claims combining all information
        
        Args:
            claims: Original claims
            verification_results: Verification results
            corrections: Optional corrections dictionary
        
        Returns:
            List of AnnotatedClaim objects
        """
        result_map = {r.claim_id: r for r in verification_results}
        corrections = corrections or {}
        
        annotated = []
        for claim in claims:
            verification = result_map.get(claim.claim_id)
            if not verification:
                continue
            
            color = Colors.get_claim_color(verification.category)
            correction = corrections.get(claim.claim_id)
            
            annotated.append(AnnotatedClaim(
                claim=claim,
                verification=verification,
                correction=correction,
                color=color
            ))
        
        return annotated
    
    def create_audit_report(
        self,
        llm_output: str,
        trust_score: TrustScore,
        annotated_claims: List[AnnotatedClaim],
        document_sources: List[str]
    ) -> AuditReport:
        """
        Create complete audit report
        
        Args:
            llm_output: Original LLM output
            trust_score: Calculated trust score
            annotated_claims: Annotated claims
            document_sources: List of source document names
        
        Returns:
            AuditReport object
        """
        import uuid
        
        summary = self._generate_summary(trust_score, annotated_claims)
        
        return AuditReport(
            report_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            llm_output=llm_output,
            trust_score=trust_score,
            annotated_claims=annotated_claims,
            summary=summary,
            document_sources=document_sources
        )
    
    def _generate_summary(
        self,
        trust_score: TrustScore,
        annotated_claims: List[AnnotatedClaim]
    ) -> str:
        """Generate executive summary"""
        total = len(annotated_claims)
        supported = sum(1 for c in annotated_claims if c.verification.category == ClaimCategory.SUPPORTED)
        contradicted = sum(1 for c in annotated_claims if c.verification.category == ClaimCategory.CONTRADICTED)
        unverifiable = total - supported - contradicted
        
        summary_parts = [
            f"Trust Score: {trust_score.score:.1f}/100 ({trust_score.level.value})",
            f"Claims Analyzed: {total}",
            f"Supported: {supported} ({supported/total*100:.1f}%)" if total > 0 else "Supported: 0",
            f"Contradicted: {contradicted} ({contradicted/total*100:.1f}%)" if total > 0 else "Contradicted: 0",
            f"Unverifiable: {unverifiable} ({unverifiable/total*100:.1f}%)" if total > 0 else "Unverifiable: 0",
        ]
        
        if trust_score.recommendations:
            summary_parts.append(f"\nRecommendations: {'; '.join(trust_score.recommendations)}")
        
        return "\n".join(summary_parts)
    
    def export_json(self, report: AuditReport) -> str:
        """Export report as JSON string"""
        return json.dumps(report.to_dict(), indent=2, default=str)
    
    def export_html(self, report: AuditReport) -> str:
        """Export report as interactive HTML"""
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hallucination Hunter Audit Report</title>
    <style>
        body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0 0 10px 0; }}
        .score-badge {{ font-size: 48px; font-weight: bold; }}
        .score-level {{ font-size: 18px; opacity: 0.9; }}
        .section {{ background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .section h2 {{ margin-top: 0; color: #1f2937; }}
        .claim {{ padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid; }}
        .claim.supported {{ background: rgba(16, 185, 129, 0.1); border-color: #10b981; }}
        .claim.contradicted {{ background: rgba(239, 68, 68, 0.1); border-color: #ef4444; }}
        .claim.unverifiable {{ background: rgba(245, 158, 11, 0.1); border-color: #f59e0b; }}
        .claim-text {{ font-weight: 500; margin-bottom: 8px; }}
        .claim-meta {{ font-size: 14px; color: #6b7280; }}
        .correction {{ background: #f0fdf4; padding: 10px; border-radius: 6px; margin-top: 10px; }}
        .correction-label {{ font-weight: 600; color: #059669; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }}
        .stat-card {{ background: #f9fafb; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #1f2937; }}
        .stat-label {{ font-size: 14px; color: #6b7280; }}
        .summary {{ white-space: pre-line; line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Hallucination Hunter Audit Report</h1>
            <div class="score-badge">{score}/100</div>
            <div class="score-level">{level}</div>
            <div style="margin-top: 10px; font-size: 14px;">Generated: {timestamp}</div>
        </div>
        
        <div class="section">
            <h2>📊 Summary</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{total_claims}</div>
                    <div class="stat-label">Total Claims</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color: #10b981;">{supported}</div>
                    <div class="stat-label">Supported</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color: #ef4444;">{contradicted}</div>
                    <div class="stat-label">Contradicted</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color: #f59e0b;">{unverifiable}</div>
                    <div class="stat-label">Unverifiable</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>📝 Claims Analysis</h2>
            {claims_html}
        </div>
        
        <div class="section">
            <h2>📚 Source Documents</h2>
            <ul>
                {sources_html}
            </ul>
        </div>
    </div>
</body>
</html>
"""
        
        # Generate claims HTML
        claims_html_parts = []
        for ac in report.annotated_claims:
            category = ac.verification.category.value
            correction_html = ""
            if ac.correction:
                correction_html = f"""
                <div class="correction">
                    <span class="correction-label">Suggested Correction:</span> {ac.correction.corrected_claim}
                </div>
                """
            
            claims_html_parts.append(f"""
            <div class="claim {category}">
                <div class="claim-text">{ac.claim.text}</div>
                <div class="claim-meta">
                    <strong>Status:</strong> {category.title()} | 
                    <strong>Confidence:</strong> {ac.verification.confidence:.0%} | 
                    <strong>Citation:</strong> {ac.verification.citation}
                </div>
                <div class="claim-meta"><strong>Explanation:</strong> {ac.verification.explanation}</div>
                {correction_html}
            </div>
            """)
        
        # Generate sources HTML
        sources_html = "\n".join(f"<li>{source}</li>" for source in report.document_sources)
        
        stats = report.to_dict()["statistics"]
        
        return html_template.format(
            score=report.trust_score.score,
            level=report.trust_score.level.value.title(),
            timestamp=report.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            total_claims=stats["total_claims"],
            supported=stats["supported"],
            contradicted=stats["contradicted"],
            unverifiable=stats["unverifiable"],
            claims_html="\n".join(claims_html_parts),
            sources_html=sources_html
        )
    
    def export_csv(self, report: AuditReport) -> str:
        """Export claims as CSV"""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            "Claim ID", "Claim Text", "Category", "Confidence",
            "Citation", "Explanation", "Correction"
        ])
        
        # Data rows
        for ac in report.annotated_claims:
            writer.writerow([
                ac.claim.claim_id,
                ac.claim.text,
                ac.verification.category.value,
                f"{ac.verification.confidence:.2f}",
                ac.verification.citation,
                ac.verification.explanation,
                ac.correction.corrected_claim if ac.correction else ""
            ])
        
        return output.getvalue()
    
    def export_pdf(self, report: AuditReport) -> bytes:
        """Export report as PDF"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30
            )
            story.append(Paragraph("🔍 Hallucination Hunter Audit Report", title_style))
            story.append(Spacer(1, 12))
            
            # Trust Score
            story.append(Paragraph(f"<b>Trust Score:</b> {report.trust_score.score}/100 ({report.trust_score.level.value})", styles['Normal']))
            story.append(Paragraph(f"<b>Generated:</b> {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Summary table
            stats = report.to_dict()["statistics"]
            summary_data = [
                ["Total Claims", "Supported", "Contradicted", "Unverifiable"],
                [stats["total_claims"], stats["supported"], stats["contradicted"], stats["unverifiable"]]
            ]
            
            table = Table(summary_data, colWidths=[1.5*inch]*4)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f3f4f6')),
                ('GRID', (0, 0), (-1, -1), 1, colors.white)
            ]))
            story.append(table)
            story.append(Spacer(1, 20))
            
            # Claims
            story.append(Paragraph("<b>Claims Analysis</b>", styles['Heading2']))
            story.append(Spacer(1, 10))
            
            for ac in report.annotated_claims[:20]:  # Limit for PDF
                category = ac.verification.category.value
                color_map = {
                    "supported": "#10b981",
                    "contradicted": "#ef4444",
                    "unverifiable": "#f59e0b"
                }
                color = color_map.get(category, "#6b7280")
                
                claim_text = f"""
                <font color="{color}"><b>[{category.upper()}]</b></font> {ac.claim.text[:200]}{'...' if len(ac.claim.text) > 200 else ''}
                <br/><i>Confidence: {ac.verification.confidence:.0%} | {ac.verification.citation}</i>
                """
                story.append(Paragraph(claim_text, styles['Normal']))
                story.append(Spacer(1, 8))
            
            doc.build(story)
            return buffer.getvalue()
            
        except ImportError:
            logger.warning("reportlab not installed. PDF export unavailable.")
            return b""
    
    def export(
        self,
        report: AuditReport,
        format: ExportFormat,
        file_path: Optional[Union[str, Path]] = None
    ) -> Union[str, bytes]:
        """
        Export report in specified format
        
        Args:
            report: Audit report
            format: Export format
            file_path: Optional path to save file
        
        Returns:
            Exported content
        """
        exporters = {
            ExportFormat.JSON: self.export_json,
            ExportFormat.HTML: self.export_html,
            ExportFormat.CSV: self.export_csv,
            ExportFormat.PDF: self.export_pdf
        }
        
        exporter = exporters.get(format)
        if not exporter:
            raise ValueError(f"Unsupported format: {format}")
        
        content = exporter(report)
        
        if file_path:
            path = Path(file_path)
            mode = "wb" if isinstance(content, bytes) else "w"
            with open(path, mode) as f:
                f.write(content)
            logger.info(f"Exported report to {file_path}")
        
        return content
    
    def format_api_response(
        self,
        report: AuditReport,
        include_details: bool = True
    ) -> Dict:
        """
        Format report for API response
        
        Args:
            report: Audit report
            include_details: Whether to include detailed claim info
        
        Returns:
            API-friendly dict
        """
        response = {
            "report_id": report.report_id,
            "timestamp": report.timestamp.isoformat(),
            "trust_score": report.trust_score.score,
            "trust_level": report.trust_score.level.value,
            "summary": report.summary,
            "statistics": report.to_dict()["statistics"]
        }
        
        if include_details:
            response["claims"] = [c.to_dict() for c in report.annotated_claims]
            response["recommendations"] = report.trust_score.recommendations
        
        return response
