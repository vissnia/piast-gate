import spacy
import logging
import os
import json
from typing import List, Optional, Dict
from presidio_analyzer import AnalyzerEngine, RecognizerResult
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.interfaces.pii_detector import PIIDetector
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer import RecognizerRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_analyzer_engine: Optional[AnalyzerEngine] = None

def download_model(model_name: str) -> None:
    """
    Downloads the spaCy model if it's not already installed.
    """

    if not spacy.util.is_package(model_name):
        logger.info(f"Downloading {model_name} model...")
        try:
            spacy.cli.download(model_name)
            logger.info(f"Successfully downloaded {model_name}.")
        except Exception as e:
            logger.error(f"Failed to download {model_name}: {e}")
            raise
    else:
        logger.info(f"{model_name} model already downloaded.")

def get_analyzer_engine() -> AnalyzerEngine:
    """Get or create singleton AnalyzerEngine instance."""
    global _analyzer_engine
    if _analyzer_engine is None:
        current_dir = os.path.dirname(__file__)
        config_path = os.path.abspath(os.path.join(current_dir, "..", "..", "presidio_config.json"))
        
        with open(config_path, "r", encoding="utf-8") as f:
            configuration = json.load(f)
        
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()
        
        supported_languages = list(nlp_engine.get_supported_languages())
        registry = RecognizerRegistry(supported_languages=["pl"])
        registry.load_predefined_recognizers(languages=["pl"])
        
        _analyzer_engine = AnalyzerEngine(
            registry=registry, 
            supported_languages=supported_languages, 
            nlp_engine=nlp_engine
        )

    return _analyzer_engine

class PresidioPIIDetector(PIIDetector):
    """
    PII Detector implementation using Microsoft Presidio and spaCy.
    """
    
    ENTITY_MAPPING: Dict[str, PIIType] = {
        "PERSON": PIIType.PERSON,
        "EMAIL_ADDRESS": PIIType.EMAIL,
        "PHONE_NUMBER": PIIType.PHONE,
        "LOCATION": PIIType.LOCATION,
        "GPE": PIIType.LOCATION,
        "ORG": PIIType.ORGANIZATION,
    }

    def __init__(self):
        self.analyzer = get_analyzer_engine()

    def detect(self, text: str) -> List[PIIToken]:
        """
        Detects PII in the given text using Presidio.
        """
        if not text:
            return []

        results: List[RecognizerResult] = self.analyzer.analyze(
            text=text,
            language="pl"
        )

        tokens: List[PIIToken] = []
        for result in results:
            pii_type = self.ENTITY_MAPPING.get(result.entity_type)
            
            if not pii_type:
                continue

            original_value = text[result.start:result.end]

            tokens.append(PIIToken(
                type=pii_type,
                original_value=original_value,
                token_str="",
                start=result.start,
                end=result.end
            ))

        return tokens