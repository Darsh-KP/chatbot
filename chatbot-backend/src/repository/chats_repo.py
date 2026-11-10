import os
import sqlite3

from pathlib import Path
from contextlib import closing

from models.MsgModel import MsgModel
from models.ChatModel import ChatModel

TITLES_SCHEMA = """
CREATE TABLE IF NOT EXISTS titles (
    chat_id INTEGER PRIMARY KEY,
    title   TEXT
);
"""

MESSAGES_SCHEMA = """
CREATE TABLE IF NOT EXISTS chats (
    chat_id    INTEGER NOT NULL,
    seq_num    INTEGER NOT NULL CHECK(seq_num >= 0),
    role       INTEGER NOT NULL CHECK (role IN (0, 1)), -- user or system
    created_at INTEGER NOT NULL DEFAULT (unixepoch()),
    msg        TEXT NOT NULL,

    PRIMARY KEY (chat_id, seq_num),
    FOREIGN KEY (chat_id) REFERENCES titles(chat_id) ON DELETE CASCADE
) WITHOUT ROWID;
"""

SELECT = """
    SELECT created_at, role, msg, seq_num
    FROM chats
    WHERE chat_id = ?
    ORDER BY seq_num;
"""

SELECT_CHATS = """
    SELECT titles.chat_id, titles.title
    FROM titles
    LEFT JOIN chats
        ON titles.chat_id = chats.chat_id
    GROUP BY titles.chat_id, titles.title
    ORDER BY MAX(chats.created_at) DESC;
"""

INSERT_TITLE = """
    INSERT INTO titles (chat_id, title) VALUES (?, ?);
"""

INSERT_MSG = """
    INSERT INTO chats (chat_id, seq_num, role, msg)
    VALUES (?, (SELECT COALESCE(MAX(seq_num) + 1, 0) FROM CHATS WHERE chat_id = ?), ?, ?);
"""

DELETE = """
    DELETE FROM titles WHERE chat_id = ?;
"""

UPDATE_TITLE = """
    UPDATE titles SET title = ? WHERE chat_id = ?;
"""

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_PATH = Path(os.environ.get("SPRINGCHAT_DB", str(PROJECT_ROOT / "db" / "springchat.db"))).expanduser().resolve()

def init_db() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(TITLES_SCHEMA)
        conn.execute(MESSAGES_SCHEMA)
        conn.commit()

def fetch_chat(chat_id: int) -> list[MsgModel]:
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        rows = conn.execute(SELECT, (chat_id,)).fetchall()    
        return [MsgModel(epoch_seconds=epoch_seconds, role=role, message=msg, seq_num=seq_num) for epoch_seconds, role, msg, seq_num in rows]

def fetch_all_chats() -> list[ChatModel]:
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        rows = conn.execute(SELECT_CHATS).fetchall()    
        return [ChatModel(chat_id=chat_id, title=title) for chat_id, title in rows]

def new_chat(chat_id: int, msg: str) -> None:
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        with conn:
            conn.execute(INSERT_TITLE, (chat_id, None))
            conn.execute(INSERT_MSG, (chat_id, None, 0, msg))

def add_msg_to_chat(chat_id: int, role: int, msg: str) -> bool:
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        with conn:
            cursor = conn.execute(INSERT_MSG, (chat_id, chat_id, role, msg))
            return cursor.rowcount > 0

def delete_chat(chat_id: int) -> bool:
    with closing(sqlite3.connect(DATABASE_PATH)) as conn:
        conn.execute("PRAGMA foreign_keys = ON")

        with conn:
            cursor = conn.execute(DELETE, (chat_id,))
            return cursor.rowcount > 0

def change_title(chat_id: int, title: str):
        with closing(sqlite3.connect(DATABASE_PATH)) as conn:
            with conn:
                conn.execute(UPDATE, (title, chat_id))
                conn.commit()
