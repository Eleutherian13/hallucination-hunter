#!/usr/bin/env python
"""
Download and cache required ML models
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import get_settings
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def download_models():
    """Download all required models"""
    settings = get_settings()
    
    print("=" * 60)
    print("🔍 Hallucination Hunter - Model Downloader")
    print("=" * 60)
    
    # Download NLI model
    print(f"\n📥 Downloading NLI model: {settings.nli_model_name}")
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(settings.nli_model_name)
        model = AutoModelForSequenceClassification.from_pretrained(settings.nli_model_name)
        print("   ✅ NLI model downloaded successfully")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Download embedding model
    print(f"\n📥 Downloading embedding model: {settings.embedding_model_name}")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(settings.embedding_model_name)
        print("   ✅ Embedding model downloaded successfully")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Download correction model
    print(f"\n📥 Downloading correction model: {settings.correction_model_name}")
    try:
        from transformers import T5ForConditionalGeneration, T5Tokenizer
        tokenizer = T5Tokenizer.from_pretrained(settings.correction_model_name)
        model = T5ForConditionalGeneration.from_pretrained(settings.correction_model_name)
        print("   ✅ Correction model downloaded successfully")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    # Download spaCy model
    spacy_model = "en_core_web_sm"
    print(f"\n📥 Downloading spaCy model: {spacy_model}")
    try:
        import spacy
        try:
            nlp = spacy.load(spacy_model)
        except OSError:
            import subprocess
            subprocess.run([sys.executable, "-m", "spacy", "download", spacy_model])
            nlp = spacy.load(spacy_model)
        print("   ✅ spaCy model downloaded successfully")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
    
    print("\n" + "=" * 60)
    print("Download complete!")
    print("=" * 60)


if __name__ == "__main__":
    download_models()
