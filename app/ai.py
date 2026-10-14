"""Optional bonus: answer questions about students with a local Ollama model.

Safety design: the model NEVER writes or runs SQL. Backend code interprets the
question, runs fixed, parameterised queries, and hands the resulting records to
the model as context. The model only phrases the answer.
"""
import json
import os
import re
import urllib.error
import urllib.request
from datetime import date

from . import crud

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
MAX_RECORDS = 25


class OllamaUnavailable(Exception):
    pass


def retrieve(db, question: str) -> dict:
    """Pick relevant records with plain code (year / course / name matching)."""
    q = question.lower()
    everyone = crud.list_students(db, limit=10_000)
    filters, after, before = [], None, None

    years = [int(y) for y in re.findall(r"\b(19\d{2}|20\d{2})\b", q)]
    if years:
        y = years[0]
        if re.search(r"\b(after|later than|since)\b", q):
            after = date(y + 1, 1, 1); filters.append(f"born after {y}")
        elif re.search(r"\b(before|earlier than|until)\b", q):
            before = date(y - 1, 12, 31); filters.append(f"born before {y}")
        else:
            after, before = date(y, 1, 1), date(y, 12, 31); filters.append(f"born in {y}")

    course = next((c for c in {s["course"] for s in everyone if s["course"]} if c.lower() in q), None)
    if course:
        filters.append(f"course is {course}")

    matched = crud.list_students(db, course=course, born_after=after, born_before=before, limit=10_000)

    if not filters:  # maybe the question names a student
        words = set(re.findall(r"[a-z]{3,}", q))
        named = [s for s in everyone if words & set(re.findall(r"[a-z]{3,}", s["name"].lower()))]
        if named:
            matched, filters = named, ["name mentioned in question"]

    return {"total": len(everyone), "filters": filters, "matched": len(matched),
            "records": matched[:MAX_RECORDS]}


def build_prompt(question: str, ctx: dict) -> str:
    lines = [
        f"- #{r['id']} {r['name']}, born {r['date_of_birth']}, course: {r['course'] or 'n/a'}, "
        f"email: {r['email'] or 'n/a'}, phone: {r['phone'] or 'n/a'}"
        for r in ctx["records"]
    ] or ["- (no matching records)"]
    return (
        "You are an assistant for a student database. Answer ONLY from the data below. "
        "If the data does not contain the answer, say you don't know. Be brief.\n\n"
        f"Total students in database: {ctx['total']}\n"
        f"Filters applied: {', '.join(ctx['filters']) or 'none'}\n"
        f"Records matching filters: {ctx['matched']}\n"
        f"Records (up to {MAX_RECORDS}):\n" + "\n".join(lines) + f"\n\nQuestion: {question}\nAnswer:"
    )


def ask(db, question: str) -> dict:
    ctx = retrieve(db, question)
    body = json.dumps({
        "model": OLLAMA_MODEL, "stream": False, "options": {"temperature": 0},
        "messages": [{"role": "user", "content": build_prompt(question, ctx)}],
    }).encode()
    req = urllib.request.Request(f"{OLLAMA_URL}/api/chat", body, {"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            answer = json.load(resp)["message"]["content"].strip()
    except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as exc:
        raise OllamaUnavailable(str(exc))
    return {"answer": answer, "model": OLLAMA_MODEL, "filters": ctx["filters"],
            "total_students": ctx["total"], "matched": ctx["matched"], "records_used": ctx["records"]}
