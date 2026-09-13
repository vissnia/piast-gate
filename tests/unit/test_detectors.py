import pytest

from domain.enums.pii_type import PIIType
from infrastructure.detectors.email_detector import EmailDetector
from infrastructure.detectors.phone_detector import PhoneDetector
from infrastructure.detectors.pesel_detector import PeselDetector
from infrastructure.detectors.bank_account_detector import BankAccountDetector
from infrastructure.detectors.nip_detector import NipDetector
from infrastructure.detectors.regon_detector import RegonDetector
from infrastructure.detectors.pii_pl import create_pii_ner_detector
from infrastructure.detectors.pii_pl.spacy_detector import SpacyNerDetector
from infrastructure.detectors.pii_pl.hf_detector import HfNerDetector


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

    def test_detects_26_digits_with_invalid_checksum(self):
        detector = BankAccountDetector()
        nrb = "12345678901234567890123457"
        tokens = detector.detect(f"Numer konta:{nrb}.")

        assert len(tokens) == 1
        assert tokens[0].original_value == nrb

    def test_detects_iban_style_number_with_invalid_checksum(self):
        detector = BankAccountDetector()
        iban = "PL61" + "12345678902"
        tokens = detector.detect(f"IBAN:{iban}.")

        assert len(tokens) == 1
        assert tokens[0].original_value == iban

    def test_rejects_repeated_digit_placeholder(self):
        detector = BankAccountDetector()
        nrb = "00000000000000000000000000"
        assert detector.detect(f"Numer konta:{nrb}.") == []


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
    """Builds a SpacyNerDetector whose spaCy pipeline is stubbed to return fixed spans."""
    monkeypatch.setattr(SpacyNerDetector, "_load_nlp", lambda self: _FakeNlp(spans))
    return SpacyNerDetector()


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

        monkeypatch.setattr(SpacyNerDetector, "_load_nlp", lambda self: _TrackingNlp())
        detector = SpacyNerDetector()

        assert detector.detect("") == []
        assert calls == []

    def test_no_entities_returns_empty_list(self, monkeypatch):
        detector = _make_detector(monkeypatch, [])
        assert detector.detect("zwykły tekst bez PII") == []


class TestNeverOrganizationFilter:
    """NIP/REGON/KRS/CEIDG are registry-identifier labels the NER model
    sometimes mistakes for a company name on their own; infrastructure/
    detectors/pii_pl/never_organization.txt lists terms that must never
    surface as an ORGANIZATION, shared by every BaseNerDetector subclass."""

    def test_blocklisted_terms_are_dropped(self, monkeypatch):
        text = "W KRS figurują dane: NIP: 700-001-02-03, REGON: 555000125, zgodnie z CEIDG."
        terms = ["KRS", "NIP", "REGON", "CEIDG"]
        spans = [("ORGANIZATION", text.index(term), text.index(term) + len(term)) for term in terms]
        detector = _make_detector(monkeypatch, spans)

        assert detector.detect(text) == []

    def test_is_case_insensitive(self, monkeypatch):
        text = "regon firmy to nie organizacja."
        detector = _make_detector(monkeypatch, [("ORGANIZATION", 0, 5)])

        assert detector.detect(text) == []

    def test_does_not_drop_a_real_organization(self, monkeypatch):
        text = "Sprzedawca: ABC Sp. z o.o."
        detector = _make_detector(monkeypatch, [("ORGANIZATION", 12, 26)])

        tokens = detector.detect(text)

        assert [t.original_value for t in tokens] == ["ABC Sp. z o.o."]

    def test_only_applies_to_organization_type(self, monkeypatch):
        text = "NIP"
        detector = _make_detector(monkeypatch, [("PERSON", 0, 3)])

        tokens = detector.detect(text)

        assert [t.original_value for t in tokens] == ["NIP"]

    def test_hf_detector_also_filters_blocklisted_organizations(self, monkeypatch):
        text = "Dane zgodne z CEIDG i REGON."
        results = [
            {"entity_group": "ORGANIZATION", "start": 14, "end": 19},
            {"entity_group": "ORGANIZATION", "start": 22, "end": 27},
        ]
        monkeypatch.setattr(HfNerDetector, "_load_pipeline", lambda self: (lambda t: results))
        detector = HfNerDetector()

        assert detector.detect(text) == []


