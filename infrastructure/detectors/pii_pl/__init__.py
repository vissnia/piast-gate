from api.config.config import settings
from .base import BaseNerDetector
from .spacy_detector import SpacyNerDetector
from .hf_detector import HfNerDetector

__all__ = ["BaseNerDetector", "SpacyNerDetector", "HfNerDetector", "create_pii_ner_detector"]

_MODES = {
    "efficiency": SpacyNerDetector,
    "accuracy": HfNerDetector,
}


def create_pii_ner_detector(mode: str | None = None) -> BaseNerDetector:
    """Builds the PERSON/LOCATION/ORGANIZATION detector for the given mode
    (``PII_NER_MODE`` setting when omitted): "efficiency" (spaCy) or
    "accuracy" (HuggingFace radlab/pii-pl-v1.0)."""
    mode = mode or settings.pii_ner_mode
    detector_cls = _MODES.get(mode)
    if not detector_cls:
        raise ValueError(f"Unknown PII_NER_MODE '{mode}', expected one of {sorted(_MODES)}")
    return detector_cls()
