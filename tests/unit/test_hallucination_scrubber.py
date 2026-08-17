import pytest
from typing import AsyncIterator
from application.services.hallucination_scrubber import HallucinationScrubber
from domain.services.anonymizer_service import AnonymizerService
from infrastructure.detectors.pesel_detector import PeselDetector
from infrastructure.detectors.email_detector import EmailDetector


async def mock_stream(*chunks: str) -> AsyncIterator[str]:
    for chunk in chunks:
        yield chunk


@pytest.fixture
def guard() -> AnonymizerService:
    return AnonymizerService([PeselDetector(), EmailDetector()])


@pytest.fixture
def scrubber(guard: AnonymizerService) -> HallucinationScrubber:
    return HallucinationScrubber(guard)


@pytest.mark.asyncio
async def test_redacts_hallucinated_pesel_word(scrubber: HallucinationScrubber):
    stream = mock_stream("Twój PESEL to 90010112349, dziękuję.")
    results = [chunk async for chunk in scrubber.process(stream)]
    assert "".join(results) == "Twój PESEL to [REDACTED:PESEL], dziękuję."


@pytest.mark.asyncio
async def test_redacts_pesel_split_across_chunks(scrubber: HallucinationScrubber):
    stream = mock_stream("Numer: 900101", "12349 potwierdzony.")
    results = [chunk async for chunk in scrubber.process(stream)]
    assert "".join(results) == "Numer: [REDACTED:PESEL] potwierdzony."


@pytest.mark.asyncio
async def test_leaves_placeholder_tags_untouched(scrubber: HallucinationScrubber):
    stream = mock_stream("Cześć <PERSON1>, Twój PESEL to <PESEL1>.")
    results = [chunk async for chunk in scrubber.process(stream)]
    assert "".join(results) == "Cześć <PERSON1>, Twój PESEL to <PESEL1>."


@pytest.mark.asyncio
async def test_leaves_plain_text_untouched(scrubber: HallucinationScrubber):
    stream = mock_stream("To jest ", "zwykła odpowiedź ", "bez PII.")
    results = [chunk async for chunk in scrubber.process(stream)]
    assert "".join(results) == "To jest zwykła odpowiedź bez PII."


@pytest.mark.asyncio
async def test_redacts_final_unterminated_word(scrubber: HallucinationScrubber):
    stream = mock_stream("Kontakt: fake@example.com")
    results = [chunk async for chunk in scrubber.process(stream)]
    assert "".join(results) == "Kontakt: [REDACTED:EMAIL]"
