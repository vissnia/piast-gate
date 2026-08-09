import pytest
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from infrastructure.detectors.email_detector import EmailDetector
from infrastructure.detectors.phone_detector import PhoneDetector
from infrastructure.detectors.pesel_detector import PeselDetector
from infrastructure.detectors.bank_account_detector import BankAccountDetector
from infrastructure.detectors.spacy.detector import SpacyPIIDetector


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


class _FakeEntity:
    def __init__(self, label_, text, start_char, end_char):
        self.label_ = label_
        self.text = text
        self.start_char = start_char
        self.end_char = end_char


class _FakeDoc:
    def __init__(self, ents):
        self.ents = ents


def _make_detector(monkeypatch, ents):
    """Builds a SpacyPIIDetector whose model is stubbed to return fixed entities."""
    monkeypatch.setattr(
        SpacyPIIDetector, "_load_model", lambda self: lambda text: _FakeDoc(ents)
    )
    return SpacyPIIDetector()


class TestSpacyPIIDetector:
    def test_maps_known_entity_labels(self, monkeypatch):
        ents = [
            _FakeEntity("persName", "Jan Kowalski", 0, 12),
            _FakeEntity("placeName", "Warszawa", 20, 28),
        ]
        detector = _make_detector(monkeypatch, ents)

        tokens = detector.detect("Jan Kowalski mieszka w Warszawa.")

        assert len(tokens) == 2
        assert tokens[0].type == PIIType.PERSON
        assert tokens[0].original_value == "Jan Kowalski"
        assert tokens[1].type == PIIType.LOCATION
        assert tokens[1].original_value == "Warszawa"

    def test_skips_unmapped_entity_labels(self, monkeypatch):
        ents = [
            _FakeEntity("MISC", "coś nieznanego", 0, 14),
            _FakeEntity("orgName", "Acme Sp. z o.o.", 20, 35),
        ]
        detector = _make_detector(monkeypatch, ents)

        tokens = detector.detect("tekst testowy")

        assert len(tokens) == 1
        assert tokens[0].type == PIIType.ORGANIZATION

    def test_empty_text_short_circuits_without_calling_model(self, monkeypatch):
        calls = []

        def fake_load(self):
            def nlp(text):
                calls.append(text)
                return _FakeDoc([])
            return nlp

        monkeypatch.setattr(SpacyPIIDetector, "_load_model", fake_load)
        detector = SpacyPIIDetector()

        tokens = detector.detect("")

        assert tokens == []
        assert calls == []

    def test_no_entities_returns_empty_list(self, monkeypatch):
        detector = _make_detector(monkeypatch, [])
        assert detector.detect("zwykły tekst bez PII") == []
