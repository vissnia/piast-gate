from domain.enums.pii_type import PIIType
from typing import Dict

ENTITY_MAPPING: Dict[str, PIIType] = {
    "persName": PIIType.PERSON,
    "person": PIIType.PERSON,
    "PERSON": PIIType.PERSON,
    
    "orgName": PIIType.ORGANIZATION,
    "org": PIIType.ORGANIZATION,
    "ORG": PIIType.ORGANIZATION,
    
    "placeName": PIIType.LOCATION,
    "geogName": PIIType.LOCATION,
    "LOC": PIIType.LOCATION,
    "GPE": PIIType.LOCATION,
    "FAC": PIIType.LOCATION,
    "date": PIIType.DATE,
}
