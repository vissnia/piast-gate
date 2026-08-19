from typing import List
from domain.entities.pii_token import PIIToken


def remove_overlapping_tokens(tokens: List[PIIToken]) -> List[PIIToken]:
    """
    Resolves overlapping PII token spans: sorts by start position (longest
    span first on ties) and keeps only tokens that don't overlap a
    previously kept one.
    """
    if not tokens:
        return []

    sorted_tokens = sorted(tokens, key=lambda t: (t.start, -(t.end - t.start)))
    result: List[PIIToken] = []
    last_end = -1

    for token in sorted_tokens:
        if token.start >= last_end:
            result.append(token)
            last_end = token.end

    return result
