from pydantic import BaseModel

# The descriptions of a single chat, for use in the UI.
class ChatModel(BaseModel):
    chat_id: int
    title: str | None