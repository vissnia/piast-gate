from api.di.detector_container import (
    get_pii_pl_detector,
    get_email_detector,
    get_phone_detector,
    get_pesel_detector,
    get_bank_account_detector,
    get_date_detector,
    get_nip_detector,
    get_regon_detector,
)
from infrastructure.detectors.phone_detector import PhoneDetector
from infrastructure.detectors.email_detector import EmailDetector
from infrastructure.detectors.pesel_detector import PeselDetector
from infrastructure.detectors.bank_account_detector import BankAccountDetector
from infrastructure.detectors.date_detector import DateDetector
from infrastructure.detectors.nip_detector import NipDetector
from infrastructure.detectors.regon_detector import RegonDetector
from infrastructure.detectors.pii_pl import PiiPlDetector
from functools import lru_cache
from typing import List
from fastapi import Depends
from infrastructure.factories.llm_factory import create_llm_provider
from domain.services.anonymizer_service import AnonymizerService
from domain.interfaces.pii_detector import PIIDetector
from application.use_cases.chat_use_case import ChatUseCase
from application.use_cases.anonymize_use_case import AnonymizeUseCase
from application.use_cases.stream_chat_use_case import StreamChatUseCase
from domain.interfaces.llm_provider import LLMProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    return create_llm_provider()

def get_anonymizer_service(
    pii_pl_detector: PiiPlDetector = Depends(get_pii_pl_detector),
    email_detector: EmailDetector = Depends(get_email_detector),
    bank_account_detector: BankAccountDetector = Depends(get_bank_account_detector),
    pesel_detector: PeselDetector = Depends(get_pesel_detector),
    phone_detector: PhoneDetector = Depends(get_phone_detector),
    date_detector: DateDetector = Depends(get_date_detector),
    nip_detector: NipDetector = Depends(get_nip_detector),
    regon_detector: RegonDetector = Depends(get_regon_detector),
) -> AnonymizerService:
    detectors: List[PIIDetector] = [
        pii_pl_detector,
        email_detector,
        bank_account_detector,
        pesel_detector,
        phone_detector,
        date_detector,
        nip_detector,
        regon_detector,
    ]
    return AnonymizerService(detectors)

_SLOW_DETECTOR_TYPES = (PiiPlDetector, DateDetector)

def get_hallucination_guard(
    anonymizer: AnonymizerService = Depends(get_anonymizer_service),
) -> AnonymizerService:
    """
    Scoped to fast, checksum-validated detectors only (no NER), to scrub
    hallucinated PII from streamed LLM output word-by-word without the
    latency of running the NER model per word.

    Derived from the full detector set rather than re-wired independently,
    so the "fast" subset can never drift from the detectors actually used
    for anonymization.
    """
    fast_detectors: List[PIIDetector] = [
        d for d in anonymizer.detectors if not isinstance(d, _SLOW_DETECTOR_TYPES)
    ]
    return AnonymizerService(fast_detectors)

def get_chat_use_case(
    anonymizer: AnonymizerService = Depends(get_anonymizer_service),
    llm: LLMProvider = Depends(get_llm_provider),
) -> ChatUseCase:
    return ChatUseCase(anonymizer, llm)

def get_stream_chat_use_case(
    anonymizer: AnonymizerService = Depends(get_anonymizer_service),
    llm: LLMProvider = Depends(get_llm_provider),
    hallucination_guard: AnonymizerService = Depends(get_hallucination_guard),
) -> StreamChatUseCase:
    return StreamChatUseCase(anonymizer, llm, hallucination_guard)

def get_anonymize_use_case(
    anonymizer: AnonymizerService = Depends(get_anonymizer_service),
) -> AnonymizeUseCase:
    return AnonymizeUseCase(anonymizer)
