"""
Pytest configuration
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests"""
    # Clear settings cache
    from src.config.settings import get_settings
    get_settings.cache_clear()
    
    # Reset global cache
    from src.utils import caching
    caching._global_cache = None
    
    yield


@pytest.fixture
def sample_llm_output():
    """Sample LLM output for testing"""
    return """
    The Eiffel Tower is located in Paris, France. It was built in 1889 and stands 
    at 324 meters tall. The tower was designed by Gustave Eiffel for the World's Fair.
    It receives approximately 7 million visitors each year.
    """


@pytest.fixture
def sample_source_text():
    """Sample source document for testing"""
    return """
    The Eiffel Tower is a wrought-iron lattice tower on the Champ de Mars in Paris, 
    France. It is named after the engineer Gustave Eiffel, whose company designed and 
    built the tower. Constructed from 1887 to 1889 as the centerpiece of the 1889 
    World's Fair, it was initially criticized by some of France's leading artists and 
    intellectuals for its design. The tower is 330 metres tall, about the same height 
    as an 81-storey building. The Eiffel Tower is the most-visited paid monument in 
    the world; 6.91 million people ascended it in 2015.
    """


@pytest.fixture
def mock_claims():
    """Mock claims for testing"""
    from dataclasses import dataclass
    from typing import List, Tuple
    
    @dataclass
    class MockClaim:
        claim_id: str
        text: str
        entities: List[Tuple[str, str]]
        numerical_values: List[float]
        source_start: int = 0
        source_end: int = 0
    
    return [
        MockClaim(
            claim_id="claim_1",
            text="The Eiffel Tower is located in Paris, France.",
            entities=[("Eiffel Tower", "FAC"), ("Paris", "GPE"), ("France", "GPE")],
            numerical_values=[]
        ),
        MockClaim(
            claim_id="claim_2",
            text="It was built in 1889.",
            entities=[],
            numerical_values=[1889]
        ),
        MockClaim(
            claim_id="claim_3",
            text="The tower stands at 324 meters tall.",
            entities=[],
            numerical_values=[324]
        ),
        MockClaim(
            claim_id="claim_4",
            text="It receives approximately 7 million visitors each year.",
            entities=[],
            numerical_values=[7000000]
        )
    ]


@pytest.fixture
def mock_verification_results():
    """Mock verification results for testing"""
    from unittest.mock import Mock
    from src.config.constants import ClaimCategory
    
    return [
        Mock(
            claim_id="claim_1",
            claim_text="The Eiffel Tower is located in Paris, France.",
            category=ClaimCategory.SUPPORTED,
            confidence=0.95,
            evidence_used="The Eiffel Tower is on the Champ de Mars in Paris, France.",
            citation="Source Document, Paragraph 1",
            explanation="The claim is directly supported by the source."
        ),
        Mock(
            claim_id="claim_2",
            claim_text="It was built in 1889.",
            category=ClaimCategory.SUPPORTED,
            confidence=0.92,
            evidence_used="Constructed from 1887 to 1889",
            citation="Source Document, Paragraph 1",
            explanation="The claim aligns with the construction completion date."
        ),
        Mock(
            claim_id="claim_3",
            claim_text="The tower stands at 324 meters tall.",
            category=ClaimCategory.CONTRADICTED,
            confidence=0.85,
            evidence_used="The tower is 330 metres tall",
            citation="Source Document, Paragraph 1",
            explanation="The source states 330 meters, not 324 meters."
        ),
        Mock(
            claim_id="claim_4",
            claim_text="It receives approximately 7 million visitors each year.",
            category=ClaimCategory.SUPPORTED,
            confidence=0.78,
            evidence_used="6.91 million people ascended it in 2015",
            citation="Source Document, Paragraph 1",
            explanation="The claim is approximately consistent with reported figures."
        )
    ]
