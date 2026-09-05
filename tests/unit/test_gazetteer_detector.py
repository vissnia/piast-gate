import pytest

from domain.enums.pii_type import PIIType
from infrastructure.detectors.gazetteer import GazetteerDetector


@pytest.fixture(scope="module")
def detector() -> GazetteerDetector:
    """One automaton build shared by the module - it loads ~700k terms."""
    return GazetteerDetector()


def _pairs(tokens):
    return [(t.type, t.original_value) for t in tokens]


class TestGazetteerDetectorPerson:
    def test_given_name_plus_surname_is_one_person_span(self, detector):
        text = "Sprawę prowadzi Jan Kowalski od marca."
        tokens = detector.detect(text)

        assert _pairs(tokens) == [(PIIType.PERSON, "Jan Kowalski")]
        assert text[tokens[0].start:tokens[0].end] == "Jan Kowalski"

    def test_multi_token_name_is_chained(self, detector):
        tokens = detector.detect("Do biura przyszła Anna Maria Wiśniewska.")
        assert _pairs(tokens) == [(PIIType.PERSON, "Anna Maria Wiśniewska")]

    def test_hyphenated_surname_is_kept_whole(self, detector):
        tokens = detector.detect("Prowadzącą jest Zofia Nowak-Jezierska tego dnia.")
        assert _pairs(tokens) == [(PIIType.PERSON, "Zofia Nowak-Jezierska")]

    def test_lone_surname_mid_sentence_is_person(self, detector):
        tokens = detector.detect("Wniosek złożył pan Kowalski w piątek.")
        assert _pairs(tokens) == [(PIIType.PERSON, "Kowalski")]

    def test_lone_given_name_is_not_reported(self, detector):
        assert detector.detect("Na miejscu był tylko Marek wczoraj.") == []

    def test_sentence_initial_lone_surname_is_not_reported(self, detector):
        assert detector.detect("Kowalski przyszedł na spotkanie.") == []

    def test_lowercase_name_is_not_reported(self, detector):
        assert detector.detect("to nazwisko kowalski jest częste") == []

    def test_all_caps_token_is_not_a_person(self, detector):
        assert detector.detect("Numer PESEL to weryfikacji nie przeszedł.") == []

    def test_common_word_surname_is_stopworded(self, detector):
        assert detector.detect("Za oknem rósł stary Dąb przez lata.") == []


class TestGazetteerDetectorLocation:
    def test_city_is_location(self, detector):
        tokens = detector.detect("Oddział mieści się w mieście Poznań obok dworca.")
        assert (PIIType.LOCATION, "Poznań") in _pairs(tokens)

    def test_street_with_trigger_is_location(self, detector):
        tokens = detector.detect("Biuro znajduje się przy ul. Marszałkowska naprzeciwko.")
        assert _pairs(tokens) == [(PIIType.LOCATION, "Marszałkowska")]

    def test_street_name_needs_a_trigger_to_count_as_location(self, detector):
        with_trigger = detector.detect("Idź prosto ul. Ogrodowa aż do końca.")
        without_trigger = detector.detect("Rozważają wariant Ogrodowa dla tej trasy.")

        assert (PIIType.LOCATION, "Ogrodowa") in _pairs(with_trigger)
        assert PIIType.LOCATION not in [t.type for t in without_trigger]

    def test_sentence_initial_locality_is_not_reported(self, detector):
        assert detector.detect("Wygoda to była nazwa tego przysiółka.") == []


class TestGazetteerDetectorMisc:
    def test_empty_text_returns_no_tokens(self, detector):
        assert detector.detect("") == []

    def test_match_inside_a_longer_word_is_rejected(self, detector):
        assert detector.detect("Sprawa Kowalskiego trafiła wczoraj do sądu.") == []

    def test_offsets_point_at_the_original_span(self, detector):
        text = "Pełnomocnik: Piotr Zając, adres w aktach."
        for tok in detector.detect(text):
            assert text[tok.start:tok.end] == tok.original_value
