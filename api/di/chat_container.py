from api.di.detector_container import (
    get_spacy_detector,
    get_email_detector,
    get_phone_detector,
    get_pesel_detector,
    get_bank_account_detector,
)
from infrastructure.detectors.phone_detector import PhoneDetector
from infrastructure.detectors.email_detector import EmailDetector
from infrastructure.detectors.pesel_detector import PeselDetector
from infrastructure.detectors.bank_account_detector import BankAccountDetector
from infrastructure.detectors.spacy import SpacyPIIDetector
from functools import lru_cache
from typing import List
from fastapi import Depends
from infrastructure.factories.llm_factory import create_llm_provider
from domain.services.anonymizer_service import AnonymizerService
from domain.interfaces.pii_detector import PIIDetector
from application.use_cases.chat_use_case import ChatUseCase
from application.use_cases.anonymize_use_case import AnonymizeUseCase
from domain.interfaces.llm_provider import LLMProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    """
    Returns a cached instance of the LLM provider.
    """
    return create_llm_provider()

def get_anonymizer_service(
    spacy_detector: SpacyPIIDetector = Depends(get_spacy_detector),
    email_detector: EmailDetector = Depends(get_email_detector),
    bank_account_detector: BankAccountDetector = Depends(get_bank_account_detector),
    pesel_detector: PeselDetector = Depends(get_pesel_detector),
    phone_detector: PhoneDetector = Depends(get_phone_detector),
) -> AnonymizerService:
    """
    Dependency provider for AnonymizerService.
    Combines all configured PII detectors.
    """
    detectors: List[PIIDetector] = [
        spacy_detector,
        email_detector,
        bank_account_detector,
        pesel_detector,
        phone_detector,
    ]
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
