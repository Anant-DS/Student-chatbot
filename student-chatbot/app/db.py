import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "chatbot.db"


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS chats(
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, student_id TEXT,
            question TEXT, answer TEXT, source TEXT, confidence REAL, rating INTEGER);
        CREATE TABLE IF NOT EXISTS tickets(
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, student_id TEXT,
            summary TEXT, reason TEXT, status TEXT DEFAULT 'open');
        """)


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log_chat(student_id, question, answer, source, confidence) -> int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO chats(ts,student_id,question,answer,source,confidence) VALUES(?,?,?,?,?,?)",
            (_now(), student_id, question, answer, source, confidence))
        return cur.lastrowid


def create_ticket(student_id, summary, reason) -> int:
    with _conn() as c:
        cur = c.execute("INSERT INTO tickets(ts,student_id,summary,reason) VALUES(?,?,?,?)",
                        (_now(), student_id, summary, reason))
        return cur.lastrowid


def set_rating(chat_id: int, rating: int):
    with _conn() as c:
        c.execute("UPDATE chats SET rating=? WHERE id=?", (rating, chat_id))


def stats() -> dict:
    with _conn() as c:
        total = c.execute("SELECT COUNT(*) FROM chats").fetchone()[0]
        tickets = c.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        rated = c.execute("SELECT COUNT(*) FROM chats WHERE rating IS NOT NULL").fetchone()[0]
        helpful = c.execute("SELECT COUNT(*) FROM chats WHERE rating=1").fetchone()[0]
        missed = [r["question"] for r in c.execute(
            "SELECT question FROM chats WHERE source='fallback' ORDER BY id DESC LIMIT 20")]
    return {
        "total_chats": total,
        "handed_to_staff": tickets,
        "resolved_without_staff_pct": round(100 * (total - tickets) / total, 1) if total else None,
        "helpful_pct": round(100 * helpful / rated, 1) if rated else None,
        "recent_unanswered_questions": missed,
    }
