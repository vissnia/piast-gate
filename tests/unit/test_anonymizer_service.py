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
