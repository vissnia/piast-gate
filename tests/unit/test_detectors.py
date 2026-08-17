import pytest
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from infrastructure.detectors.email_detector import EmailDetector
from infrastructure.detectors.phone_detector import PhoneDetector
from infrastructure.detectors.pesel_detector import PeselDetector
from infrastructure.detectors.bank_account_detector import BankAccountDetector
from infrastructure.detectors.date_detector import DateDetector
from infrastructure.detectors.pii_pl.detector import PiiPlDetector


class TestEmailDetector:
    def test_detects_single_email(self):
        detector = EmailDetector()
        text = "Kontakt: jan.kowalski@example.com proszę."
        tokens = detector.detect(text)

        assert len(tokens) == 1
        token = tokens[0]
        assert token.type == PIIType.EMAIL
        assert token.original_value == "jan.kowalski@example.com"
        assert text[token.start:token.end] == "jan.kowalski@example.com"

    def test_detects_multiple_emails(self):
        detector = EmailDetector()
        text = "a@example.com i b@test.pl to dwa maile."
        tokens = detector.detect(text)

        values = {t.original_value for t in tokens}
        assert values == {"a@example.com", "b@test.pl"}

    def test_no_match_without_at_symbol(self):
        detector = EmailDetector()
        assert detector.detect("to nie jest email.com") == []

    def test_no_match_with_single_char_tld(self):
        detector = EmailDetector()
        assert detector.detect("foo@bar.c") == []

    def test_empty_text_returns_no_tokens(self):
        detector = EmailDetector()
        assert detector.detect("") == []


class TestPhoneDetector:
    def test_detects_valid_polish_mobile_number(self):
        detector = PhoneDetector()
        text = "Zadzwoń pod numer 500123456."
        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].type == PIIType.PHONE
        assert tokens[0].original_value == "500123456"

    def test_detects_number_with_country_code(self):
        detector = PhoneDetector()
        text = "Numer to +48 500 123 456."
        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].type == PIIType.PHONE

    def test_does_not_include_trailing_whitespace(self):
        detector = PhoneDetector()
        text = "Zadzwoń pod numer 500123456 po godzinie 10."
        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].original_value == "500123456"
        assert text[tokens[0].start:tokens[0].end] == "500123456"

    def test_rejects_invalid_number(self):
        detector = PhoneDetector()
        text = "Kod klienta to 000000000 (nie telefon)."
        assert detector.detect(text) == []

    def test_no_candidate_in_short_digit_sequence(self):
        detector = PhoneDetector()
        assert detector.detect("kod: 12345") == []

    def test_no_match_in_plain_text(self):
        detector = PhoneDetector()
        assert detector.detect("Nie ma tu żadnego numeru.") == []


class TestPeselDetector:
    def test_detects_eleven_digit_sequence(self):
        detector = PeselDetector()
        text = "Jego PESEL to 90010112345 dziękuję."
        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].type == PIIType.PESEL
        assert tokens[0].original_value == "90010112345"

    def test_does_not_match_ten_digit_sequence(self):
        detector = PeselDetector()
        assert detector.detect("numer 9001011234 to nie pesel") == []

    def test_does_not_match_twelve_digit_sequence(self):
        detector = PeselDetector()
        assert detector.detect("numer 900101123456 to nie pesel") == []

    def test_detects_multiple_separate_sequences(self):
        detector = PeselDetector()
        text = "90010112345 oraz 12345678901 to dwa numery."
        tokens = detector.detect(text)

        values = {t.original_value for t in tokens}
        assert values == {"90010112345", "12345678901"}

    def test_empty_text_returns_no_tokens(self):
        detector = PeselDetector()
        assert detector.detect("") == []


