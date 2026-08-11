import logging
import re
from typing import Dict, List
from domain.entities.pii_token import PIIToken
from domain.interfaces.pii_detector import PIIDetector
from .mapping import ENTITY_MAPPING
from api.config.config import settings

logger = logging.getLogger(__name__)

_THRESHOLD = 0.05

_MERGE_GAP_PATTERN = re.compile(r"^[\s.\-]{0,3}$")
_LOCATION_PREFIX_WORDS = {"województwo", "powiat", "gmina", "miasto", "dzielnica", "osiedle"}
_PRECEDING_WORD_PATTERN = re.compile(r"(\S+)(\s+)$")


def _merge_adjacent_entities(text: str, entities: List[Dict]) -> List[Dict]:
    if not entities:
        return entities

    merged = [dict(entities[0])]
    for entity in entities[1:]:
        last = merged[-1]
        gap = text[last["end"]:entity["start"]]
        if entity["entity_group"] == last["entity_group"] and _MERGE_GAP_PATTERN.match(gap):
            last["end"] = entity["end"]
            last["score"] = min(last["score"], entity["score"])
        else:
            merged.append(dict(entity))

    return merged


def _extend_location_prefixes(text: str, entities: List[Dict]) -> List[Dict]:
    extended = []
    for entity in entities:
        if entity["entity_group"] == "LOCATION":
            match = _PRECEDING_WORD_PATTERN.search(text[:entity["start"]])
            if match and match.group(1).lower() in _LOCATION_PREFIX_WORDS:
                entity = dict(entity)
                entity["start"] -= len(match.group(1)) + len(match.group(2))
        extended.append(entity)

    return extended


class PiiPlDetector(PIIDetector):
    """
    PII Detector implementation using a Polish token-classification
    NER model: radlab/pii-pl-v1.0.
    """

    def __init__(self):
        self.model_name = settings.pl_ner_model_name
        self._pipeline = self._load_pipeline()

    def _load_pipeline(self):
        try:
            from transformers import pipeline
            return pipeline(
                "ner",
                model=self.model_name,
                tokenizer=self.model_name,
                aggregation_strategy="simple",
            )
        except Exception as e:
            logger.error(f"Failed to load PII PL model {self.model_name}: {e}")
            raise

    def detect(self, text: str) -> List[PIIToken]:
        """
        Detects PII in the given text using radlab/pii-pl-v1.0.
        """
        if not text:
            return []

        entities = self._pipeline(text)
        entities = _extend_location_prefixes(text, entities)
        entities = _merge_adjacent_entities(text, entities)

        tokens: List[PIIToken] = []
        for entity in entities:
            pii_type = ENTITY_MAPPING.get(entity["entity_group"])

            if not pii_type:
                continue

            if entity["score"] < _THRESHOLD:
                continue

            start, end = entity["start"], entity["end"]

            tokens.append(PIIToken(
                type=pii_type,
                original_value=text[start:end],
                token_str="",
                start=start,
                end=end
            ))

        return tokens
