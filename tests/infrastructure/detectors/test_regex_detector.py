import pytest
from infrastructure.detectors.email_detector import RegexPIIDetector
from domain.enums.pii_type import PIIType

def test_detect_email():
    detector = RegexPIIDetector()
    text = "Contact us at support@example.com for info."
    tokens = detector.detect(text)
    
    email_tokens = [t for t in tokens if t.type == PIIType.EMAIL]
    assert len(email_tokens) == 1
    assert email_tokens[0].original_value == "support@example.com"

def test_detect_phone():
    detector = RegexPIIDetector()
    text = "Call +48 123-456-7890 now."
    tokens = detector.detect(text)
    
    # Phone regex might catch parts, checking one
    phone_tokens = [t for t in tokens if t.type == PIIType.PHONE]
    assert len(phone_tokens) > 0
    assert "123-456-7890" in [t.original_value for t in phone_tokens] or "+48 123-456-7890" in [t.original_value for t in phone_tokens]

