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
