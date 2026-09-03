import logging
import threading
from typing import List

import spacy

from api.config.config import settings
from domain.entities.pii_token import PIIToken
from domain.interfaces.pii_detector import PIIDetector
from .mapping import ENTITY_MAPPING

logger = logging.getLogger(__name__)


class PiiPlDetector(PIIDetector):
    """
    PII detector backed by a locally-bundled spaCy NER pipeline
    (``models/pii_ner_model`` by default), labelling PERSON, LOCATION
    and ORGANIZATION.
    """

    def __init__(self):
        self.model_path = settings.pl_ner_model_path
        self._nlp = self._load_nlp()
        self._lock = threading.Lock()

    def _load_nlp(self):
        try:
            nlp = spacy.load(self.model_path)
            logger.info(
                f"Loaded PII PL spaCy model from {self.model_path} "
                f"(labels: {nlp.get_pipe('ner').labels})"
            )
            return nlp
        except Exception as e:
            logger.error(f"Failed to load PII PL spaCy model from {self.model_path}: {e}")
            raise

    def detect(self, text: str) -> List[PIIToken]:
        """Detects PII in the given text using the bundled spaCy NER model."""
        if not text:
            return []

        with self._lock:
            doc = self._nlp(text)
            entities = [(ent.label_, ent.start_char, ent.end_char, ent.text) for ent in doc.ents]

        tokens: List[PIIToken] = []
        for label, start, end, value in entities:
            pii_type = ENTITY_MAPPING.get(label)
            if not pii_type:
                continue

            tokens.append(PIIToken(
                type=pii_type,
                original_value=value,
                token_str="",
                start=start,
                end=end,
            ))

        return tokens
