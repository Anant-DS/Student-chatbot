import re
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

import jwt

from . import config

SENSITIVE_WORDS = [
    "suicide", "kill myself", "end my life", "self harm", "self-harm", "hurt myself",
    "harassment", "harassed", "abuse", "assault", "ragging", "threat", "depressed",
    "can't cope", "cannot cope", "panic attack", "complaint against",
]
INJECTION_PATTERNS = [
    r"ignore (all |your )?(previous|prior) instructions", r"reveal (your )?(system )?prompt",
    r"you are now", r"act as (an? )?(admin|developer)", r"disregard .* rules",
]


def create_token(student_id: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=config.TOKEN_MINUTES)
    return jwt.encode({"sub": student_id, "exp": exp}, config.SECRET_KEY, algorithm="HS256")


def verify_token(token: str):
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"]).get("sub")
    except jwt.PyJWTError:
        return None


def mask_pii(text: str) -> str:
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[email]", text)
    text = re.sub(r"\b\d{10,}\b", "[number]", text)
    text = re.sub(r"\b\d{4}[ -]\d{4}[ -]\d{4}\b", "[number]", text)
    return text


def is_sensitive(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in SENSITIVE_WORDS)


def looks_like_injection(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in INJECTION_PATTERNS)


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit, self.window = limit, window_seconds
        self.hits = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.time()
        q = self.hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.limit:
            return False
        q.append(now)
        return True
