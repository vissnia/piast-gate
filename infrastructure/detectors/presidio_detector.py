import spacy
import logging
from typing import List, Optional, Dict
from presidio_analyzer import AnalyzerEngine, RecognizerResult
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.interfaces.pii_detector import PIIDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Singleton instances for expensive resources
_analyzer_engine: Optional[AnalyzerEngine] = None
_model_downloaded: bool = False

def download_model(model_name: str) -> None:
    """
    Downloads the spaCy model if it's not already installed.
    """
    global _model_downloaded
    if not _model_downloaded:
        if not spacy.util.is_package(model_name):
            logger.info(f"Downloading {model_name} model...")
            try:
                spacy.cli.download(model_name)
                logger.info(f"Successfully downloaded {model_name}.")
            except Exception as e:
                logger.error(f"Failed to download {model_name}: {e}")
                raise
        else:
            logger.debug(f"{model_name} model already downloaded.")
        _model_downloaded = True

def get_analyzer_engine(model_name: str = "en_core_web_lg") -> AnalyzerEngine:
    """Get or create singleton AnalyzerEngine instance."""
    global _analyzer_engine
    if _analyzer_engine is None:
        download_model(model_name)
        _analyzer_engine = AnalyzerEngine()
        # Pre-warm the analyzer to load all recognizers once during initialization
        logger.info("Warming up Presidio Analyzer...")
        _analyzer_engine.analyze(text="warm up", language="en")
    return _analyzer_engine

class PresidioPIIDetector(PIIDetector):
    """
    PII Detector implementation using Microsoft Presidio and spaCy.
    """
    
    # Mapping from Presidio/Spacy entity types to our PIIType enum
    ENTITY_MAPPING: Dict[str, PIIType] = {
        "PERSON": PIIType.PERSON,
        "EMAIL_ADDRESS": PIIType.EMAIL,
        "PHONE_NUMBER": PIIType.PHONE,
        "LOCATION": PIIType.LOCATION,
        "GPE": PIIType.LOCATION,
        "ORG": PIIType.ORGANIZATION,
        # Add more mappings as needed
    }

    def __init__(self, model_name: str = "en_core_web_lg"):
        self.analyzer = get_analyzer_engine(model_name)

    def detect(self, text: str) -> List[PIIToken]:
        """
        Detects PII in the given text using Presidio.
        """
        if not text:
            return []

        results: List[RecognizerResult] = self.analyzer.analyze(
            text=text,
            language="en"
        )

        tokens: List[PIIToken] = []
        for result in results:
            pii_type = self.ENTITY_MAPPING.get(result.entity_type)
            
            # Skip unsupported entity types
            if not pii_type:
                continue

            # Extract the actual text value
            original_value = text[result.start:result.end]

            tokens.append(PIIToken(
                type=pii_type,
                original_value=original_value,
                token_str="",  # Placeholder, usually set by Anonymizer
                start=result.start,
                end=result.end
            ))

        return tokens