"""Demo student records. In a real system, replace this with calls to your
student information system (SIS) through a secure API."""
import hashlib
import hmac

_SALT = b"demo-salt-change-in-production"


def hash_pw(password: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), _SALT, 100_000).hex()


STUDENTS = {
    "2300001": {"name": "Asha Verma", "program": "B.Tech CSE, Year 2", "pw": hash_pw("asha123"),
                "fee_due": 42000, "due_date": "15 Dec 2026", "attendance": "82%"},
    "2300002": {"name": "Rohan Mehta", "program": "BBA, Year 1", "pw": hash_pw("rohan123"),
                "fee_due": 0, "due_date": "Paid", "attendance": "91%"},
}


def authenticate(student_id: str, password: str):
    s = STUDENTS.get(student_id)
    if s and hmac.compare_digest(s["pw"], hash_pw(password)):
        return s
    return None


def get(student_id: str):
    return STUDENTS.get(student_id)
