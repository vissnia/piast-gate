from domain.enums.pii_type import PIIType
from infrastructure.detectors.email_detector import EmailDetector
from infrastructure.detectors.phone_detector import PhoneDetector
from infrastructure.detectors.pesel_detector import PeselDetector
from infrastructure.detectors.bank_account_detector import BankAccountDetector
from infrastructure.detectors.nip_detector import NipDetector
from infrastructure.detectors.regon_detector import RegonDetector
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
    def test_detects_eleven_digit_sequence_with_valid_checksum(self):
        detector = PeselDetector()
        text = "Jego PESEL to 90010112349 dziękuję."
        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].type == PIIType.PESEL
        assert tokens[0].original_value == "90010112349"

    def test_does_not_match_ten_digit_sequence(self):
        detector = PeselDetector()
        assert detector.detect("numer 9001011234 to nie pesel") == []

    def test_does_not_match_twelve_digit_sequence(self):
        detector = PeselDetector()
        assert detector.detect("numer 900101123456 to nie pesel") == []

    def test_rejects_eleven_digits_with_invalid_checksum(self):
        detector = PeselDetector()
        assert detector.detect("numer zgłoszenia 90010112345 nie jest peselem") == []

    def test_rejects_eleven_digits_with_implausible_month(self):
        detector = PeselDetector()
        assert detector.detect("numer 90990112344 nie jest peselem") == []

    def test_detects_multiple_separate_valid_sequences(self):
        detector = PeselDetector()
        text = "90010112349 oraz 02280512381 to dwa numery."
        tokens = detector.detect(text)

        values = {t.original_value for t in tokens}
        assert values == {"90010112349", "02280512381"}

    def test_empty_text_returns_no_tokens(self):
        detector = PeselDetector()
        assert detector.detect("") == []


class TestBankAccountDetector:
    def test_detects_nrb_number_with_valid_checksum(self):
        detector = BankAccountDetector()
        nrb = "94345678901234567890123456"
        text = f"Numer konta:{nrb}."
        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].type == PIIType.BANK_ACCOUNT
        assert tokens[0].original_value == nrb

    def test_detects_iban_style_number_with_valid_checksum(self):
        detector = BankAccountDetector()
        iban = "DE89370400440532013000"
        text = f"IBAN:{iban}."
        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].type == PIIType.BANK_ACCOUNT
        assert tokens[0].original_value == iban

    def test_rejects_26_digits_with_invalid_checksum(self):
        detector = BankAccountDetector()
        nrb = "12345678901234567890123456"
        assert detector.detect(f"Numer konta:{nrb}.") == []

    def test_rejects_iban_style_number_with_invalid_checksum(self):
        detector = BankAccountDetector()
        iban = "PL61" + "12345678901"
        assert detector.detect(f"IBAN:{iban}.") == []

    def test_does_not_match_pesel_length_sequence(self):
        detector = BankAccountDetector()
        assert detector.detect("PESEL: 90010112345") == []

    def test_empty_text_returns_no_tokens(self):
        detector = BankAccountDetector()
        assert detector.detect("") == []


class TestNipDetector:
    def test_detects_plain_ten_digit_nip_with_valid_checksum(self):
        detector = NipDetector()
        text = "NIP dostawcy: 5260000005."
        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].type == PIIType.NIP
        assert tokens[0].original_value == "5260000005"

    def test_detects_dash_separated_3_3_2_2_format(self):
        detector = NipDetector()
        text = "NIP: 526-000-00-05."
        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].original_value == "526-000-00-05"

    def test_detects_dash_separated_3_2_2_3_format(self):
        detector = NipDetector()
        text = "NIP: 526-00-00-005."
        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].original_value == "526-00-00-005"

    def test_rejects_ten_digits_with_invalid_checksum(self):
        detector = NipDetector()
        assert detector.detect("numer zamówienia 1234567890 przyjęto") == []

    def test_empty_text_returns_no_tokens(self):
        detector = NipDetector()
        assert detector.detect("") == []


