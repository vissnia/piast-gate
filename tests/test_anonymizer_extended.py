from domain.enums.pii_type import PIIType
import pytest
from domain.services.anonymizer_service import AnonymizerService
from domain.entities.pii_token import PIIToken
from infrastructure.detectors.regex_detector import RegexPIIDetector

@pytest.fixture
def service():
    detectors = [RegexPIIDetector()]
    return AnonymizerService(detectors)

def test_overlapping_pii(service):
    # This is a synthetic test for overlap since regex detector might not produce overlaps naturally with current simple patterns
    # But we can verify that if we *did* have overlapping tokens, the logic holds.
    # We'll mock the detector to return overlapping tokens
    
    class MockDetector:
        def detect(self, text):
            # "apple banana"
            # Token 1: "apple banana" (span 0-12)
            # Token 2: "apple" (span 0-5)
            # Token 3: "banana" (span 6-12)
            # Assuming text is "apple banana"
            return [
                PIIToken(type=PIIType.EMAIL, original_value="apple", token_str="", start=0, end=5),
                PIIToken(type=PIIType.EMAIL, original_value="banana", token_str="", start=6, end=12),
                PIIToken(type=PIIType.EMAIL, original_value="apple banana", token_str="", start=0, end=12),
            ]

    service.detectors = [MockDetector()]
    text = "apple banana"
    anon_text, mapping = service.anonymize(text)
    
    # Should pick "apple banana" because it's longer and starts at same position as "apple"
    # "apple banana" (0, 12)
    # "apple" (0, 5) -> overlapping start
    # "banana" (6, 12) -> overlapping end with "apple banana"
    
    assert "<PII:EMAIL:" in anon_text
    assert "apple" not in anon_text
    assert "banana" not in anon_text
    # It should be exactly one token replacing the whole string
    assert len(mapping) == 1

def test_consistent_tokenization(service):
    text = "Email me at test@example.com or test@example.com"
    anon_text, mapping = service.anonymize(text)
    
    # Check that the same email got the same token ID
    import re
    # Extract all PII tokens
    tokens = re.findall(r"<PII:EMAIL:[a-f0-9-]+>", anon_text)
    assert len(tokens) == 2
    assert tokens[0] == tokens[1] # Should be identical ID for identical value
    assert len(mapping) == 1 # Only one entry in mapping for the unique email
