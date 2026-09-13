import logging
import threading
from typing import List, Tuple

from domain.entities.pii_token import PIIToken
from domain.interfaces.pii_detector import PIIDetector
from .mapping import ENTITY_MAPPING

logger = logging.getLogger(__name__)

RawEntity = Tuple[str, int, int, str]


class BaseNerDetector(PIIDetector):
    """
    Shared PERSON/LOCATION/ORGANIZATION detection logic for the NER-backed
    detectors. Subclasses only need to load a model and turn a text into a
    list of (label, start_char, end_char, text) spans via ``_extract_entities``.
    """

    _lock: threading.Lock

    def _extract_entities(self, text: str) -> List[RawEntity]:
        raise NotImplementedError

    def detect(self, text: str) -> List[PIIToken]:
        if not text:
            return []

        with self._lock:
            entities = self._extract_entities(text)

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
