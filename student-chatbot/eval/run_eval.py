"""Measures how often the retriever finds the right knowledge-base entry.
Run:  python -m eval.run_eval"""
import json
from pathlib import Path

from app.retriever import Retriever

BASE = Path(__file__).resolve().parent.parent
retriever = Retriever(BASE / "data" / "knowledge_base.json")
cases = json.loads((BASE / "eval" / "questions.json").read_text())

hits = 0
for c in cases:
    found = retriever.search(c["q"], k=1)
    got = found[0]["id"] if found else None
    ok = got == c["expect"]
    hits += ok
    print(("PASS" if ok else "FAIL"), "|", c["q"], "->", got)
print(f"\nAccuracy: {hits}/{len(cases)} = {100 * hits / len(cases):.0f}%")
