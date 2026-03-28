from __future__ import annotations

import os
import sqlite3
from threading import Lock
from typing import Dict, List, Optional


class ChatSessionStore:
    def __init__(self, db_path: str = "data/chat_sessions.db"):
        self._db_path = db_path
        self._lock = Lock()
        self._ensure_parent_dir()
        self._init_db()

    def _ensure_parent_dir(self) -> None:
        directory = os.path.dirname(self._db_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chats (
                    chat_id TEXT PRIMARY KEY,
                    agent_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id TEXT NOT NULL,
                    user_prompt TEXT NOT NULL,
                    assistant_reply TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(chat_id) REFERENCES chats(chat_id)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_chat_id_id ON messages(chat_id, id)"
            )
            conn.commit()

    def get_stats(self) -> Dict[str, int | str]:
        with self._connect() as conn:
            chats_row = conn.execute("SELECT COUNT(*) AS total FROM chats").fetchone()
            messages_row = conn.execute("SELECT COUNT(*) AS total FROM messages").fetchone()
        return {
            "backend": "sqlite",
            "db_path": self._db_path,
            "chat_count": int(chats_row["total"] if chats_row else 0),
            "message_count": int(messages_row["total"] if messages_row else 0),
        }

    def get_or_create(self, chat_id: str) -> Dict:
        with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT agent_id FROM chats WHERE chat_id = ?",
                    (chat_id,),
                ).fetchone()
                if row is None:
                    conn.execute(
                        "INSERT INTO chats (chat_id, agent_id) VALUES (?, ?)",
                        (chat_id, None),
                    )
                    conn.commit()
                    agent_id = None
                else:
                    agent_id = row["agent_id"]

            return {
                "agent_id": agent_id,
                "history": self.get_recent_turns(chat_id, limit=1000),
            }

    def get_agent_id(self, chat_id: str) -> Optional[str]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT agent_id FROM chats WHERE chat_id = ?",
                (chat_id,),
            ).fetchone()
            if row is None:
                return None
            return row["agent_id"]

    def set_agent_id(self, chat_id: str, agent_id: Optional[str]) -> None:
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO chats (chat_id, agent_id, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(chat_id)
                    DO UPDATE SET agent_id = excluded.agent_id, updated_at = CURRENT_TIMESTAMP
                    """,
                    (chat_id, agent_id),
                )
                conn.commit()

    def append_turn(self, chat_id: str, user_prompt: str, assistant_reply: str) -> str:
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO chats (chat_id, agent_id, updated_at)
                    VALUES (?, NULL, CURRENT_TIMESTAMP)
                    ON CONFLICT(chat_id) DO NOTHING
                    """,
                    (chat_id,),
                )
                conn.execute(
                    """
                    INSERT INTO messages (chat_id, user_prompt, assistant_reply)
                    VALUES (?, ?, ?)
                    """,
                    (chat_id, user_prompt, assistant_reply),
                )
                row = conn.execute(
                    "SELECT created_at FROM messages WHERE id = last_insert_rowid()"
                ).fetchone()
                conn.execute(
                    "UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE chat_id = ?",
                    (chat_id,),
                )
                conn.commit()
                return row["created_at"] if row else ""

    def get_recent_turns(self, chat_id: str, limit: int = 6) -> List[Dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT user_prompt, assistant_reply, created_at
                FROM messages
                WHERE chat_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (chat_id, limit),
            ).fetchall()

        ordered = list(reversed(rows))
        return [
            {
                "user": row["user_prompt"],
                "assistant": row["assistant_reply"],
                "created_at": row["created_at"]
            }
            for row in ordered
        ]
