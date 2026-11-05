from typing import Literal
from pydantic import BaseModel

class MsgModel(BaseModel):
    # If this value is null, then a new chat is created according
    # to the backend.
    chat_id: int | None = None
    
    # If this value is 0, then show it as being sent by the user. If it
    # is 1, then show it as being sent by the LLM.
    role: Literal[0, 1]
    
    # The literal message
    text: str

