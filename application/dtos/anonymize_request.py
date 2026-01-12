from pydantic import BaseModel

class AnonymizeRequest(BaseModel):
    text: str
