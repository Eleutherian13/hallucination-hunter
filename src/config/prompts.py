"""
Prompt templates for LLM interactions in Hallucination Hunter
"""

from typing import Dict, List, Optional


class PromptTemplates:
    """Collection of prompt templates for various system components"""
    
    # ==========================================================================
    # Claim Extraction Prompts
    # ==========================================================================
    
    CLAIM_EXTRACTION = """Extract all atomic factual claims from the following text. 
Each claim should be:
1. A single, verifiable statement
2. Self-contained (understandable without context)
3. Specific (contains concrete facts, numbers, or entities)

Text: {text}

Return the claims as a JSON array of strings. Example:
["Claim 1", "Claim 2", "Claim 3"]

Claims:"""

    CLAIM_DECOMPOSITION = """Break down the following complex claim into atomic sub-claims.
Each sub-claim should express exactly one fact.

Complex claim: {claim}

Example:
Input: "John, a 45-year-old diabetic patient, was prescribed 500mg of Metformin twice daily"
Output: 
- "John is a patient"
- "John is 45 years old"  
- "John has diabetes"
- "John was prescribed Metformin"
- "The Metformin dosage is 500mg"
- "Metformin is to be taken twice daily"

Atomic claims:"""

    # ==========================================================================
    # Entity Extraction Prompts
    # ==========================================================================
    
    ENTITY_EXTRACTION_HEALTHCARE = """Extract all medical entities from the following text.
Categories: MEDICATION, DISEASE, SYMPTOM, DOSAGE, LAB_VALUE, PROCEDURE, ANATOMY

Text: {text}

Return as JSON with entity type and value. Example:
{{"entities": [{{"type": "MEDICATION", "value": "Metformin"}}, {{"type": "DOSAGE", "value": "500mg"}}]}}

Entities:"""

    ENTITY_EXTRACTION_LAW = """Extract all legal entities from the following text.
Categories: CASE_CITATION, STATUTE, COURT, JUDGE, PARTY, DATE, LEGAL_TERM

Text: {text}

Return as JSON with entity type and value.

Entities:"""

    ENTITY_EXTRACTION_FINANCE = """Extract all financial entities from the following text.
Categories: MONEY, PERCENT, COMPANY, METRIC, DATE, STOCK_SYMBOL, FINANCIAL_TERM

Text: {text}

Return as JSON with entity type and value.

Entities:"""

    # ==========================================================================
    # Correction Generation Prompts
    # ==========================================================================
    
    CORRECTION_GENERATION = """Rewrite the following claim to be factually accurate based on the provided evidence.

Original claim: {claim}

Evidence from source: {evidence}

Corrected claim (keep the same style and format, only fix factual errors):"""

    CORRECTION_WITH_EXPLANATION = """The following claim has been identified as contradicting the source document.

Claim: {claim}
Category: {category}
Confidence: {confidence}

Evidence from source:
{evidence}

Please provide:
1. A corrected version of the claim
2. A brief explanation of what was wrong

Response format:
Corrected: [corrected claim]
Explanation: [what was changed and why]

Response:"""

    # ==========================================================================
    # Explanation Generation Prompts
    # ==========================================================================
    
    EXPLANATION_SUPPORTED = """Generate a concise explanation for why this claim is supported by the evidence.

Claim: {claim}
Evidence: {evidence}
Confidence: {confidence}

Explanation (be specific and reference the evidence):"""

    EXPLANATION_CONTRADICTED = """Generate a concise explanation for why this claim contradicts the evidence.

Claim: {claim}
Evidence: {evidence}
Specific contradiction: {contradiction_detail}

Explanation (clearly state what the claim says vs what the evidence says):"""

    EXPLANATION_UNVERIFIABLE = """Generate a concise explanation for why this claim cannot be verified.

Claim: {claim}
Available evidence: {evidence}
Search results: Found {num_results} potentially relevant passages

Explanation (explain what information is missing or insufficient):"""

    # ==========================================================================
    # Summary Generation Prompts
    # ==========================================================================
    
    AUDIT_SUMMARY = """Generate a concise executive summary of the verification audit results.

Document: {document_title}
Total claims: {total_claims}
Supported: {supported_count} ({supported_percent}%)
Contradicted: {contradicted_count} ({contradicted_percent}%)
Unverifiable: {unverifiable_count} ({unverifiable_percent}%)
Trust Score: {trust_score}/100

Key issues found:
{key_issues}

Summary (2-3 sentences highlighting main findings and recommendations):"""

    # ==========================================================================
    # Domain-Specific Prompts
    # ==========================================================================
    
    DOMAIN_PROMPTS: Dict[str, str] = {
        "healthcare": """You are analyzing a medical document. Pay special attention to:
- Medication names, dosages, and frequencies
- Lab values and their normal ranges
- Disease names and stages
- Patient demographics and history
Be extremely precise with numerical values.""",

        "law": """You are analyzing a legal document. Pay special attention to:
- Case citations (format: Reporter Volume Page)
- Statute references
- Dates and deadlines
- Party names and roles
Exact citation accuracy is critical.""",

        "finance": """You are analyzing a financial document. Pay special attention to:
- Monetary values and currencies
- Percentages and growth rates
- Company names and stock symbols
- Dates and reporting periods
Numerical precision is essential.""",

        "general": """You are analyzing a general document. Pay attention to:
- Names of people, places, and organizations
- Dates and numerical facts
- Quoted statements
- Causal relationships"""
    }

    # ==========================================================================
    # Utility Methods
    # ==========================================================================
    
    @classmethod
    def get_claim_extraction_prompt(cls, text: str) -> str:
        """Get formatted claim extraction prompt"""
        return cls.CLAIM_EXTRACTION.format(text=text)
    
    @classmethod
    def get_correction_prompt(
        cls, 
        claim: str, 
        evidence: str,
        category: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> str:
        """Get formatted correction prompt"""
        if category and confidence:
            return cls.CORRECTION_WITH_EXPLANATION.format(
                claim=claim,
                evidence=evidence,
                category=category,
                confidence=f"{confidence:.2%}"
            )
        return cls.CORRECTION_GENERATION.format(claim=claim, evidence=evidence)
    
    @classmethod
    def get_explanation_prompt(
        cls,
        claim: str,
        category: str,
        evidence: str,
        confidence: float,
        **kwargs
    ) -> str:
        """Get appropriate explanation prompt based on category"""
        if category == "supported":
            return cls.EXPLANATION_SUPPORTED.format(
                claim=claim,
                evidence=evidence,
                confidence=f"{confidence:.2%}"
            )
        elif category == "contradicted":
            return cls.EXPLANATION_CONTRADICTED.format(
                claim=claim,
                evidence=evidence,
                contradiction_detail=kwargs.get("contradiction_detail", "See evidence")
            )
        else:
            return cls.EXPLANATION_UNVERIFIABLE.format(
                claim=claim,
                evidence=evidence,
                num_results=kwargs.get("num_results", 0)
            )
    
    @classmethod
    def get_domain_context(cls, domain: str) -> str:
        """Get domain-specific context prompt"""
        return cls.DOMAIN_PROMPTS.get(domain, cls.DOMAIN_PROMPTS["general"])
    
    @classmethod
    def get_entity_extraction_prompt(cls, text: str, domain: str) -> str:
        """Get domain-specific entity extraction prompt"""
        prompts = {
            "healthcare": cls.ENTITY_EXTRACTION_HEALTHCARE,
            "law": cls.ENTITY_EXTRACTION_LAW,
            "finance": cls.ENTITY_EXTRACTION_FINANCE,
        }
        template = prompts.get(domain, cls.ENTITY_EXTRACTION_HEALTHCARE)
        return template.format(text=text)
