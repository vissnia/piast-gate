import sys
from unittest.mock import MagicMock

# Mock libraries that cause issues on Python 3.14 or require installation
sys.modules["spacy"] = MagicMock()
sys.modules["presidio_analyzer"] = MagicMock()
# Mock submodules causing issues
sys.modules["presidio_analyzer.analyzer_engine"] = MagicMock()

import pytest
from unittest.mock import patch, MagicMock 
# Re-import mocked modules for typing if needed, 
# but PresidioPIIDetector import needs them mocked first.

from infrastructure.detectors.presidio_detector import PresidioPIIDetector
from domain.enums.pii_type import PIIType

# We need to ensure RecognizerResult is available for our test setup
# Since we mocked presidio_analyzer, we need to defined a dummy RecognizerResult
class RecognizerResult:
    def __init__(self, entity_type, start, end, score):
        self.entity_type = entity_type
        self.start = start
        self.end = end
        self.score = score



@pytest.fixture
def mock_analyzer_engine():
    with patch('infrastructure.detectors.presidio_detector.get_analyzer_engine') as mock_get:
        mock_engine = MagicMock()
        mock_get.return_value = mock_engine
        yield mock_engine

def test_detect_returns_correct_tokens(mock_analyzer_engine):
    # Setup
    mock_analyzer_engine.analyze.return_value = [
        RecognizerResult(entity_type="PERSON", start=0, end=8, score=0.85),
        RecognizerResult(entity_type="EMAIL_ADDRESS", start=23, end=39, score=0.99)
    ]
    
    detector = PresidioPIIDetector()
    text = "John Doe sent email to test@example.com"
    
    # Execute
    tokens = detector.detect(text)
    
    # Verify
    assert len(tokens) == 2
    
    # Check Person
    assert tokens[0].type == PIIType.PERSON
    assert tokens[0].original_value == "John Doe"
    assert tokens[0].start == 0
    assert tokens[0].end == 8
    
    # Check Email
    assert tokens[1].type == PIIType.EMAIL
    assert tokens[1].original_value == "test@example.com"
    assert tokens[1].start == 23
    assert tokens[1].end == 39

def test_detect_handles_unknown_types(mock_analyzer_engine):
    # Setup
    mock_analyzer_engine.analyze.return_value = [
        RecognizerResult(entity_type="UNKNOWN_TYPE", start=0, end=5, score=0.5)
    ]
    
    detector = PresidioPIIDetector()
    
    # Execute
    tokens = detector.detect("Tests")
    
    # Verify
    assert len(tokens) == 0

def test_detect_handles_empty_text(mock_analyzer_engine):
    detector = PresidioPIIDetector()
    tokens = detector.detect("")
    assert len(tokens) == 0

def test_entity_mapping_completeness(mock_analyzer_engine):
    detector = PresidioPIIDetector()
    
    assert "PERSON" in detector.ENTITY_MAPPING
    assert detector.ENTITY_MAPPING["PERSON"] == PIIType.PERSON
    
    assert "LOCATION" in detector.ENTITY_MAPPING
    assert detector.ENTITY_MAPPING["LOCATION"] == PIIType.LOCATION
    
    assert "ORG" in detector.ENTITY_MAPPING
    assert detector.ENTITY_MAPPING["ORG"] == PIIType.ORGANIZATION
