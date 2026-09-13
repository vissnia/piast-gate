from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.services.token_overlap import remove_overlapping_tokens


class TestRemoveOverlappingTokens:
    def test_keeps_longest_token(self):
        tokens = [
            PIIToken(PIIType.BANK_ACCOUNT, "short", "", 5, 20),
            PIIToken(PIIType.BANK_ACCOUNT, "long", "", 0, 26),
        ]

        result = remove_overlapping_tokens(tokens)

        assert len(result) == 1
        assert result[0].original_value == "long"

    def test_keeps_disjoint_tokens(self):
        tokens = [
            PIIToken(PIIType.BANK_ACCOUNT, "first", "", 0, 10),
            PIIToken(PIIType.BANK_ACCOUNT, "second", "", 15, 25),
        ]

        result = remove_overlapping_tokens(tokens)

        assert {t.original_value for t in result} == {"first", "second"}

    def test_handles_empty_list(self):
        assert remove_overlapping_tokens([]) == []

    def test_validated_type_wins_over_overlapping_ner_type_regardless_of_position(self):
        tokens = [
            PIIToken(PIIType.LOCATION, "widerange", "", 0, 30),
            PIIToken(PIIType.EMAIL, "jan@krakow-firma.pl", "", 5, 24),
        ]

        result = remove_overlapping_tokens(tokens)

        assert len(result) == 1
        assert result[0].type == PIIType.EMAIL

    def test_validated_type_wins_even_when_ner_span_starts_earlier(self):
        tokens = [
            PIIToken(PIIType.PERSON, "Jan Kowalski 600", "", 0, 17),
            PIIToken(PIIType.PHONE, "600123456", "", 13, 22),
        ]

        result = remove_overlapping_tokens(tokens)

        assert [t.type for t in result] == [PIIType.PHONE]

    def test_non_overlapping_validated_and_ner_tokens_both_kept_in_order(self):
        tokens = [
            PIIToken(PIIType.LOCATION, "Krakowie", "", 20, 28),
            PIIToken(PIIType.EMAIL, "jan@example.com", "", 0, 15),
        ]

        result = remove_overlapping_tokens(tokens)

        assert [t.type for t in result] == [PIIType.EMAIL, PIIType.LOCATION]
