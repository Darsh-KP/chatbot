from pydantic import BaseModel

# The descriptions of a single chat, for use in the UI.
class ChatModel(BaseModel):
    first_msg: str