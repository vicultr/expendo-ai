from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class NLRequest(BaseModel):
    question: str