from typing import List

from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType

_HEURISTIC_TYPES = frozenset({PIIType.PERSON, PIIType.LOCATION, PIIType.ORGANIZATION})


def remove_overlapping_tokens(tokens: List[PIIToken]) -> List[PIIToken]:
    """
    Resolves overlapping PII token spans. A checksum/regex-validated type
    (EMAIL, PHONE, PESEL, NIP, REGON, BANK_ACCOUNT) always wins over an
    overlapping NER/gazetteer type (PERSON, LOCATION, ORGANIZATION), since
    those are heuristic and more prone to misaligned boundaries; within the
    same tier, the earlier, longest span wins as before.
    """
    if not tokens:
        return []

    ordered = sorted(
        tokens,
        key=lambda t: (t.type in _HEURISTIC_TYPES, t.start, -(t.end - t.start)),
    )
    result: List[PIIToken] = []

    for token in ordered:
        if not any(token.start < kept.end and token.end > kept.start for kept in result):
            result.append(token)

    return sorted(result, key=lambda t: t.start)
