import re
from typing import List, Tuple

from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType

_STREET_PREFIX_RE = re.compile(r"(?:ul|al|pl|os|zam)\.?\s*$", re.IGNORECASE)
_STREET_PREFIX_START_RE = re.compile(r"^(?:ul|al|pl|os|zam)\.?\s*", re.IGNORECASE)
_ADMIN_PREFIX_RE = re.compile(
    r"(?:wojew[oó]dztw[a-ząęó]*|woj\.|powiat(?:ci?e)?|gmin[ayę]|miejscowo[śs]ci?)\s*$",
    re.IGNORECASE,
)
_BUILDING_NUMBER_RE = re.compile(
    r"^\.?\s*\d+[^\W\d_]?(?:/\d+)?(?:\s*m\.?\s*\d+)?",
    re.IGNORECASE,
)
_POSTAL_CODE = r"\d{2}-?\s*\d{3}"
_POSTAL_CODE_SUFFIX_RE = re.compile(rf"{_POSTAL_CODE}\s*$")
_GLUE_RE = re.compile(rf"^,\s*(?:{_POSTAL_CODE}\s*)?$|^\s+we?\s+$", re.IGNORECASE)


def merge_location_spans(text: str, tokens: List[PIIToken]) -> List[PIIToken]:
    """
    Stitches together LOCATION spans that belong to one address or
    administrative-hierarchy mention but were tagged as separate fragments
    by the upstream detectors (a street name, a building number, a postal
    code, a city, each caught independently): absorbs a street/admin-unit
    prefix word and a trailing building number directly against a span,
    then merges spans still joined only by a comma (optionally carrying a
    postal code) or a bare "w"/"we".

    Expects ``tokens`` already overlap-resolved and does not itself detect
    any new PII — only grows and combines spans detectors already found.
    """
    if not tokens:
        return tokens

    ordered = sorted(tokens, key=lambda t: t.start)
    floors = [0] + [t.end for t in ordered[:-1]]
    ceilings = [t.start for t in ordered[1:]] + [len(text)]

    grown: List[PIIToken] = []
    for token, floor, ceiling in zip(ordered, floors, ceilings):
        if token.type is not PIIType.LOCATION:
            grown.append(token)
            continue
        start, end = _grow_location_span(text, token.start, token.end, floor, ceiling)
        grown.append(_retagged(token, start, end, text))

    merged: List[PIIToken] = []
    for token in grown:
        if (
            merged
            and merged[-1].type is PIIType.LOCATION
            and token.type is PIIType.LOCATION
            and _GLUE_RE.match(text[merged[-1].end:token.start])
        ):
            prev = merged.pop()
            token = _retagged(token, prev.start, token.end, text)
        merged.append(token)

    return merged


def _grow_location_span(text: str, start: int, end: int, floor: int, ceiling: int) -> Tuple[int, int]:
    postal_match = _POSTAL_CODE_SUFFIX_RE.search(text[floor:start])
    if postal_match:
        return floor + postal_match.start(), end

    prefix_window = text[floor:start]
    street_match = _STREET_PREFIX_RE.search(prefix_window)
    if street_match or _STREET_PREFIX_START_RE.match(text[start:end]):
        new_start = floor + street_match.start() if street_match else start
        number_match = _BUILDING_NUMBER_RE.match(text[end:ceiling])
        new_end = end + number_match.end() if number_match else end
        return new_start, new_end

    admin_match = _ADMIN_PREFIX_RE.search(prefix_window)
    if admin_match:
        return floor + admin_match.start(), end

    return start, end


def _retagged(token: PIIToken, start: int, end: int, text: str) -> PIIToken:
    if start == token.start and end == token.end:
        return token
    return PIIToken(
        type=token.type,
        original_value=text[start:end],
        token_str="",
        start=start,
        end=end,
    )
