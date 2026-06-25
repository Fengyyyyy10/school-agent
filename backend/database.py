import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.db')


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT NOT NULL,
            role       TEXT NOT NULL,
            content    TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_chat_username ON chat_messages(username)')
    conn.commit()
    conn.close()


def save_message(username: str, role: str, content: str):
    conn = _get_conn()
    conn.execute(
        'INSERT INTO chat_messages (username, role, content, created_at) VALUES (?, ?, ?, ?)',
        (username, role, content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def save_messages(username: str, messages: List[Dict]):
    if not messages:
        return
    conn = _get_conn()
    now = datetime.now().isoformat()
    rows = [(username, m['role'], m['content'], now) for m in messages]
    conn.executemany(
        'INSERT INTO chat_messages (username, role, content, created_at) VALUES (?, ?, ?, ?)',
        rows
    )
    conn.commit()
    conn.close()


def get_messages(username: str, limit: int = 100) -> List[Dict]:
    conn = _get_conn()
    cursor = conn.execute(
        'SELECT id, role, content, created_at FROM chat_messages WHERE username = ? ORDER BY id ASC',
        (username,)
    )
    rows = cursor.fetchall()
    conn.close()
    rows = rows[-limit:]
    return [{'id': r['id'], 'type': r['role'], 'content': r['content'], 'time': r['created_at']} for r in rows]


def delete_user_messages(username: str):
    conn = _get_conn()
    conn.execute('DELETE FROM chat_messages WHERE username = ?', (username,))
    conn.commit()
    conn.close()
