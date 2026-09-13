from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from domain.services.location_merger import merge_location_spans


def _loc(text, needle, n=1):
    start = text.find(needle)
    for _ in range(n - 1):
        start = text.find(needle, start + 1)
    end = start + len(needle)
    return PIIToken(type=PIIType.LOCATION, original_value=needle, token_str="", start=start, end=end)


class TestMergeLocationSpans:
    def test_empty_tokens_returns_empty(self):
        assert merge_location_spans("anything", []) == []

    def test_no_location_tokens_passthrough(self):
        token = PIIToken(type=PIIType.EMAIL, original_value="a@b.com", token_str="", start=0, end=7)
        assert merge_location_spans("a@b.com", [token]) == [token]

    def test_street_number_postal_and_city_merge_into_one_span(self):
        text = "Adres zamieszkania: ul. Polna 3, 30-001 Kraków."
        tokens = [_loc(text, "Polna"), _loc(text, "Kraków")]

        result = merge_location_spans(text, tokens)

        assert len(result) == 1
        assert result[0].original_value == "ul. Polna 3, 30-001 Kraków"
        assert text[result[0].start:result[0].end] == result[0].original_value

    def test_reversed_order_postal_city_then_street(self):
        text = "Adres: 30-001 Kraków, ul. Polna 3."
        tokens = [_loc(text, "Kraków"), _loc(text, "Polna")]

        result = merge_location_spans(text, tokens)

        assert [t.original_value for t in result] == ["30-001 Kraków, ul. Polna 3"]

    def test_glued_no_spacing(self):
        text = "ul.Polna3,30-001Kraków to ciąg wklejony bez separacji."
        tokens = [_loc(text, "Polna"), _loc(text, "Kraków")]

        result = merge_location_spans(text, tokens)

        assert [t.original_value for t in result] == ["ul.Polna3,30-001Kraków"]

    def test_building_number_with_letter_and_apartment_variants(self):
        cases = [
            ("Adres: ul. Leśna 12A, 40-001 Katowice.", "ul. Leśna 12A, 40-001 Katowice"),
            ("Adres: ul. Polna 12/3, 30-001 Kraków.", "ul. Polna 12/3, 30-001 Kraków"),
            ("Adres: ul. Polna 12 m. 3, 30-001 Kraków.", "ul. Polna 12 m. 3, 30-001 Kraków"),
            ("Adres: ul. Polna 3, 30001 Kraków.", "ul. Polna 3, 30001 Kraków"),
        ]
        for text, expected in cases:
            street = text.split(",")[0].split(". ", 1)[1].split(" ")[0]
            city = expected.rsplit(" ", 1)[1]
            tokens = [_loc(text, street), _loc(text, city)]

            result = merge_location_spans(text, tokens)

            assert [t.original_value for t in result] == [expected], text

    def test_building_number_grows_even_when_prefix_is_already_inside_the_base_span(self):
        """Regression: the upstream NER model sometimes already includes the
        "al."/"ul." prefix in its own span (nothing left for this module to
        grow backward), which must not disable the forward building-number
        growth that follows it."""
        text = "Biuro znajduje się przy al. Niepodległości 12, 02-653 Warszawa."
        tokens = [_loc(text, "al. Niepodległości"), _loc(text, "Warszawa")]

        result = merge_location_spans(text, tokens)

        assert [t.original_value for t in result] == ["al. Niepodległości 12, 02-653 Warszawa"]

    def test_all_caps_address(self):
        text = "W formularzu wpisano: UL. POLNA 3, 30-001 KRAKÓW, zgodnie z danymi."
        tokens = [_loc(text, "POLNA"), _loc(text, "KRAKÓW")]

        result = merge_location_spans(text, tokens)

        assert [t.original_value for t in result] == ["UL. POLNA 3, 30-001 KRAKÓW"]

    def test_postal_code_and_city_without_street(self):
        text = "Dokumenty należy przesłać na adres: 30-001 Kraków."
        tokens = [_loc(text, "Kraków")]

        result = merge_location_spans(text, tokens)

        assert [t.original_value for t in result] == ["30-001 Kraków"]

    def test_admin_prefix_alone(self):
        text = "Inwestycja realizowana jest na terenie gminy Chełmiec."
        tokens = [_loc(text, "Chełmiec")]

        result = merge_location_spans(text, tokens)

        assert [t.original_value for t in result] == ["gminy Chełmiec"]

    def test_three_level_administrative_hierarchy_chains_into_one_span(self):
        text = (
            "Nieruchomość położona jest w miejscowości Marcinkowice, "
            "powiat gorlicki, województwo małopolskie."
        )
        tokens = [_loc(text, "Marcinkowice"), _loc(text, "gorlicki"), _loc(text, "małopolskie")]

        result = merge_location_spans(text, tokens)

        assert [t.original_value for t in result] == [
            "miejscowości Marcinkowice, powiat gorlicki, województwo małopolskie"
        ]

    def test_bare_w_glue_merges_district_within_city(self):
        text = "Biuro znajduje się na Mokotowie w Warszawie."
        tokens = [_loc(text, "Mokotowie"), _loc(text, "Warszawie")]

        result = merge_location_spans(text, tokens)

        assert [t.original_value for t in result] == ["Mokotowie w Warszawie"]

    def test_unrelated_locations_separated_by_prose_are_not_merged(self):
        text = "Delegacja obejmuje wyjazd do Krakowa oraz do Poznania w tym samym tygodniu."
        tokens = [_loc(text, "Krakowa"), _loc(text, "Poznania")]

        result = merge_location_spans(text, tokens)

        assert [t.original_value for t in result] == ["Krakowa", "Poznania"]

    def test_comma_with_repeated_preposition_is_not_merged(self):
        text = "Nieruchomość znajduje się w województwie małopolskim, w powiecie nowosądeckim."
        tokens = [_loc(text, "małopolskim"), _loc(text, "nowosądeckim")]

        result = merge_location_spans(text, tokens)

        assert len(result) == 2

    def test_intervening_non_location_token_blocks_merge(self):
        text = "Kraków, Jan Kowalski, Warszawa"
        location_a = _loc(text, "Kraków")
        person = PIIToken(
            type=PIIType.PERSON, original_value="Jan Kowalski", token_str="",
            start=text.index("Jan"), end=text.index("Jan") + len("Jan Kowalski"),
        )
        location_b = _loc(text, "Warszawa")

        result = merge_location_spans(text, [location_a, person, location_b])

        assert [t.original_value for t in result] == ["Kraków", "Jan Kowalski", "Warszawa"]

    def test_multiple_addresses_stay_separate(self):
        text = (
            "Adres zamieszkania: ul. Kwiatowa 5, 30-002 Kraków. "
            "Adres do korespondencji: ul. Skrzynkowa 8, 31-000 Kraków."
        )
        tokens = [
            _loc(text, "Kwiatowa"), _loc(text, "Kraków", n=1),
            _loc(text, "Skrzynkowa"), _loc(text, "Kraków", n=2),
        ]

        result = merge_location_spans(text, tokens)

        assert [t.original_value for t in result] == [
            "ul. Kwiatowa 5, 30-002 Kraków",
            "ul. Skrzynkowa 8, 31-000 Kraków",
        ]

    def test_growth_never_overlaps_a_neighboring_token(self):
        text = "ul. Polna 3, 30-001 Kraków"
        tokens = [_loc(text, "Polna"), _loc(text, "Kraków")]

        result = merge_location_spans(text, tokens)

        for a, b in zip(result, result[1:]):
            assert a.end <= b.start
