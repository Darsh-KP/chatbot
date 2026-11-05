from typing import Literal
from pydantic import BaseModel

class MsgModel(BaseModel):
    chat_id: int | None = None
    role: Literal[0, 1] # User (0), Role (1)
    text: str