class TestDateDetector:
    def test_detects_iso_date(self):
        detector = DateDetector()
        text = "Zgłoszenie zarejestrowano dnia 2024-01-15."
        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].type == PIIType.DATE
        assert tokens[0].original_value == "2024-01-15"

    def test_detects_numeric_dotted_date(self):
        detector = DateDetector()
        text = "Termin płatności upływa 31.12.2024."
        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].original_value == "31.12.2024"

    def test_detects_polish_long_form_date(self):
        detector = DateDetector()
        text = "Umowa została podpisana 15 marca 2023 roku."
        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].original_value == "15 marca 2023 roku"

    def test_does_not_include_preceding_word(self):
        detector = DateDetector()
        text = "Zgłoszenie z dnia 3 stycznia 2024 zostało przyjęte."
        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].original_value == "3 stycznia 2024"

    def test_empty_text_returns_no_tokens(self):
        detector = DateDetector()
        assert detector.detect("") == []

    def test_no_match_in_plain_text(self):
        detector = DateDetector()
        assert detector.detect("Nie ma tu żadnej daty.") == []


class TestBankAccountDetector:
    def test_detects_nrb_number(self):
        detector = BankAccountDetector()
        nrb = "12345678901234567890123456"[:26]
        text = f"Numer konta:{nrb}."
        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].type == PIIType.BANK_ACCOUNT
        assert tokens[0].original_value == nrb

    def test_detects_iban_style_number(self):
        detector = BankAccountDetector()
        iban = "PL61" + "12345678901"
        text = f"IBAN:{iban}."
        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].type == PIIType.BANK_ACCOUNT
        assert tokens[0].original_value == iban

    def test_does_not_match_pesel_length_sequence(self):
        detector = BankAccountDetector()
        assert detector.detect("PESEL: 90010112345") == []

    def test_empty_text_returns_no_tokens(self):
        detector = BankAccountDetector()
        assert detector.detect("") == []

    def test_remove_overlaps_keeps_longest_token(self):
        detector = BankAccountDetector()
        tokens = [
            PIIToken(PIIType.BANK_ACCOUNT, "short", "", 5, 20),
            PIIToken(PIIType.BANK_ACCOUNT, "long", "", 0, 26),
        ]

        result = detector._remove_overlaps(tokens)

        assert len(result) == 1
        assert result[0].original_value == "long"

    def test_remove_overlaps_keeps_disjoint_tokens(self):
        detector = BankAccountDetector()
        tokens = [
            PIIToken(PIIType.BANK_ACCOUNT, "first", "", 0, 10),
            PIIToken(PIIType.BANK_ACCOUNT, "second", "", 15, 25),
        ]

        result = detector._remove_overlaps(tokens)

        assert {t.original_value for t in result} == {"first", "second"}

    def test_remove_overlaps_handles_empty_list(self):
        detector = BankAccountDetector()
        assert detector._remove_overlaps([]) == []


def _entity(entity_group, start, end, score=0.99):
    return {"entity_group": entity_group, "score": score, "start": start, "end": end}


class _FakePipeline:
    def __init__(self, entities):
        self._entities = entities

    def __call__(self, text, **kwargs):
        return self._entities


def _make_detector(monkeypatch, entities):
    """Builds a PiiPlDetector whose HF pipeline is stubbed to return fixed entities."""
    monkeypatch.setattr(
        PiiPlDetector, "_load_pipeline", lambda self: _FakePipeline(entities)
    )
    return PiiPlDetector()


