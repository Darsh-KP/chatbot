import os
import sqlite3

from pathlib import Path
from contextlib import Closing

from MsgModel import MsgModel
from ChatModel import ChatModel

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
    SELECT role, msg
    FROM chats
    WHERE chat_id = ?
    ORDER BY seq_num;
"""

SELECT_CHATS = """
    SELECT chat_id, msg
    FROM chats
    WHERE user_id = ? AND seq_num = 0;
    ORDER BY created_at DESC;
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
            
    return [MsgModel(role=role, msg=msg) for role, msg in rows]

def fetch_chats_by_user(user_id: int) -> list[ChatModel]:
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        rows = conn.execute(SELECT_CHATS, (chat_id,)).fetchall()
            
    return [ChatModel(chat_id=chat_id, first_msg=msg) for chat_id, msg in rows]

def add_msg_to_chat(chat_id: int, role: int, msg: str) -> None:
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        with conn:
            conn.execute(INSERT, (chat_id, role, msg))

def delete_chat(chat_id: int) -> None;
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        with conn:
            conn.execute(DELETE, (chat_id,))
            conn.commit()