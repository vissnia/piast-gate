"""Build Aho-Corasick-ready gazetteer term lists from the raw GUS source files.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "data"

MIN_LEN = 3
_REJECT_CHARS = set(".()/")
_WS_RE = re.compile(r"\s+")

csv.field_size_limit(min(sys.maxsize, 2**31 - 1))


def _normalize(raw: str) -> str | None:
    """Canonical form of a single gazetteer term, or None if it should be dropped."""
    term = unicodedata.normalize("NFC", raw).strip()
    term = _WS_RE.sub(" ", term).lower()
    if len(term) < MIN_LEN:
        return None
    if any(ch in _REJECT_CHARS for ch in term):
        return None
    if not any(ch.isalpha() for ch in term):
        return None
    return term


def _read_csv(path: Path, delimiter: str):
    with path.open(encoding="utf-8-sig", newline="") as fh:
        yield from csv.DictReader(fh, delimiter=delimiter)


def _one(pattern: str) -> Path:
    matches = sorted(ROOT.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"no source file matches {pattern!r} under {ROOT}")
    return matches[-1]


def _collect_from(paths, delimiter, row_to_term, meta, group, kind, keep=None) -> set[str]:
    """Normalize one term per row across ``paths`` into a single deduped set.

    ``keep``, if given, is a predicate on the raw row; rows it rejects are
    skipped before normalization (still counted in ``rows``)."""
    terms: set[str] = set()
    for path in paths:
        rows = 0
        for row in _read_csv(path, delimiter):
            rows += 1
            if keep is not None and not keep(row):
                continue
            term = _normalize(row_to_term(row))
            if term:
                terms.add(term)
        meta["sources"].append(
            {"group": group, "kind": kind, "file": path.name, "rows": rows}
        )
    return terms


def collect(meta: dict) -> dict[str, set[str]]:
    return {
        "person/given_names": _collect_from(
            sorted(ROOT.glob("person/10_-_Wykaz_imion_*.csv")),
            ",", lambda r: r["IMIĘ_DRUGIE"], meta, "person", "given_names",
        ),
        "person/surnames": _collect_from(
            sorted(ROOT.glob("person/2_-_nazwiska_*.csv")),
            ",", lambda r: r["Nazwisko aktualne"], meta, "person", "surnames",
        ),
        "location/localities": _collect_from(
            [_one("location/SIMC_Adresowy_*.csv")],
            ";", lambda r: r["NAZWA"], meta, "location", "localities",
            keep=lambda r: r["RM"] != "00",
        ),
        "location/admin_units": _collect_from(
            [_one("location/TERC_Adresowy_*.csv")],
            ";", lambda r: r["NAZWA"], meta, "location", "admin_units",
        ),
        "location/streets": _collect_from(
            [_one("location/ULIC_Adresowy_*.csv")],
            ";", lambda r: f"{r['NAZWA_2']} {r['NAZWA_1']}".strip(),
            meta, "location", "streets",
        ),
    }


def main() -> None:
    meta: dict = {"generated_on": date.today().isoformat(), "min_len": MIN_LEN, "sources": []}
    lists = collect(meta)

    meta["outputs"] = {}
    for rel, terms in lists.items():
        path = OUT_DIR / f"{rel}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        ordered = sorted(terms)
        path.write_text("\n".join(ordered) + "\n", encoding="utf-8")
        meta["outputs"][rel + ".txt"] = len(ordered)

    (OUT_DIR / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    for name, count in meta["outputs"].items():
        print(f"{name}: {count} terms")


if __name__ == "__main__":
    main()
