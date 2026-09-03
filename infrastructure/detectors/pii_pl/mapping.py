from domain.enums.pii_type import PIIType
from typing import Dict

ENTITY_MAPPING: Dict[str, PIIType] = {
    "PERSON": PIIType.PERSON,
    "LOCATION": PIIType.LOCATION,
    "ORGANIZATION": PIIType.ORGANIZATION,
}