class TestRegonDetector:
    def test_detects_nine_digit_regon_with_valid_checksum(self):
        detector = RegonDetector()
        text = "REGON firmy: 123456785."
        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].type == PIIType.REGON
        assert tokens[0].original_value == "123456785"

    def test_detects_fourteen_digit_regon_with_valid_checksum(self):
        detector = RegonDetector()
        text = "REGON jednostki lokalnej: 12345678500010."
        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].original_value == "12345678500010"

    def test_rejects_nine_digits_with_invalid_checksum(self):
        detector = RegonDetector()
        assert detector.detect("kod produktu 123456789 na magazynie") == []

    def test_rejects_fourteen_digits_with_invalid_tail_checksum(self):
        detector = RegonDetector()
        assert detector.detect("numer referencyjny 12345678500011 w systemie") == []

    def test_empty_text_returns_no_tokens(self):
        detector = RegonDetector()
        assert detector.detect("") == []


class _FakeEnt:
    def __init__(self, label, start, end, text):
        self.label_ = label
        self.start_char = start
        self.end_char = end
        self.text = text


class _FakeDoc:
    def __init__(self, ents):
        self.ents = ents


class _FakeNlp:
    def __init__(self, spans):
        self._spans = spans

    def __call__(self, text):
        return _FakeDoc([_FakeEnt(label, s, e, text[s:e]) for label, s, e in self._spans])


def _make_detector(monkeypatch, spans):
    """Builds a PiiPlDetector whose spaCy pipeline is stubbed to return fixed spans."""
    monkeypatch.setattr(PiiPlDetector, "_load_nlp", lambda self: _FakeNlp(spans))
    return PiiPlDetector()


class TestPiiPlDetector:
    def test_maps_person_location_organization_labels(self, monkeypatch):
        text = "Jan Kowalski mieszka w Warszawie i pracuje w Acme."
        spans = [
            ("PERSON", 0, 12),
            ("LOCATION", 23, 32),
            ("ORGANIZATION", 45, 49),
        ]
        detector = _make_detector(monkeypatch, spans)

        tokens = detector.detect(text)

        assert [(t.type, t.original_value) for t in tokens] == [
            (PIIType.PERSON, "Jan Kowalski"),
            (PIIType.LOCATION, "Warszawie"),
            (PIIType.ORGANIZATION, "Acme"),
        ]
        for t in tokens:
            assert text[t.start:t.end] == t.original_value

    def test_skips_unmapped_entity_labels(self, monkeypatch):
        text = "Spotkanie na Euro 2024 w Acme."
        spans = [
            ("EVENT", 13, 22),
            ("ORGANIZATION", 25, 29),
        ]
        detector = _make_detector(monkeypatch, spans)

        tokens = detector.detect(text)

        assert len(tokens) == 1
        assert tokens[0].type == PIIType.ORGANIZATION
        assert tokens[0].original_value == "Acme"

    def test_keeps_adjacent_same_type_entities_separate(self, monkeypatch):
        text = "Warszawa i Krakow."
        spans = [
            ("LOCATION", 0, 8),
            ("LOCATION", 11, 17),
        ]
        detector = _make_detector(monkeypatch, spans)

        tokens = detector.detect(text)

        assert [t.original_value for t in tokens] == ["Warszawa", "Krakow"]

    def test_empty_text_short_circuits_without_calling_model(self, monkeypatch):
        calls = []

        class _TrackingNlp:
            def __call__(self, text):
                calls.append(text)
                return _FakeDoc([])

        monkeypatch.setattr(PiiPlDetector, "_load_nlp", lambda self: _TrackingNlp())
        detector = PiiPlDetector()

        assert detector.detect("") == []
        assert calls == []

    def test_no_entities_returns_empty_list(self, monkeypatch):
        detector = _make_detector(monkeypatch, [])
        assert detector.detect("zwykły tekst bez PII") == []

