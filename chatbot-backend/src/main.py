from contextlib import asynccontextmanager
from fastapi import FastAPI, Body, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from secrets import randbits
from typing import Annotated

from repository import chats_repo

from models.ChatModel import ChatModel
from models.MsgModel import MsgModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    chats_repo.init_db()
    yield

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200"
]

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chats/new")
def new_chat(user_message: Annotated[str, Body(embed=True)]):
    chat_id = randbits(63)
    chats_repo.new_chat(chat_id, user_message)

    # Unimplemented
    return JSONResponse(content={"chat_id": chat_id, "system_message": None}, status_code=201)

@app.post("/chats/{chat_id}")
def add_msg(chat_id: int, msg: MsgModel):
    added_row = chats_repo.add_msg_to_chat(chat_id, msg.role, msg.text)

    # Unimplemented; the system needs to produce this
    if added_row == True: 
        return JSONResponse(content=MsgModel(epoch_seconds=None, role=1, text="").model_dump(mode="json"), status_code=201)
    else:
        return Response(status_code=404)

# Get all chat IDs
@app.get("/chats")
def get_chat_info():
    return chats_repo.fetch_all_chats()

# Get all messages stored within a chat
@app.get("/chats/{chat_id}", response_model=list[MsgModel])
def get_messages(chat_id: int):
    output = chats_repo.fetch_chat(chat_id)
    if len(output) == 0: return Response(status_code=404)
    else: return output

@app.delete("/chats/{chat_id}")
def delete_chat(chat_id: int):
    deleted = chats_repo.delete_chat(chat_id)
    if deleted == True: return Response(status_code=204)
    else: return Response(status_code=404)
