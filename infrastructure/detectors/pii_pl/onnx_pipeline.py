from typing import Dict, List, Tuple

import numpy as np


def _softmax(x: np.ndarray) -> np.ndarray:
    x = x - x.max(axis=-1, keepdims=True)
    exp = np.exp(x)
    return exp / exp.sum(axis=-1, keepdims=True)


def _tag_and_type(label: str) -> Tuple[str, str]:
    if label.startswith("B-"):
        return "B", label[2:]
    if label.startswith("I-"):
        return "I", label[2:]
    return "B", label


class OnnxNerPipeline:
    """
    Minimal token-classification pipeline running directly on an ONNX
    Runtime session, reproducing transformers' aggregation_strategy="simple"
    grouping (consecutive same-type B-/I- tokens merged into one span).

    This bypasses `optimum`, whose onnxruntime integration doesn't yet
    support this project's transformers version, and the HF model this
    detector uses ships ONNX weights only (no pytorch_model.bin/safetensors).
    """

    def __init__(self, session, tokenizer, id2label: Dict[int, str]):
        self.session = session
        self.tokenizer = tokenizer
        self.id2label = id2label
        self._input_names = {inp.name for inp in session.get_inputs()}

    def __call__(self, text: str, stride: int = 0, **_) -> List[Dict]:
        if not text:
            return []

        encoding = self.tokenizer(
            text,
            return_offsets_mapping=True,
            return_overflowing_tokens=True,
            return_token_type_ids=True,
            truncation=True,
            max_length=self.tokenizer.model_max_length,
            stride=stride,
            padding=False,
        )

        entities: List[Dict] = []
        for i in range(len(encoding["input_ids"])):
            entities.extend(self._process_chunk(encoding, i))

        entities.sort(key=lambda e: e["start"])
        return entities

    def _process_chunk(self, encoding, index: int) -> List[Dict]:
        input_ids = encoding["input_ids"][index]
        attention_mask = encoding["attention_mask"][index]
        offsets = encoding["offset_mapping"][index]

        ort_inputs = {
            "input_ids": np.array([input_ids], dtype=np.int64),
            "attention_mask": np.array([attention_mask], dtype=np.int64),
        }
        if "token_type_ids" in self._input_names:
            token_type_ids = encoding["token_type_ids"][index]
            ort_inputs["token_type_ids"] = np.array([token_type_ids], dtype=np.int64)

        logits = self.session.run(None, ort_inputs)[0][0]
        scores = _softmax(logits)

        tokens = []
        for j, (start, end) in enumerate(offsets):
            if start == end:
                continue
            label_id = int(scores[j].argmax())
            tokens.append({
                "entity": self.id2label[label_id],
                "score": float(scores[j][label_id]),
                "start": start,
                "end": end,
            })

        return self._group(tokens)

    def _group(self, tokens: List[Dict]) -> List[Dict]:
        groups: List[Dict] = []
        current: List[Dict] = []

        def flush():
            if not current:
                return
            _, tag = _tag_and_type(current[0]["entity"])
            if tag != "O":
                groups.append({
                    "entity_group": tag,
                    "score": sum(t["score"] for t in current) / len(current),
                    "start": current[0]["start"],
                    "end": current[-1]["end"],
                })

        for token in tokens:
            bi, tag = _tag_and_type(token["entity"])
            if current:
                _, last_tag = _tag_and_type(current[-1]["entity"])
                if tag == last_tag and bi != "B":
                    current.append(token)
                    continue
                flush()
            current = [token]
        flush()

        return groups
