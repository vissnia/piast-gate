import sys
from unittest.mock import MagicMock, patch

# Mock libraries that might not be present in test environment or are heavy
sys.modules["spacy"] = MagicMock()

import pytest
from infrastructure.detectors.spacy_detector import SpacyPIIDetector
from domain.enums.pii_type import PIIType

@pytest.fixture
def mock_spacy():
    with patch('infrastructure.detectors.spacy_detector.spacy') as mock:
        yield mock

def test_detect_returns_correct_tokens(mock_spacy):
    # Setup
    mock_nlp = MagicMock()
    mock_spacy.load.return_value = mock_nlp
    
    # Mock entities
    ent1 = MagicMock()
    ent1.text = "Janusz"
    ent1.label_ = "persName"
    ent1.start_char = 0
    ent1.end_char = 6

    ent2 = MagicMock()
    ent2.text = "Warszawa"
    ent2.label_ = "placeName"
    ent2.start_char = 10
    ent2.end_char = 18
    
    mock_doc = MagicMock()
    mock_doc.ents = [ent1, ent2]
    mock_nlp.return_value = mock_doc
    
    detector = SpacyPIIDetector()
    text = "Janusz w Warszawa"
    
    # Execute
    tokens = detector.detect(text)
    
    # Verify
    assert len(tokens) == 2
    
    assert tokens[0].type == PIIType.PERSON
    assert tokens[0].original_value == "Janusz"
    assert tokens[0].start == 0
    assert tokens[0].end == 6
    
    assert tokens[1].type == PIIType.LOCATION
    assert tokens[1].original_value == "Warszawa"
    assert tokens[1].start == 10
    assert tokens[1].end == 18

def test_detect_handles_unknown_labels(mock_spacy):
    # Setup
    mock_nlp = MagicMock()
    mock_spacy.load.return_value = mock_nlp
    
    ent1 = MagicMock()
    ent1.label_ = "UNKNOWN_LABEL"
    ent1.text = "Some text"
    
    mock_doc = MagicMock()
    mock_doc.ents = [ent1]
    mock_nlp.return_value = mock_doc
    
    detector = SpacyPIIDetector()
    
    # Execute
    tokens = detector.detect("Some text")
    
    # Verify
    assert len(tokens) == 0

def test_config_model_name(mock_spacy):
    with patch.dict('os.environ', {'PL_NER_MODEL_NAME': 'custom_model'}):
        detector = SpacyPIIDetector()
        mock_spacy.load.assert_called_with('custom_model')
