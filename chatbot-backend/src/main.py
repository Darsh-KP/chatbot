from contextlib import asynccontextmanager
from fastapi import FastAPI, Body, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from secrets import randbits
from typing import Annotated

from repository import chats_repo

from models.ChatModel import ChatModel
from models.ChatListModel import ChatListModel
from models.MsgModel import MsgModel
from services.vectordb_service import ingest_adoc_directory
from models.MsgListModel import MsgListModel

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

@app.post("/ingest")
def ingest_data():
    chunks_ingested = ingest_adoc_directory("spring-docs")
    return {"collection": "spring-docs", "chunks_ingested": chunks_ingested}

@app.post("/chats/new")
def new_chat(user_message: Annotated[str, Body(embed=True)]):
    chat_id = randbits(32)
    chats_repo.new_chat(chat_id, user_message)

    # Unimplemented
    return JSONResponse(content={"chat_id": chat_id, "system_message": None, "epoch_seconds": 0, "seq_num": 1}, status_code=201)

@app.post("/chats/{chat_id}")
def add_msg(chat_id: int, user_message: Annotated[str, Body(embed=True)]):
    added_row = chats_repo.add_msg_to_chat(chat_id, 0, user_message)

    if added_row == True: 
        # Unimplemented; the system needs to produce this
        return JSONResponse(content=MsgModel(role=1, message="", epoch_seconds=0, seq_num=-1).model_dump(mode="json"), status_code=201)
    else:
        return Response(status_code=404)

# Get all chats, including titles
@app.get("/chats")
def get_chat_info():
    return ChatListModel(chats=chats_repo.fetch_all_chats())

# Get all messages stored within a chat
@app.get("/chats/{chat_id}")
def get_messages(chat_id: int):
    output = chats_repo.fetch_chat(chat_id)
    if len(output) == 0: return Response(status_code=404)
    else: return MsgListModel(messages=output)

@app.delete("/chats/{chat_id}")
def delete_chat(chat_id: int):
    deleted = chats_repo.delete_chat(chat_id)
    if deleted == True: return Response(status_code=204)
    else: return Response(status_code=404)
