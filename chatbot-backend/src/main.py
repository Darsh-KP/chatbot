from contextlib import asynccontextmanager
from fastapi import FastAPI, Body, Response
from fastapi.responses import JSONResponse
from secrets import randbits
from typing import Annotated

from repository import chats_repo
import asyncio
import logging

from fastapi import Body, FastAPI, HTTPException, Path, Response
from pydantic import StringConstraints
from services.rag_service import answer_question
from models.ChatModel import ChatModel
from models.MsgModel import MsgModel

LOGGER = logging.getLogger(__name__)

USER_ROLE, SYSTEM_ROLE = 0, 1  
SQLITE_MAX_INT = 2**63 - 1

@asynccontextmanager
async def lifespan(app: FastAPI):
    chats_repo.init_db()
    yield


UserMessage = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1), Body(embed=True)]
app = FastAPI(lifespan=lifespan)

async def _answer(question: str) -> str:
    try:
        return (await answer_question(question))["answer"]
    except Exception:
        LOGGER.exception("Failed to answer question")  # real cause goes to the server log only
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


async def _save_new_chat(chat_id: int, user_text: str, system_text: str) -> None:
    msgs = [(USER_ROLE, user_text), (SYSTEM_ROLE, system_text)]
    try:
        # One transaction: title + both messages are stored, or nothing is.
        await asyncio.to_thread(chats_repo.create_chat, chat_id, msgs)
    except Exception:
        LOGGER.exception("Failed to save new chat")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")


async def _save_exchange(chat_id: int, user_text: str, system_text: str) -> None:
    msgs = [(USER_ROLE, user_text), (SYSTEM_ROLE, system_text)]
    try:
        saved = await asyncio.to_thread(chats_repo.add_msgs_to_chat, chat_id, msgs)
    except Exception:
        LOGGER.exception("Failed to save messages")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
    if not saved:
        raise HTTPException(status_code=404, detail="The chat does not exist")


@app.post("/chats/new", status_code=201)
async def new_chat(user_message: UserMessage):
    system_message = await _answer(user_message)
    chat_id = randbits(52) # 52-bit ID to avoid JavaScript integer precision issues
    await _save_new_chat(chat_id, user_message, system_message)
    return {"chat_id": chat_id, "system_message": system_message}


@app.post("/chats/{chat_id}", status_code=201)
async def add_msg(chat_id: Annotated[int, Path(ge=0, le=SQLITE_MAX_INT)], user_message: UserMessage):
    if not await asyncio.to_thread(chats_repo.chat_exists, chat_id):
        raise HTTPException(status_code=404, detail="The chat does not exist")
    system_message = await _answer(user_message)
    await _save_exchange(chat_id, user_message, system_message)
    return {"system_message": system_message}

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
