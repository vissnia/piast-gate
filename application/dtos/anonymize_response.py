from pydantic import BaseModel

class AnonymizeResponse(BaseModel):
    anonymized_text: str
