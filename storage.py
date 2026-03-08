import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

DB_PATH = Path("data/homonyms.db")


def _connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with _connect() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                ip          TEXT    NOT NULL,
                date        TEXT    NOT NULL,
                word_ids    TEXT    NOT NULL,
                score       REAL    NOT NULL,
                created_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS guesses (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id           INTEGER NOT NULL REFERENCES sessions(id),
                guess_text           TEXT    NOT NULL,
                matched              INTEGER NOT NULL,
                matched_definition_id TEXT,
                guessed_at           TEXT    NOT NULL
            );
        """)


init_db()


def save_result(ip, word_ids, guesses, _matched_ids, score):
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as con:
        cur = con.execute(
            "INSERT INTO sessions (ip, date, word_ids, score, created_at) VALUES (?, ?, ?, ?, ?)",
            (ip, date.today().isoformat(), json.dumps(word_ids) if not isinstance(word_ids, str) else word_ids, score, now),
        )
        session_id = cur.lastrowid
        con.executemany(
            "INSERT INTO guesses (session_id, guess_text, matched, matched_definition_id, guessed_at) VALUES (?, ?, ?, ?, ?)",
            [
                (session_id, g["text"], int(g["matched"]), g.get("matched_definition_id"), now)
                for g in guesses
            ],
        )


def get_result(ip, word_ids):
    key = json.dumps(word_ids) if not isinstance(word_ids, str) else word_ids
    with _connect() as con:
        row = con.execute(
            "SELECT * FROM sessions WHERE ip = ? AND word_ids = ? AND date = ? ORDER BY id DESC LIMIT 1",
            (ip, key, date.today().isoformat()),
        ).fetchone()
        return dict(row) if row else None
