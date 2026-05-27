from pydantic import BaseModel
class ChatMessage(BaseModel):
    role: str
    content: str
class ChatRequest(BaseModel):
    messages: str
    history: list[ChatMessage] = []
    context: ChatContext
class ChatContext(BaseModel):
    page:str
    tickers:list[str]