import re
import spacy
import logging
from typing import List, Optional, Tuple
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.interfaces.pii_detector import PIIDetector
from .mapping import ENTITY_MAPPING
from api.config.config import settings

logger = logging.getLogger(__name__)

_LOCATION_STOPWORDS = {"ul.", "al.", "pl."}

_LEGAL_SUFFIX_CONTINUATIONS = [
    (("Sp.", "sp."), re.compile(r"\s*z\s+o\.?\s*o\.?")),
    (("S.",), re.compile(r"\s*A\.")),
]

class SpacyPIIDetector(PIIDetector):
    """
    PII Detector implementation using spaCy directly.
    """
    
    def __init__(self):
        self.model_name = settings.pl_ner_model_name
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

            if pii_type == PIIType.LOCATION and ent.text.strip().lower() in _LOCATION_STOPWORDS:
                continue

            tokens.append(PIIToken(
                type=pii_type,
                original_value=ent.text,
                token_str="",
                start=ent.start_char,
                end=ent.end_char
            ))

        return self._merge_legal_suffixes(tokens, text)

    def _merge_legal_suffixes(self, tokens: List[PIIToken], text: str) -> List[PIIToken]:
        """
        Stitches Polish legal-entity suffixes (e.g. "z o.o.", "S.A.") back onto
        the ORGANIZATION entity spaCy split them off from, dropping any other
        entity fully absorbed by the merge (e.g. a trailing "A." mistagged PERSON).
        """
        tokens_by_start = sorted(tokens, key=lambda t: t.start)
        result: List[PIIToken] = []
        skip_until = -1

        for token in tokens_by_start:
            if token.start < skip_until:
                continue

            if token.type == PIIType.ORGANIZATION:
                extension = self._match_legal_suffix(token, text)
                if extension:
                    new_end, new_value = extension
                    token = PIIToken(PIIType.ORGANIZATION, new_value, "", token.start, new_end)
                    skip_until = new_end

            result.append(token)

        return result

    def _match_legal_suffix(self, token: PIIToken, text: str) -> Optional[Tuple[int, str]]:
        for suffixes, continuation in _LEGAL_SUFFIX_CONTINUATIONS:
            if token.original_value.endswith(suffixes):
                match = continuation.match(text, token.end)
                if match:
                    return match.end(), text[token.start:match.end()]
        return None
