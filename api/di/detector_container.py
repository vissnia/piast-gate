from functools import lru_cache
from infrastructure.detectors.pii_pl import PiiPlDetector
from infrastructure.detectors.email_detector import EmailDetector
from infrastructure.detectors.phone_detector import PhoneDetector
from infrastructure.detectors.pesel_detector import PeselDetector
from infrastructure.detectors.bank_account_detector import BankAccountDetector
from infrastructure.detectors.date_detector import DateDetector
from infrastructure.detectors.nip_detector import NipDetector
from infrastructure.detectors.regon_detector import RegonDetector

@lru_cache
def get_pii_pl_detector() -> PiiPlDetector:
    return PiiPlDetector()

@lru_cache
def get_email_detector() -> EmailDetector:
    return EmailDetector()

@lru_cache
def get_phone_detector() -> PhoneDetector:
    return PhoneDetector()

@lru_cache
def get_pesel_detector() -> PeselDetector:
    return PeselDetector()

@lru_cache
def get_bank_account_detector() -> BankAccountDetector:
    return BankAccountDetector()

@lru_cache
def get_date_detector() -> DateDetector:
    return DateDetector()

@lru_cache
def get_nip_detector() -> NipDetector:
    return NipDetector()

@lru_cache
def get_regon_detector() -> RegonDetector:
    return RegonDetector()
