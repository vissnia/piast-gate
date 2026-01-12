from functools import lru_cache
from typing import List

from fastapi import Depends
from infrastructure.detectors.spacy import SpacyPIIDetector
from infrastructure.detectors.regex_detector import RegexPIIDetector
from infrastructure.llm.llm_factory import create_llm_provider
from domain.services.anonymizer_service import AnonymizerService
from domain.interfaces.pii_detector import PIIDetector
from application.use_cases.chat_use_case import ChatUseCase
from application.use_cases.anonymize_use_case import AnonymizeUseCase
from domain.interfaces.llm_provider import LLMProvider

@lru_cache
def get_spacy_detector() -> SpacyPIIDetector:
    """
    Returns a cached instance of SpacyPIIDetector to avoid reloading the model.
    """
    return SpacyPIIDetector()

@lru_cache
def get_regex_detector() -> RegexPIIDetector:
    """
    Returns a cached instance of RegexPIIDetector.
    """
    return RegexPIIDetector()

@lru_cache
def get_llm_provider() -> LLMProvider:
    """
    Returns a cached instance of the LLM provider.
    """
    return create_llm_provider()

def get_anonymizer_service(
    spacy_detector: SpacyPIIDetector = Depends(get_spacy_detector),
    regex_detector: RegexPIIDetector = Depends(get_regex_detector),
) -> AnonymizerService:
    """
    Dependency provider for AnonymizerService.
    Combines all configured PII detectors.
    """
    detectors: List[PIIDetector] = [spacy_detector, regex_detector]
    return AnonymizerService(detectors)

def get_chat_use_case(
    anonymizer: AnonymizerService = Depends(get_anonymizer_service),
    llm: LLMProvider = Depends(get_llm_provider),
) -> ChatUseCase:
    """
    Dependency provider for ChatUseCase.
    Wraps the application logic with required services.
    """
    return ChatUseCase(anonymizer, llm)

def get_anonymize_use_case(
    anonymizer: AnonymizerService = Depends(get_anonymizer_service),
) -> AnonymizeUseCase:
    """
    Dependency provider for AnonymizeUseCase.
    """
    return AnonymizeUseCase(anonymizer)
