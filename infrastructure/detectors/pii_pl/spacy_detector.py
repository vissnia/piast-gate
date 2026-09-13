import logging
import threading
from typing import List

import spacy

from api.config.config import settings
from .base import BaseNerDetector, RawEntity

logger = logging.getLogger(__name__)


class SpacyNerDetector(BaseNerDetector):
    """
    "efficiency" mode: a locally-bundled spaCy NER pipeline
    (``models/pii_ner_model`` by default), labelling PERSON, LOCATION
    and ORGANIZATION. Fast enough to run inline on every request.
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

    def _extract_entities(self, text: str) -> List[RawEntity]:
        doc = self._nlp(text)
        return [(ent.label_, ent.start_char, ent.end_char, ent.text) for ent in doc.ents]
