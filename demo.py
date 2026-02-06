#!/usr/bin/env python3
"""Quick demo script for Hallucination Hunter v2.0."""

import sys
sys.path.insert(0, 'src')

def main():
    print('=' * 60)
    print('HALLUCINATION HUNTER v2.0 - Quick Demo')
    print('=' * 60)

    # Test claim extraction
    print('\n1. Testing Claim Extraction...')
    from layers.claim_intelligence import ClaimIntelligenceLayer
    claim_layer = ClaimIntelligenceLayer()

    test_text = '''
    The Eiffel Tower was built in 1889 and is located in Paris, France.
    It stands at 330 meters tall, making it the tallest structure in Paris.
    The tower was designed by Gustave Eiffel.
    '''

    claims = claim_layer.extract_claims(test_text)
    print(f'   Extracted {len(claims)} claims from text')
    for i, claim in enumerate(claims[:3], 1):
        text_preview = claim.text[:50] + '...' if len(claim.text) > 50 else claim.text
        print(f'   - Claim {i}: "{text_preview}"')

    # Test text processing
    print('\n2. Testing Text Processing...')
    from utils.text_processing import TextProcessor
    processed = TextProcessor.clean_text('  Hello,   World!  ')
    print(f'   Cleaned: "{processed}"')

    # Test settings
    print('\n3. Testing Configuration...')
    from config.settings import Settings
    settings = Settings()
    print(f'   NLI Model: {settings.nli_model_name}')
    print(f'   Embedding Model: {settings.embedding_model_name}')
    print(f'   Entailment Threshold: {settings.entailment_threshold}')

    # Test validation
    print('\n4. Testing Input Validation...')
    from utils.validation import InputValidator
    validator = InputValidator()
    result = validator.validate_text_input('Test input text')
    print(f'   Validation: {"PASS" if result.is_valid else "FAIL"}')

    # Test UI integration layer
    print('\n5. Testing UI Integration Layer...')
    from layers.ui_integration import UIIntegrationLayer
    ui_layer = UIIntegrationLayer()
    print(f'   UI Layer initialized successfully')

    print('\n' + '=' * 60)
    print('DEMO COMPLETE - All core systems operational!')
    print('=' * 60)

if __name__ == '__main__':
    main()
