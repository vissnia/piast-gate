import logging
import threading
from typing import List

from api.config.config import settings
from .base import BaseNerDetector, RawEntity

logger = logging.getLogger(__name__)


class HfNerDetector(BaseNerDetector):
    """
    "accuracy" mode: a HuggingFace token-classification pipeline
    (radlab/pii-pl-v1.0 by default), labelling PERSON, LOCATION and
    ORGANIZATION (plus other categories the mapping ignores). Noticeably
    slower per request than the spaCy pipeline, in exchange for accuracy.

    Requires the optional "accuracy" extra: pip install -e ".[accuracy]"
    """

    def __init__(self):
        self.model_name = settings.pii_ner_hf_model
        self._pipeline = self._load_pipeline()
        self._lock = threading.Lock()

    def _load_pipeline(self):
        try:
            from transformers import pipeline
        except ImportError as e:
            raise ImportError(
                "PII_NER_MODE=accuracy requires the 'transformers' and 'torch' packages. "
                "Install them with: pip install -e \".[accuracy]\" (or: uv sync --extra accuracy)"
            ) from e

        try:
            nlp = pipeline(
                "ner",
                model=self.model_name,
                tokenizer=self.model_name,
                aggregation_strategy="simple",
            )
            logger.info(f"Loaded PII PL HuggingFace NER model {self.model_name}")
            return nlp
        except Exception as e:
            logger.error(f"Failed to load PII PL HuggingFace NER model {self.model_name}: {e}")
            raise

    def _extract_entities(self, text: str) -> List[RawEntity]:
        results = self._pipeline(text)
        entities: List[RawEntity] = []
        for r in results:
            span = text[r["start"]:r["end"]]
            stripped = span.strip()
            if not stripped:
                continue
            start = r["start"] + span.index(stripped)
            end = start + len(stripped)
            entities.append((r["entity_group"], start, end, stripped))
        return entities
