from functools import lru_cache
from infrastructure.detectors.spacy import SpacyPIIDetector
from infrastructure.detectors.email_detector import EmailDetector
from infrastructure.detectors.phone_detector import PhoneDetector
from infrastructure.detectors.pesel_detector import PeselDetector
from infrastructure.detectors.bank_account_detector import BankAccountDetector

@lru_cache
def get_spacy_detector() -> SpacyPIIDetector:
    """
    Returns a cached instance of SpacyPIIDetector to avoid reloading the model.
    """
    return SpacyPIIDetector()

@lru_cache
def get_email_detector() -> EmailDetector:
    """
    Returns a cached instance of EmailDetector.
    """
    return EmailDetector()

@lru_cache
def get_phone_detector() -> PhoneDetector:
    """
    Returns a cached instance of PhoneDetector.
    """
    return PhoneDetector()

@lru_cache
def get_pesel_detector() -> PeselDetector:
    """
    Returns a cached instance of PeselDetector.
    """
    return PeselDetector()

@lru_cache
def get_bank_account_detector() -> BankAccountDetector:
    """
    Returns a cached instance of BankAccountDetector.
    """
    return BankAccountDetector()
