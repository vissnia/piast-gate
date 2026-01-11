import spacy
import logging
import os
from typing import List
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.interfaces.pii_detector import PIIDetector
from .mapping import ENTITY_MAPPING

logger = logging.getLogger(__name__)

class SpacyPIIDetector(PIIDetector):
    """
    PII Detector implementation using spaCy directly.
    """
    
    def __init__(self, model_name: str = "pl_core_news_lg"):
        self.model_name = os.getenv("PL_NER_MODEL_NAME", model_name)
        self._nlp = self._load_model()

    def _load_model(self):
        try:
            if not spacy.util.is_package(self.model_name):
                logger.info(f"Downloading {self.model_name} model...")
                spacy.cli.download(self.model_name)
            return spacy.load(self.model_name)
        except Exception as e:
            logger.error(f"Failed to load Spacy model {self.model_name}: {e}")
            raise

    def detect(self, text: str) -> List[PIIToken]:
        """
        Detects PII in the given text using Spacy NER.
        """
        if not text:
            return []

        doc = self._nlp(text)
        tokens: List[PIIToken] = []

        for ent in doc.ents:
            pii_type = ENTITY_MAPPING.get(ent.label_)
            
            if not pii_type:
                continue

            tokens.append(PIIToken(
                type=pii_type,
                original_value=ent.text,
                token_str="",
                start=ent.start_char,
                end=ent.end_char
            ))

        return tokens
