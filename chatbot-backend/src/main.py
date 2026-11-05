from contextlib import asynccontextmanager
from fastapi import FastAPI
from secrets import randbits    

from repository import chats_repo

from models.ChatModel import ChatModel
from models.MsgModel import MsgModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    chats_repo.init_db()
    yield

app = FastAPI(lifespan=lifespan)

# If a new chat is being created, the frontend needs to keep track of 
# the chats assigned to the user by refreshing get_chats() and route
# to the new chat
@app.post("/api/send_msg")
def add_msg(msg: MsgModel):
    chat_id = msg.chat_id

    if msg.chat_id is None:
        chat_id = randbits(63)

    chats_repo.add_msg_to_chat(chat_id, msg.role, msg.text)

    return {"chat_id": chat_id}

# This should be called for all chats that the client saves
# in local storage.
@app.get("/api/chats/{chat_id}", response_model=ChatModel)
def get_chat_info(chat_id: int):
    return chats_repo.fetch_chat_info(chat_id)

# Get all messages stored within a chat
@app.get("/api/chats/{chat_id}/messages", response_model=list[MsgModel])
def get_messages(chat_id: int):
    return chats_repo.fetch_chat(chat_id)
