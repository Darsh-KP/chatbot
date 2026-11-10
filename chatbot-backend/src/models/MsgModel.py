from typing import Literal
from pydantic import BaseModel

class MsgModel(BaseModel):
    # If this value is 0, then show it as being sent by the user. If it
    # is 1, then show it as being sent by the LLM.
    role: Literal[0, 1]
    
    # The literal message
    message: str

    # Seconds since 1970-01-01 00:00 UTC
    epoch_seconds: int | None = None

    # The index of the message in the chat
    seq_num: int

