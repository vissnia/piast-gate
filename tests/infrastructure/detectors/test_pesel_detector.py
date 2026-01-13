import pytest
from infrastructure.detectors.pesel_detector import PeselDetector
from domain.enums.pii_type import PIIType

def test_pesel_detector_valid():
    """Test with a valid PESEL."""
    detector = PeselDetector()
    text = "Mój PESEL to 44051401359."
    results = detector.detect(text)
    
    assert len(results) == 1
    assert results[0].type == PIIType.PESEL
    assert results[0].original_value == "44051401359"
    assert results[0].start == 13
    assert results[0].end == 24

def test_pesel_detector_invalid_checksum():
    """Test with an invalid PESEL checksum."""
    detector = PeselDetector()
    text = "To jest niepoprawny PESEL: 44051401358."
    results = detector.detect(text)
    
    assert len(results) == 0

def test_pesel_detector_invalid_length():
    """Test with a PESEL of invalid length."""
    detector = PeselDetector()
    text = "Krótki PESEL: 123456789."
    results = detector.detect(text)
    
    assert len(results) == 0

def test_pesel_detector_non_digit():
    """Test with non-digit characters."""
    detector = PeselDetector()
    text = "PESEL z literą: 4405140135A."
    results = detector.detect(text)
    
    assert len(results) == 0

def test_pesel_detector_multiple():
    """Test with multiple PESELs."""
    detector = PeselDetector()
    text = "Dwa PESEL-e: 44051401359 i 92082612348."
    # 92082612348:
    # 9*1 + 2*3 + 0*7 + 8*9 + 2*1 + 6*3 + 1*7 + 2*9 + 3*1 + 4*3 = 9 + 6 + 0 + 72 + 2 + 18 + 7 + 18 + 3 + 12 = 147
    # 147 % 10 = 7
    # 10 - 7 = 3
    # Wait, let me check the example 92082612348.
    # 92082612348 -> control digit 8?
    # 9*1 = 9
    # 2*3 = 6
    # 0*7 = 0
    # 8*9 = 72
    # 2*1 = 2
    # 6*3 = 18
    # 1*7 = 7
    # 2*9 = 18
    # 3*1 = 3
    # 4*3 = 12
    # Sum: 9+6+0+72+2+18+7+18+3+12 = 147. 10 - (147%10) = 3. So 92082612343 should be valid.
    
    valid_pesel_1 = "44051401359"
    valid_pesel_2 = "92082612343"
    text = f"Dwa PESEL-e: {valid_pesel_1} i {valid_pesel_2}."
    results = detector.detect(text)
    
    assert len(results) == 2
    assert results[0].original_value == valid_pesel_1
    assert results[1].original_value == valid_pesel_2
