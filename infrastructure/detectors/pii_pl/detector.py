import logging
import re
from typing import Dict, List
from domain.entities.pii_token import PIIToken
from domain.interfaces.pii_detector import PIIDetector
from .mapping import ENTITY_MAPPING
from .onnx_pipeline import OnnxNerPipeline
from api.config.config import settings

logger = logging.getLogger(__name__)

_THRESHOLD = 0.05

_MERGE_GAP_PATTERN = re.compile(r"^[\s.\-]{0,3}$")
_LOCATION_PREFIX_WORDS = {"województwo", "powiat", "gmina", "miasto", "dzielnica", "osiedle"}
_PRECEDING_WORD_PATTERN = re.compile(r"(\S+)(\s+)$")
_LOCATION_LABELS = {"STREET", "CITY"}


def _merge_adjacent_entities(text: str, entities: List[Dict]) -> List[Dict]:
    if not entities:
        return entities

    merged = [dict(entities[0])]
    for entity in entities[1:]:
        last = merged[-1]
        gap = text[last["end"]:entity["start"]]
        same_type = ENTITY_MAPPING.get(entity["entity_group"]) == ENTITY_MAPPING.get(last["entity_group"])
        if same_type and _MERGE_GAP_PATTERN.match(gap):
            last["end"] = entity["end"]
            last["score"] = min(last["score"], entity["score"])
        else:
            merged.append(dict(entity))

    return merged


def _extend_location_prefixes(text: str, entities: List[Dict]) -> List[Dict]:
    extended = []
    for entity in entities:
        if entity["entity_group"] in _LOCATION_LABELS:
            match = _PRECEDING_WORD_PATTERN.search(text[:entity["start"]])
            if match and match.group(1).lower() in _LOCATION_PREFIX_WORDS:
                entity = dict(entity)
                entity["start"] -= len(match.group(1)) + len(match.group(2))
        extended.append(entity)

    return extended


class PiiPlDetector(PIIDetector):
    """
    PII Detector implementation using a Polish token-classification
    NER model: ArkadiuszPawlak/fastpdn-ner-polish-pii.
    """

    def __init__(self):
        self.model_name = settings.pl_ner_model_name
        self.model_revision = settings.pl_ner_model_revision
        self.chunk_tokens = settings.pl_ner_chunk_tokens
        self.chunk_stride = settings.pl_ner_chunk_stride
        self._pipeline = self._load_pipeline()

    def _load_pipeline(self):
        try:
            import os

            os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

            import onnxruntime as ort
            from huggingface_hub import hf_hub_download
            from transformers import AutoConfig, AutoTokenizer

            provider = (
                "CUDAExecutionProvider"
                if "CUDAExecutionProvider" in ort.get_available_providers()
                else "CPUExecutionProvider"
            )
            model_path = hf_hub_download(self.model_name, "model.onnx", revision=self.model_revision)

            session_options = ort.SessionOptions()
            session_options.intra_op_num_threads = 1
            session_options.inter_op_num_threads = 1
            session_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL

            session = ort.InferenceSession(model_path, sess_options=session_options, providers=[provider])
            tokenizer = AutoTokenizer.from_pretrained(self.model_name, revision=self.model_revision)
            tokenizer.model_max_length = self.chunk_tokens
            id2label = AutoConfig.from_pretrained(self.model_name, revision=self.model_revision).id2label

            logger.info(f"Loaded PII PL model {self.model_name}@{self.model_revision} (ONNX, provider={provider})")
            return OnnxNerPipeline(session, tokenizer, id2label)
        except Exception as e:
            logger.error(f"Failed to load PII PL model {self.model_name}@{self.model_revision}: {e}")
            raise

    def detect(self, text: str) -> List[PIIToken]:
        """
        Detects PII in the given text using ArkadiuszPawlak/fastpdn-ner-polish-pii.
        """
        if not text:
            return []

        entities = self._pipeline(text, stride=self.chunk_stride)
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
