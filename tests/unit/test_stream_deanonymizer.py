import pytest
from typing import AsyncIterator, Dict
from domain.entities.pii_token import PIIToken
from domain.enums.pii_type import PIIType
from application.services.stream_deanonymizer import StreamDeanonymizer

async def mock_stream(*chunks: str) -> AsyncIterator[str]:
    """
    Creates an async generator from a series of string chunks.

    Args:
        *chunks (str): Variable length string chunks to be yielded.

    Yields:
        str: A single chunk from the input strings.
    """
    for chunk in chunks:
        yield chunk

@pytest.fixture
def test_mapping() -> Dict[str, PIIToken]:
    """
    Provides a sample mapping of placeholder tokens to PIITokens for testing.

    Returns:
        Dict[str, PIIToken]: A dictionary mapping placeholder string to PIIToken objects.
    """
    return {
        "<PERSON1>": PIIToken(PIIType.PERSON, "Jan Kowalski", "<PERSON1>", 0, 12),
        "<LOCATION1>": PIIToken(PIIType.LOCATION, "Warszawa", "<LOCATION1>", 0, 8),
    }

@pytest.fixture
def deanonymizer(test_mapping: Dict[str, PIIToken]) -> StreamDeanonymizer:
    """
    Creates a StreamDeanonymizer instance with the test mapping.

    Args:
        test_mapping (Dict[str, PIIToken]): The mock token dictionary.

    Returns:
        StreamDeanonymizer: The service instance ready for testing.
    """
    return StreamDeanonymizer(test_mapping)

@pytest.mark.asyncio
async def test_process_no_tags(deanonymizer: StreamDeanonymizer):
    """
    Tests processing a stream without any PII placeholder tags.
    """
    stream = mock_stream("Hello ", "world", "!")
    results = [chunk async for chunk in deanonymizer.process(stream)]
    assert "".join(results) == "Hello world!"

@pytest.mark.asyncio
async def test_process_complete_tag_in_chunk(deanonymizer: StreamDeanonymizer):
    """
    Tests processing a stream where a full tag is contained within a single chunk.
    """
    stream = mock_stream("Hello ", "<PERSON1>", "!")
    results = [chunk async for chunk in deanonymizer.process(stream)]
    assert "".join(results) == "Hello Jan Kowalski!"

@pytest.mark.asyncio
async def test_process_split_tag(deanonymizer: StreamDeanonymizer):
    """
    Tests processing a stream where a tag spans across multiple chunks.
    """
    stream = mock_stream("Hello <PE", "RSON", "1>!")
    results = [chunk async for chunk in deanonymizer.process(stream)]
    assert "".join(results) == "Hello Jan Kowalski!"

@pytest.mark.asyncio
async def test_process_unknown_tag(deanonymizer: StreamDeanonymizer):
    """
    Tests processing a stream containing an unrecognized tag format.
    """
    stream = mock_stream("Hello <UNKNOWN>!")
    results = [chunk async for chunk in deanonymizer.process(stream)]
    assert "".join(results) == "Hello <UNKNOWN>!"

@pytest.mark.asyncio
async def test_process_malformed_bracket(deanonymizer: StreamDeanonymizer):
    """
    Tests processing when a new '<' is encountered before closing the previous tag.
    """
    stream = mock_stream("Hello <bad<PERSON1>!")
    results = [chunk async for chunk in deanonymizer.process(stream)]
    assert "".join(results) == "Hello <badJan Kowalski!"

@pytest.mark.asyncio
async def test_process_incomplete_tag_at_end(deanonymizer: StreamDeanonymizer):
    """
    Tests processing when the stream ends with an unclosed tag.
    """
    stream = mock_stream("Hello <PERSO")
    results = [chunk async for chunk in deanonymizer.process(stream)]
    assert "".join(results) == "Hello <PERSO"

@pytest.mark.asyncio
async def test_process_empty_chunks(deanonymizer: StreamDeanonymizer):
    """
    Tests processing a stream that occasionally produces empty chunks.
    """
    stream = mock_stream("Hello ", "", "<PERSON1>", "", "!")
    results = [chunk async for chunk in deanonymizer.process(stream)]
    assert "".join(results) == "Hello Jan Kowalski!"

@pytest.mark.asyncio
async def test_process_multiple_tags(deanonymizer: StreamDeanonymizer):
    """
    Tests processing a stream that contains multiple distinct tags.
    """
    stream = mock_stream("<PERSON1>", " is from ", "<LOCATION1>", ".")
    results = [chunk async for chunk in deanonymizer.process(stream)]
    assert "".join(results) == "Jan Kowalski is from Warszawa."
