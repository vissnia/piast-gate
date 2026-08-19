import pytest
from typing import List
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.services.anonymizer_service import AnonymizerService

class MockDetector:
    def __init__(self, tokens_to_return: List[PIIToken]):
        self.tokens_to_return = tokens_to_return

    def detect(self, text: str) -> List[PIIToken]:
        return self.tokens_to_return

@pytest.fixture
def base_text():
    return "Jan Kowalski mieszka w Krakowie i jego email to [EMAIL_ADDRESS]."

def test_anonymize_no_overlap():
    tokens = [
        PIIToken(PIIType.PERSON, "Jan Kowalski", "", 0, 12),
        PIIToken(PIIType.LOCATION, "Krakowie", "", 23, 31),
    ]
    detector = MockDetector(tokens)
    service = AnonymizerService([detector])

    text = "Jan Kowalski mieszka w Krakowie."
    anonymized, mapping = service.anonymize(text)

    assert anonymized == "<PERSON1> mieszka w <LOCATION1>."
    assert "<PERSON1>" in mapping
    assert "<LOCATION1>" in mapping
    assert mapping["<PERSON1>"].original_value == "Jan Kowalski"
    assert mapping["<LOCATION1>"].original_value == "Krakowie"

def test_anonymize_exact_same_bounds():
    tokens = [
        PIIToken(PIIType.PERSON, "Jan Kowalski", "", 0, 12),
        PIIToken(PIIType.ORGANIZATION, "Jan Kowalski", "", 0, 12),
    ]
    detector = MockDetector(tokens)
    service = AnonymizerService([detector])

    text = "Jan Kowalski"
    anonymized, mapping = service.anonymize(text)

    assert anonymized == "<PERSON1>"
    assert len(mapping) == 1
    assert mapping["<PERSON1>"].original_value == "Jan Kowalski"

def test_anonymize_complete_overlap():
    tokens = [
        PIIToken(PIIType.PERSON, "Jan", "", 0, 3),
        PIIToken(PIIType.PERSON, "Jan Kowalski", "", 0, 12),
    ]
    detector = MockDetector(tokens)
    service = AnonymizerService([detector])

    text = "Jan Kowalski"
    anonymized, mapping = service.anonymize(text)

    assert anonymized == "<PERSON1>"
    assert mapping["<PERSON1>"].original_value == "Jan Kowalski"

def test_anonymize_partial_overlap():
    tokens = [
        PIIToken(PIIType.LOCATION, "Kraków", "", 0, 6),
        PIIToken(PIIType.LOCATION, "Kraków, małopolskie", "", 0, 19),
    ]
    detector = MockDetector(tokens)
    service = AnonymizerService([detector])

    text = "Kraków, małopolskie"
    anonymized, mapping = service.anonymize(text)

    assert anonymized == "<LOCATION1>"
    assert len(mapping) == 1
    assert mapping["<LOCATION1>"].original_value == "Kraków, małopolskie"

def test_anonymize_multiple_detectors_overlap():
    detector1 = MockDetector([
        PIIToken(PIIType.PERSON, "Jan", "", 0, 3)
    ])
    detector2 = MockDetector([
        PIIToken(PIIType.PERSON, "Jan Kowalski", "", 0, 12)
    ])
    service = AnonymizerService([detector1, detector2])

    text = "Jan Kowalski"
    anonymized, mapping = service.anonymize(text)

    assert anonymized == "<PERSON1>"
    assert mapping["<PERSON1>"].original_value == "Jan Kowalski"

def test_anonymize_same_value_reuse():
    tokens = [
        PIIToken(PIIType.PERSON, "Jan", "", 0, 3),
        PIIToken(PIIType.PERSON, "Jan", "", 7, 10),
    ]
    detector = MockDetector(tokens)
    service = AnonymizerService([detector])

    text = "Jan to Jan"
    anonymized, mapping = service.anonymize(text)

    assert anonymized == "<PERSON1> to <PERSON1>"
    assert len(mapping) == 1
    assert mapping["<PERSON1>"].original_value == "Jan"

def test_deanonymize():
    tokens = [
        PIIToken(PIIType.PERSON, "Jan Kowalski", "", 0, 12),
        PIIToken(PIIType.LOCATION, "Krakowie", "", 23, 31),
    ]
    detector = MockDetector(tokens)
    service = AnonymizerService([detector])

    text = "Jan Kowalski mieszka w Krakowie."
    anonymized, mapping = service.anonymize(text)
    
    assert anonymized == "<PERSON1> mieszka w <LOCATION1>."
    
    restored = service.deanonymize(anonymized, mapping)
    assert restored == "Jan Kowalski mieszka w Krakowie."

