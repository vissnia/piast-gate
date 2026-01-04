import pytest
from domain.services.anonymizer_service import AnonymizerService
from infrastructure.detectors.regex_detector import RegexPIIDetector

@pytest.fixture
def service():
    detectors = [RegexPIIDetector()]
    return AnonymizerService(detectors)

def test_anonymize_email(service):
    text = "Contact me at test@example.com."
    anon_text, mapping = service.anonymize(text)
    
    assert "test@example.com" not in anon_text
    assert "<PII:EMAIL:" in anon_text
    assert len(mapping) == 1
    
    # Check if restoration works
    restored_text = service.deanonymize(anon_text, mapping)
    assert restored_text == text

def test_anonymize_no_pii(service):
    text = "Hello world!"
    anon_text, mapping = service.anonymize(text)
    
    assert anon_text == text
    assert len(mapping) == 0

def test_multiple_pii(service):
    text = "Call 123-456-7890 or email foo@bar.com"
    anon_text, mapping = service.anonymize(text)
    
    assert "123-456-7890" not in anon_text
    assert "foo@bar.com" not in anon_text
    assert len(mapping) == 2
    
    restored = service.deanonymize(anon_text, mapping)
    assert restored == text
