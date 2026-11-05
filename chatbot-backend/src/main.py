from fastapi import FastAPI
from secrets import randbits

import chats_repo

from ChatModel import ChatModel
from MsgModel import MsgModel

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

@app.get("/api/chats/{user_id}", response_model=list[ChatModel])
def get_chats():
    return chats_repo.fetch_chats_by_user(int(user_id))

@app.get("/api/chats/{chat_id}/messages", response_model=list[MsgModel])
def get_messages():
    return chats_repo.get_messages(int(chat_id))
