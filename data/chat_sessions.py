from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from threading import Lock
from typing import Dict, List, Optional


class ChatSessionStore:
    def __init__(self, file_path: str = "data/chat_sessions_store.json"):
        self._sessions: Dict[str, Dict] = {}
        self._lock = Lock()
        self._file_path = file_path
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        if not os.path.exists(self._file_path):
            return

        try:
            with open(self._file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, dict):
                    self._sessions = data
        except Exception:
            self._sessions = {}

    def _save_to_disk(self) -> None:
        directory = os.path.dirname(self._file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(self._file_path, "w", encoding="utf-8") as file:
            json.dump(self._sessions, file, ensure_ascii=False, indent=2)

    def get_stats(self) -> Dict[str, int | str]:
        with self._lock:
            chat_count = len(self._sessions)
            message_count = 0
            for session in self._sessions.values():
                history = session.get("history", [])
                message_count += len(history)
        return {
            "backend": "json",
            "file_path": self._file_path,
            "chat_count": chat_count,
            "message_count": message_count,
        }

    def get_or_create(self, chat_id: str) -> Dict:
        with self._lock:
            if chat_id not in self._sessions:
                self._sessions[chat_id] = {
                    "agent_id": None,
                    "history": []
                }
                self._save_to_disk()
            return self._sessions[chat_id]

    def get_agent_id(self, chat_id: str) -> Optional[str]:
        session = self.get_or_create(chat_id)
        return session.get("agent_id")

    def set_agent_id(self, chat_id: str, agent_id: Optional[str]) -> None:
        with self._lock:
            session = self._sessions.get(chat_id)
            if session is None:
                session = {
                    "agent_id": None,
                    "history": []
                }
                self._sessions[chat_id] = session
            session["agent_id"] = agent_id
            self._save_to_disk()

    def append_turn(self, chat_id: str, user_prompt: str, assistant_reply: str) -> str:
        with self._lock:
            session = self._sessions.get(chat_id)
            if session is None:
                session = {
                    "agent_id": None,
                    "history": []
                }
                self._sessions[chat_id] = session
            created_at = datetime.now(timezone.utc).isoformat()
            session["history"].append({
                "user": user_prompt,
                "assistant": assistant_reply,
                "created_at": created_at
            })
            self._save_to_disk()
            return created_at

    def get_recent_turns(self, chat_id: str, limit: int = 6) -> List[Dict[str, str]]:
        session = self.get_or_create(chat_id)
        history = session.get("history", [])
        normalized = []
        for turn in history[-limit:]:
            normalized.append({
                "user": turn.get("user", ""),
                "assistant": turn.get("assistant", ""),
                "created_at": turn.get("created_at")
            })
        return normalized
