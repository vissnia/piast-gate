from domain.enums.pii_type import PIIType
from typing import Dict

ENTITY_MAPPING: Dict[str, PIIType] = {
    "PERSON": PIIType.PERSON,
    "PERSON_F": PIIType.PERSON,
    "PERSON_L": PIIType.PERSON,
    "STREET": PIIType.LOCATION,
    "CITY": PIIType.LOCATION,
    "ORG": PIIType.ORGANIZATION
}
