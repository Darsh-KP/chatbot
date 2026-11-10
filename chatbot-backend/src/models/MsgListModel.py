from pydantic import BaseModel
from models.MsgModel import MsgModel

# Wrapper class for messages
class MsgListModel(BaseModel):
    messages: list[MsgModel]