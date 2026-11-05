import os
import sqlite3

from pathlib import Path
from contextlib import closing

from models.MsgModel import MsgModel
from models.ChatModel import ChatModel

SCHEMA = """
CREATE TABLE IF NOT EXISTS chats (
    chat_id    INTEGER NOT NULL,
    seq_num    INTEGER NOT NULL,
    role       INTEGER NOT NULL CHECK (role IN (0, 1)), -- user or system
    created_at INTEGER NOT NULL DEFAULT (unixepoch()),
    msg        TEXT NOT NULL,

    PRIMARY KEY (chat_id, seq_num)
) WITHOUT ROWID;
"""

SELECT = """
    SELECT chat_id, role, msg
    FROM chats
    WHERE chat_id = ?
    ORDER BY seq_num;
"""

SELECT_CHATS = """
    SELECT msg
    FROM chats
    WHERE chat_id = ? AND seq_num = 0;
"""

INSERT = """
    INSERT INTO chats (chat_id, seq_num, role, msg)
    VALUES (?, (SELECT COALESCE(MAX(seq_num) + 1, 0) FROM CHATS WHERE chat_id = ?), ?, ?);
"""

DELETE = """
    DELETE FROM chats WHERE chat_id = ?;
"""

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = Path(os.environ.get("SPRINGCHAT_DB", str(PROJECT_ROOT / "db" / "springchat.db"))).expanduser().resolve()

def init_db() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute(SCHEMA)
        conn.commit()

def fetch_chat(chat_id: int) -> list[MsgModel]:
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        rows = conn.execute(SELECT, (chat_id,)).fetchall()
            
    return [MsgModel(chat_id=chat_id, role=role, text=msg) for chat_id, role, msg in rows]

def fetch_chat_info(chat_id: int) -> ChatModel:
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        row = conn.execute(SELECT_CHATS, (chat_id,)).fetchone()
            
    return ChatModel(first_msg=row[0])

def add_msg_to_chat(chat_id: int, role: int, msg: str) -> None:
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        with conn:
            conn.execute(INSERT, (chat_id, None, role, msg))

def delete_chat(chat_id: int) -> None:
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        with conn:
            conn.execute(DELETE, (chat_id,))
            conn.commit()