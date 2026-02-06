"""
Hallucination Hunter - AI-assisted fact-checking and attribution system
"""

__version__ = "2.0.0"
__author__ = "DataForge Team"

from src.layers.ui_integration import UIIntegrationLayer, AuditRequest, get_integration_layer
from src.layers.scoring import TrustScore
from src.layers.correction import AuditReport
from src.config.constants import Domain, ClaimCategory

__all__ = [
    "UIIntegrationLayer",
    "AuditRequest",
    "get_integration_layer",
    "TrustScore",
    "AuditReport",
    "Domain",
    "ClaimCategory",
    "__version__"
]


def create_audit(
    sources: list,
    llm_output: str,
    domain: str = "general"
) -> AuditReport:
    """
    Quick function to run an audit
    
    Args:
        sources: List of source documents (dicts with name, content, type)
        llm_output: LLM output to verify
        domain: Domain for verification
    
    Returns:
        AuditReport with results
    
    Example:
        >>> from src import create_audit
        >>> report = create_audit(
        ...     sources=[{"name": "doc.txt", "content": "Paris is in France.", "type": "txt"}],
        ...     llm_output="Paris is the capital of France."
        ... )
        >>> print(f"Trust Score: {report.trust_score.score}")
    """
    try:
        domain_enum = Domain(domain.lower())
    except ValueError:
        domain_enum = Domain.GENERAL
    
    request = AuditRequest(
        sources=sources,
        llm_output=llm_output,
        domain=domain_enum
    )
    
    integration = get_integration_layer()
    return integration.run_audit(request)
