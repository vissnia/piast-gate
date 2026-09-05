import logging
import re
from pathlib import Path
from typing import FrozenSet, List, Tuple

import ahocorasick

from api.config.config import settings
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.interfaces.pii_detector import PIIDetector
from domain.services.token_overlap import remove_overlapping_tokens

logger = logging.getLogger(__name__)

GIVEN_NAMES = "person/given_names"
SURNAMES = "person/surnames"
LOCALITIES = "location/localities"
ADMIN_UNITS = "location/admin_units"
STREETS = "location/streets"

_LIST_FILES = {
    GIVEN_NAMES: "person/given_names.txt",
    SURNAMES: "person/surnames.txt",
    LOCALITIES: "location/localities.txt",
    ADMIN_UNITS: "location/admin_units.txt",
    STREETS: "location/streets.txt",
}
_PERSON_LISTS = frozenset({GIVEN_NAMES, SURNAMES})

_STREET_TRIGGERS = frozenset({
    "ul", "ulica", "ulicy", "al", "aleja", "alei", "aleją",
    "pl", "plac", "placu", "os", "osiedle", "osiedlu",
    "rondo", "ronda", "skwer", "skweru", "bulwar", "bulwaru", "rynek", "rynku",
})

_ABBREVIATIONS = frozenset({
    "ul", "al", "pl", "os", "gen", "płk", "ppłk", "dr", "prof", "mgr", "inż",
    "św", "im", "nr", "godz", "tel", "ok", "tj", "np", "itp", "itd", "por",
})
_TRAILING_WORD_RE = re.compile(r"([^\W\d_]+)\.?\s*$", re.UNICODE)

_STOPWORDS = frozenset({
    "brat", "bór", "cel", "czeka", "dom", "droga", "dyrektor", "dzień", "dziś",
    "dąb", "góra", "jednak", "jesień", "las", "lato", "los", "mama", "miasto",
    "mur", "nagle", "oraz", "plac", "pole", "poranek", "potem", "przykład",
    "puch", "rak", "rodzina", "rok", "rynek", "róg", "sad", "sam", "syn", "tam",
    "tata", "teraz", "tutaj", "ulica", "wieczór", "wiosna", "więc", "zima", "łąka",
    "pan", "pani", "pana", "panu", "panią", "panie", "panowie", "państwo",
    "państwa", "panów",
})

_Hit = Tuple[int, int, FrozenSet[str]]


def _lower_keep_len(text: str) -> str:
    """Lower-case ``text`` without changing its length, so match offsets stay
    valid against the original (a few code points such as U+0130 otherwise
    lower to two characters and shift everything after them)."""
    lowered = text.lower()
    if len(lowered) == len(text):
        return lowered
    return "".join(c.lower() if len(c.lower()) == 1 else c for c in text)


def _is_sep(ch: str) -> bool:
    return not ch.isalnum() and ch != "_"


def _word_bounded(text: str, start: int, end: int) -> bool:
    left = start == 0 or _is_sep(text[start - 1])
    right = end == len(text) or _is_sep(text[end])
    return left and right


def _sentence_initial(text: str, i: int) -> bool:
    """True if position ``i`` opens the text or a sentence, where an upper-case
    initial is no evidence of a name. A "." that closes a known abbreviation
    ("ul.", "dr.", ...) does not count as a sentence break."""
    j = i - 1
    while j >= 0 and text[j] in " \t":
        j -= 1
    if j < 0:
        return True
    if text[j] in "!?:\n\r•":
        return True
    if text[j] != ".":
        return False
    k = j - 1
    while k >= 0 and text[k].isalpha():
        k -= 1
    return text[k + 1:j].lower() not in _ABBREVIATIONS


def _has_street_trigger(lowered: str, start: int) -> bool:
    match = _TRAILING_WORD_RE.search(lowered, 0, start)
    return bool(match) and match.group(1) in _STREET_TRIGGERS


