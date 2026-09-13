from functools import lru_cache
from infrastructure.detectors.pii_pl import BaseNerDetector, create_pii_ner_detector
from infrastructure.detectors.gazetteer import GazetteerDetector
from infrastructure.detectors.email_detector import EmailDetector
from infrastructure.detectors.phone_detector import PhoneDetector
from infrastructure.detectors.pesel_detector import PeselDetector
from infrastructure.detectors.bank_account_detector import BankAccountDetector
from infrastructure.detectors.nip_detector import NipDetector
from infrastructure.detectors.regon_detector import RegonDetector

@lru_cache
def get_pii_pl_detector() -> BaseNerDetector:
    return create_pii_ner_detector()

@lru_cache
def get_gazetteer_detector() -> GazetteerDetector:
    return GazetteerDetector()

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
def get_nip_detector() -> NipDetector:
    return NipDetector()

@lru_cache
def get_regon_detector() -> RegonDetector:
    return RegonDetector()
