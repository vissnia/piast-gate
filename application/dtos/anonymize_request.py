from pydantic import BaseModel, Field

MAX_TEXT_LENGTH = 20_000

class AnonymizeRequest(BaseModel):
    text: str = Field(..., max_length=MAX_TEXT_LENGTH)
