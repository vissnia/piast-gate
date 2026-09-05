# Gazetteers

Deterministic PII term lists used as a fast pass **after** the spaCy NER
model (`infrastructure/detectors/pii_pl`). Consumed by
`infrastructure/detectors/gazetteer`, which loads all five lists into one
Aho-Corasick automaton. Split by sub-type so that detector can weigh them
differently (a lone given name is dropped, a street needs an "ul." trigger,
an administrative unit is trusted over a same-spelled surname, ...).

## Layout

```
gazetteers/
  person/               raw GUS registers (given names + surnames, PESEL, living)
  location/             raw GUS registers (SIMC localities, TERC units, ULIC streets)
  build_gazetteers.py   regenerates data/ from the raw registers (stdlib only)
  data/
    person/
      given_names.txt    given names (PESEL register, living persons)
      surnames.txt       current surnames
    location/
      localities.txt     village / town / city names (SIMC)
      admin_units.txt    voivodeship / county / commune names (TERC)
      streets.txt        street names, no "ul." / "pl." / "rondo" prefix (ULIC)
    meta.json            source files, raw row counts, output term counts
```

Regenerate after dropping in newer register files:

```
python gazetteers/build_gazetteers.py
```

## Term list format

- One term per line, UTF-8, `\n`, sorted, de-duplicated.
- **Lower-cased**, Unicode NFC, internal whitespace collapsed to single spaces.
- Category is the file path — no per-term metadata. `person/*` → `PIIType.PERSON`,
  `location/*` → `PIIType.LOCATION`.
- Terms shorter than 3 characters and abbreviation junk (`.`, `(`, `)`, `/`)
  are dropped at build time; see `MIN_LEN` in the build script.
- `localities.txt` excludes SIMC `RM="00"` ("część miejscowości") — 35k mostly
  common-word names that are rarely referred to as a place.