class TestPiiPlDetector:
    def test_maps_known_entity_labels(self, monkeypatch):
        text = "Jan Kowalski mieszka w Warszawie."
        entities = [
            _entity("PERSON", 0, 12),
            _entity("LOCATION", 23, 32),
        ]
        detector = _make_detector(monkeypatch, entities)

        tokens = detector.detect(text)

        assert len(tokens) == 2
        assert tokens[0].type == PIIType.PERSON
        assert tokens[0].original_value == "Jan Kowalski"
        assert tokens[1].type == PIIType.LOCATION
        assert tokens[1].original_value == "Warszawie"

    def test_maps_facility_to_location(self, monkeypatch):
        text = "Wysylka na adres ul. Marszalkowska 12, Warszawa."
        entities = [_entity("FACILITY", 21, 34)]
        detector = _make_detector(monkeypatch, entities)

        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].type == PIIType.LOCATION
        assert tokens[0].original_value == "Marszalkowska"

    def test_skips_contact_num_while_unmapped(self, monkeypatch):
        """CONTACT/NUM has no entry in ENTITY_MAPPING (dedicated PhoneDetector handles phones)."""
        text = "Numer: 500123456."
        entities = [_entity("CONTACT/NUM", 7, 16)]
        detector = _make_detector(monkeypatch, entities)

        assert detector.detect(text) == []

    def test_extends_location_with_administrative_prefix_noun(self, monkeypatch):
        text = "Oddzial regionalny obejmuje województwo małopolskie."
        entities = [_entity("LOCATION", 40, 51)]
        detector = _make_detector(monkeypatch, entities)

        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].type == PIIType.LOCATION
        assert tokens[0].original_value == "województwo małopolskie"

    def test_does_not_extend_location_for_unlisted_preceding_word(self, monkeypatch):
        text = "Piekne Krakow."
        entities = [_entity("LOCATION", 7, 13)]
        detector = _make_detector(monkeypatch, entities)

        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].original_value == "Krakow"

    def test_merges_org_split_by_legal_suffix_punctuation(self, monkeypatch):
        text = (
            "Nazywam sie Jan Kowalski, mieszkam w Warszawie i pracuje w "
            "firmie Acme Sp. z o.o. Moj numer to 500123456."
        )
        entities = [
            _entity("ORGANIZATION", 66, 73),
            _entity("ORGANIZATION", 75, 78),
            _entity("ORGANIZATION", 79, 80),
        ]
        detector = _make_detector(monkeypatch, entities)

        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].type == PIIType.ORGANIZATION
        assert tokens[0].original_value == "Acme Sp. z o.o"

    def test_does_not_merge_across_unrelated_text(self, monkeypatch):
        text = "Warszawa jest stolica. Krakow jest stary."
        entities = [
            _entity("LOCATION", 0, 8),
            _entity("LOCATION", 23, 29),
        ]
        detector = _make_detector(monkeypatch, entities)

        tokens = detector.detect(text)

        assert len(tokens) == 2
        assert tokens[0].original_value == "Warszawa"
        assert tokens[1].original_value == "Krakow"

    def test_does_not_merge_different_entity_types(self, monkeypatch):
        text = "Acme w Warszawie."
        entities = [
            _entity("ORGANIZATION", 0, 4),
            _entity("LOCATION", 7, 16),
        ]
        detector = _make_detector(monkeypatch, entities)

        tokens = detector.detect(text)

        assert len(tokens) == 2
        assert tokens[0].type == PIIType.ORGANIZATION
        assert tokens[1].type == PIIType.LOCATION

    def test_skips_unmapped_entity_labels(self, monkeypatch):
        text = "coś nieznanego Acme Sp. z o.o."
        entities = [
            _entity("EVENT", 0, 14),
            _entity("ORGANIZATION", 15, 30),
        ]
        detector = _make_detector(monkeypatch, entities)

        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].type == PIIType.ORGANIZATION

    def test_skips_low_confidence_entities(self, monkeypatch):
        text = "Jan Kowalski"
        entities = [_entity("PERSON", 0, 12, score=0.01)]
        detector = _make_detector(monkeypatch, entities)

        assert detector.detect(text) == []

    def test_empty_text_short_circuits_without_calling_model(self, monkeypatch):
        calls = []

        class _TrackingPipeline:
            def __call__(self, text, **kwargs):
                calls.append(text)
                return []

        monkeypatch.setattr(PiiPlDetector, "_load_pipeline", lambda self: _TrackingPipeline())
        detector = PiiPlDetector()

        tokens = detector.detect("")

        assert tokens == []
        assert calls == []

    def test_no_entities_returns_empty_list(self, monkeypatch):
        detector = _make_detector(monkeypatch, [])
        assert detector.detect("zwykły tekst bez PII") == []
