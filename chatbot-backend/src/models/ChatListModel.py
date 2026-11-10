from pydantic import BaseModel
from models.ChatModel import ChatModel

# Wrapper class
class ChatListModel(BaseModel):
    chats: list[ChatModel]