def test_deanonymize_overlapping_token_strings():
    tokens = [PIIToken(PIIType.PERSON, f"Person {i}", "", 0, 8) for i in range(1, 12)]
    
    mapping = {}
    for i, t in enumerate(tokens, start=1):
        token_str = f"<PERSON{i}>"
        t.token_str = token_str
        mapping[token_str] = t
        
    service = AnonymizerService([])
    
    text = "Cześć <PERSON10> i <PERSON1>"
    restored = service.deanonymize(text, mapping)
    
    assert restored == "Cześć Person 10 i Person 1"

@pytest.mark.asyncio
async def test_anonymize_async():
    tokens = [
        PIIToken(PIIType.PERSON, "Jan Kowalski", "", 0, 12),
    ]
    detector = MockDetector(tokens)
    service = AnonymizerService([detector])

    text = "Jan Kowalski mieszka w Krakowie."
    anonymized, mapping = await service.anonymize_async(text)

    assert anonymized == "<PERSON1> mieszka w Krakowie."
    assert "<PERSON1>" in mapping

@pytest.mark.asyncio
async def test_deanonymize_async():
    tokens = [
        PIIToken(PIIType.PERSON, "Jan Kowalski", "", 0, 12),
    ]
    detector = MockDetector(tokens)
    service = AnonymizerService([detector])

    text = "Jan Kowalski mieszka w Krakowie."
    anonymized, mapping = service.anonymize(text)

    restored = await service.deanonymize_async(anonymized, mapping)
    assert restored == text


def test_deanonymize_strips_unresolved_placeholder_shaped_tag():
    """A tag that looks like our placeholder format but isn't in the
    mapping (hallucinated number, or a mangled real one) must not leak."""
    tokens = [PIIToken(PIIType.PERSON, "Jan Kowalski", "<PERSON1>", 0, 12)]
    mapping = {"<PERSON1>": tokens[0]}
    service = AnonymizerService([])

    text = "<PERSON1> rozmawiał z <PERSON99>."
    restored = service.deanonymize(text, mapping)

    assert restored == "Jan Kowalski rozmawiał z ."


def test_deanonymize_strips_residual_tag_with_empty_mapping():
    service = AnonymizerService([])
    restored = service.deanonymize("Cześć <ORGANIZATION3>!", {})
    assert restored == "Cześć !"


def test_deanonymize_leaves_non_placeholder_shaped_brackets_untouched():
    service = AnonymizerService([])
    restored = service.deanonymize("5 <3 10 i <b>bold</b>", {})
    assert restored == "5 <3 10 i <b>bold</b>"


def test_redact_replaces_detected_spans_with_marker():
    tokens = [
        PIIToken(PIIType.PESEL, "90010112349", "", 11, 22),
    ]
    detector = MockDetector(tokens)
    service = AnonymizerService([detector])

    text = "Twój PESEL 90010112349 nigdy nie trafił do modelu."
    redacted, found = service.redact(text)

    assert redacted == "Twój PESEL [REDACTED:PESEL] nigdy nie trafił do modelu."
    assert found == tokens


def test_redact_ignores_matches_inside_intact_placeholder_tags():
    """Regression: a detector (esp. NER) can misread a placeholder's own
    type name as PII in its own right (e.g. "PERSON1" inside "<PERSON1>"
    read as a name) — that must not corrupt the tag deanonymize() still
    needs to resolve."""
    tokens = [PIIToken(PIIType.PERSON, "PERSON1", "", 13, 20)]
    detector = MockDetector(tokens)
    service = AnonymizerService([detector])

    text = "Nazywam się <PERSON1>. Mój PESEL to 90010112349."
    redacted, found = service.redact(text)

    assert redacted == text
    assert found == []


def test_redact_no_matches_returns_text_unchanged():
    service = AnonymizerService([MockDetector([])])
    text = "Zwykła odpowiedź bez PII."

    redacted, found = service.redact(text)

    assert redacted == text
    assert found == []


@pytest.mark.asyncio
async def test_redact_async():
    tokens = [PIIToken(PIIType.EMAIL, "fake@example.com", "", 0, 16)]
    detector = MockDetector(tokens)
    service = AnonymizerService([detector])

    redacted, found = await service.redact_async("fake@example.com to wymyślony adres.")

    assert redacted == "[REDACTED:EMAIL] to wymyślony adres."
    assert found == tokens
