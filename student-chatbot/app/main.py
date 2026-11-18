from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import hmac

from . import config, db, security, students
from .llm import generate_answer
from .retriever import Retriever

BASE = Path(__file__).resolve().parent.parent
app = FastAPI(title="Student Support Chatbot")
app.add_middleware(CORSMiddleware, allow_origins=config.ALLOWED_ORIGINS,
                   allow_methods=["GET", "POST"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

retriever = Retriever(BASE / "data" / "knowledge_base.json")
limiter = security.RateLimiter(config.RATE_LIMIT, 60)
db.init_db()

HANDOVER_TEXT = ("I want to make sure you get the right help, so I have passed your message to our "
                 "student support team. They will contact you soon. If this is urgent, please call "
                 "the helpline listed on the Contact page or visit the student services office.")
CRISIS_TEXT = ("I'm sorry you are going through this. You deserve support from a real person. I have "
               "alerted our student support team, and I encourage you to contact the university "
               "counselling centre or a trusted person now. If you are in immediate danger, call "
               "your local emergency number.")


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    history: list[dict] = Field(default_factory=list)


class LoginIn(BaseModel):
    student_id: str = Field(min_length=1, max_length=20)
    password: str = Field(min_length=1, max_length=100)


class FeedbackIn(BaseModel):
    chat_id: int
    rating: int = Field(ge=0, le=1)


def student_from_header(authorization: Optional[str]):
    if authorization and authorization.startswith("Bearer "):
        return security.verify_token(authorization[7:])
    return None


def clean_history(history: list) -> list:
    """Keep the last turns, only valid roles, strictly alternating, starting with 'user'."""
    out = []
    for h in history[-6:]:
        role, text = h.get("role"), h.get("content")
        if role not in ("user", "assistant") or not isinstance(text, str):
            continue
        if (out and out[-1]["role"] == role) or (not out and role != "user"):
            continue
        out.append({"role": role, "content": text[:500]})
    if out and out[-1]["role"] == "user":
        out.pop()
    return out


def personal_intent(text: str):
    t = text.lower()
    if " my " not in f" {t} " and "mine" not in t:
        return None

    # General payment how-to questions should use the FAQ.
    if any(phrase in t for phrase in (
        "how can i pay", "how do i pay", "how to pay", "where can i pay"
    )):
        return None

    if any(word in t for word in ("fee", "due", "balance", "payment")):
        return "fee"
    if "attendance" in t:
        return "attendance"
    return None


def reply(answer, chat_id, sources=None, escalated=False, needs_login=False):
    return {"answer": answer, "chat_id": chat_id, "sources": sources or [],
            "escalated": escalated, "needs_login": needs_login}


@app.post("/api/login")
def login(body: LoginIn):
    s = students.authenticate(body.student_id.strip(), body.password)
    if not s:
        raise HTTPException(401, "Student ID or password is incorrect.")
    return {"token": security.create_token(body.student_id.strip()), "name": s["name"]}


@app.post("/api/chat")
def chat(body: ChatIn, request: Request, authorization: Optional[str] = Header(default=None)):
    ip = request.client.host if request.client else "unknown"
    if not limiter.allow(ip):
        raise HTTPException(429, "Too many messages. Please wait a minute and try again.")

    text = body.message.strip()
    sid = student_from_header(authorization)
    masked = security.mask_pii(text)

    if security.looks_like_injection(text):
        ans = "I can only help with student services questions. How can I help you with those?"
        return reply(ans, db.log_chat(sid, masked, ans, "blocked", 1.0))

    if security.is_sensitive(text):
        db.create_ticket(sid, masked, "sensitive")
        return reply(CRISIS_TEXT, db.log_chat(sid, masked, CRISIS_TEXT, "escalation", 1.0), escalated=True)

    intent = personal_intent(text)
    if intent:
        s = students.get(sid) if sid else None
        if not s:
            ans = "To see your personal details, please sign in with your student ID first."
            return reply(ans, db.log_chat(sid, masked, ans, "login", 1.0), needs_login=True)
        if intent == "fee":
            ans = (f"{s['name']}, your outstanding fee is Rs {s['fee_due']:,}. Last date: {s['due_date']}."
                   if s["fee_due"] else f"{s['name']}, you have no pending fee. Thank you!")
        else:
            ans = f"{s['name']}, your current attendance is {s['attendance']}."
        return reply(ans, db.log_chat(sid, masked, ans, "student_record", 1.0))

    passages = retriever.search(text, k=3)
    if not passages or passages[0]["score"] < config.MIN_CONFIDENCE:
        db.create_ticket(sid, masked, "low_confidence")
        return reply(HANDOVER_TEXT, db.log_chat(sid, masked, HANDOVER_TEXT, "fallback", 0.0), escalated=True)

    best = passages[0]
    ans = generate_answer(text, passages, clean_history(body.history)) or best["answer"]
    sources = [{"title": p["title"], "source": p.get("source", "Knowledge base")} for p in passages[:2]]
    return reply(ans, db.log_chat(sid, masked, ans, "kb", best["score"]), sources=sources)


@app.post("/api/feedback")
def feedback(body: FeedbackIn):
    db.set_rating(body.chat_id, body.rating)
    return {"ok": True}


@app.get("/api/stats")
def stats(x_admin_key: Optional[str] = Header(default=None)):
    if not x_admin_key or not hmac.compare_digest(x_admin_key, config.ADMIN_KEY):
        raise HTTPException(403, "Admin key required.")
    return db.stats()


@app.get("/")
def home():
    return FileResponse(BASE / "static" / "index.html")