class GazetteerDetector(PIIDetector):
    """
    Dictionary PII pass that runs after the NER model: an Aho-Corasick sweep
    over the GUS gazetteers (``gazetteers/data`` by default) for nominative
    person and location names.

    Only nominative forms are matched, so recall on inflected mentions is
    essentially zero; this layer catches plain nominative mentions and rare
    names the NER model misses, it does not replace it.

    Every hit must be a whole word, start upper-case in the source text, and not
    be a common-word stop term. A hit is then routed, in order:

      * street list + an "ul."/"al."/... trigger in front  -> LOCATION
      * administrative-unit list (voivodeship/county/city)  -> LOCATION
      * given-/surname list -> person pass: hits adjacent through spaces or
        hyphens are chained; a chain is kept if it spans >= 2 tokens or holds a
        surname that is not also a given name; a lone or sentence-initial one is
        dropped
      * locality list, not sentence-initial -> LOCATION
    """

    def __init__(self) -> None:
        self.data_dir = Path(settings.gazetteer_data_dir)
        self._automaton = self._build_automaton()

    def _build_automaton(self) -> ahocorasick.Automaton:
        term_kinds: dict[str, set] = {}
        for kind, filename in _LIST_FILES.items():
            path = self.data_dir / filename
            try:
                with path.open(encoding="utf-8") as fh:
                    for line in fh:
                        term = line.rstrip("\n")
                        if term:
                            term_kinds.setdefault(term, set()).add(kind)
            except OSError as e:
                logger.error("Failed to load gazetteer list %s: %s", path, e)
                raise

        interned: dict = {}
        automaton = ahocorasick.Automaton()
        for term, kinds in term_kinds.items():
            frozen = frozenset(kinds)
            frozen = interned.setdefault(frozen, frozen)
            automaton.add_word(term, (frozen, len(term)))
        automaton.make_automaton()
        logger.info(
            "Loaded gazetteer automaton (%d terms) from %s",
            len(automaton), self.data_dir,
        )
        return automaton

    def detect(self, text: str) -> List[PIIToken]:
        if not text:
            return []

        lowered = _lower_keep_len(text)

        hits: List[_Hit] = []
        for end_idx, (kinds, term_len) in self._automaton.iter(lowered):
            end = end_idx + 1
            start = end - term_len
            if not _word_bounded(lowered, start, end):
                continue
            if not text[start].isupper():
                continue
            if lowered[start:end] in _STOPWORDS:
                continue
            hits.append((start, end, kinds))

        if not hits:
            return []

        hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))
        deduped: List[_Hit] = []
        last_end = -1
        for hit in hits:
            if hit[0] >= last_end:
                deduped.append(hit)
                last_end = hit[1]

        spans: List[Tuple[int, int, PIIType]] = []
        name_hits: List[_Hit] = []
        for start, end, kinds in deduped:
            if STREETS in kinds and _has_street_trigger(lowered, start):
                spans.append((start, end, PIIType.LOCATION))
            elif ADMIN_UNITS in kinds:
                spans.append((start, end, PIIType.LOCATION))
            elif kinds & _PERSON_LISTS:
                name_hits.append((start, end, kinds))
            elif (
                LOCALITIES in kinds
                and not _sentence_initial(text, start)
                and not text[start:end].isupper()
            ):
                spans.append((start, end, PIIType.LOCATION))

        spans += self._person_spans(name_hits, lowered, text)

        tokens = [
            PIIToken(
                type=pii_type,
                original_value=text[start:end],
                token_str="",
                start=start,
                end=end,
            )
            for start, end, pii_type in spans
        ]
        return remove_overlapping_tokens(tokens)

    def _person_spans(self, name_hits: List[_Hit], lowered: str, text: str):
        spans: List[Tuple[int, int, PIIType]] = []
        i = 0
        while i < len(name_hits):
            start, end, _ = name_hits[i]
            chain = [name_hits[i]]
            while i + 1 < len(name_hits):
                gap = lowered[end:name_hits[i + 1][0]]
                if gap and all(c in " -" for c in gap):
                    i += 1
                    end = name_hits[i][1]
                    chain.append(name_hits[i])
                else:
                    break
            i += 1

            if len(chain) < 2:
                pure_surname = any(
                    SURNAMES in kinds and GIVEN_NAMES not in kinds
                    for _, _, kinds in chain
                )
                if not pure_surname or _sentence_initial(text, start):
                    continue
                if text[start:end].isupper():
                    continue
            spans.append((start, end, PIIType.PERSON))
        return spans