class TestHfNerDetector:
    """The mapping/aggregation logic is shared with SpacyNerDetector via
    BaseNerDetector; these tests focus on translating the HF pipeline's
    dict output (entity_group/start/end) into PIITokens."""

    def _make_detector(self, monkeypatch, results):
        monkeypatch.setattr(HfNerDetector, "_load_pipeline", lambda self: (lambda text: results))
        return HfNerDetector()

    def test_maps_person_location_organization_labels(self, monkeypatch):
        text = "Jan Kowalski mieszka w Warszawie i pracuje w Acme."
        results = [
            {"entity_group": "PERSON", "start": 0, "end": 12},
            {"entity_group": "LOCATION", "start": 23, "end": 32},
            {"entity_group": "ORGANIZATION", "start": 45, "end": 49},
        ]
        detector = self._make_detector(monkeypatch, results)

        tokens = detector.detect(text)

        assert [(t.type, t.original_value) for t in tokens] == [
            (PIIType.PERSON, "Jan Kowalski"),
            (PIIType.LOCATION, "Warszawie"),
            (PIIType.ORGANIZATION, "Acme"),
        ]

    def test_skips_unmapped_entity_labels(self, monkeypatch):
        text = "Zadzwoń pod 123456789 w sprawie iPhone."
        results = [
            {"entity_group": "CONTACT/NUM", "start": 12, "end": 21},
            {"entity_group": "PRODUCT", "start": 33, "end": 39},
        ]
        detector = self._make_detector(monkeypatch, results)

        assert detector.detect(text) == []

    def test_trims_leading_whitespace_the_tokenizer_folds_into_the_span(self, monkeypatch):
        """Regression: this model's byte-level BPE tokenizer attributes the
        space before a word to that word's token, so aggregated start/end
        can include it (e.g. start/end covering " PKO BP" instead of "PKO
        BP"). Left untrimmed, original_value and start/end both drift by
        one, and the resulting text[start:end] no longer round-trips."""
        text = "Jan Kowalski z firmy PKO BP mieszka w Warszawie."
        results = [
            {"entity_group": "PERSON", "start": 0, "end": 12},
            {"entity_group": "ORGANIZATION", "start": 20, "end": 27},
            {"entity_group": "LOCATION", "start": 37, "end": 47},
        ]
        detector = self._make_detector(monkeypatch, results)

        tokens = detector.detect(text)

        assert [(t.type, t.original_value) for t in tokens] == [
            (PIIType.PERSON, "Jan Kowalski"),
            (PIIType.ORGANIZATION, "PKO BP"),
            (PIIType.LOCATION, "Warszawie"),
        ]
        for t in tokens:
            assert text[t.start:t.end] == t.original_value

    def test_empty_text_short_circuits_without_calling_model(self, monkeypatch):
        calls = []
        monkeypatch.setattr(
            HfNerDetector, "_load_pipeline", lambda self: (lambda text: calls.append(text))
        )
        detector = HfNerDetector()

        assert detector.detect("") == []
        assert calls == []

    def test_missing_transformers_raises_helpful_error(self, monkeypatch):
        import builtins

        real_import = builtins.__import__

        def _fake_import(name, *args, **kwargs):
            if name == "transformers":
                raise ImportError("no module named transformers")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", _fake_import)

        with pytest.raises(ImportError, match="accuracy"):
            HfNerDetector()


class TestCreatePiiNerDetector:
    def test_efficiency_mode_builds_spacy_detector(self, monkeypatch):
        monkeypatch.setattr(SpacyNerDetector, "_load_nlp", lambda self: _FakeNlp([]))
        detector = create_pii_ner_detector("efficiency")
        assert isinstance(detector, SpacyNerDetector)

    def test_accuracy_mode_builds_hf_detector(self, monkeypatch):
        monkeypatch.setattr(HfNerDetector, "_load_pipeline", lambda self: (lambda text: []))
        detector = create_pii_ner_detector("accuracy")
        assert isinstance(detector, HfNerDetector)

    def test_unknown_mode_raises(self):
        with pytest.raises(ValueError, match="bogus"):
            create_pii_ner_detector("bogus")

