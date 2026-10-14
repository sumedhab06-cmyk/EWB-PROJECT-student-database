"""Students Database API: FastAPI + SQLite (+ optional Ollama assistant)."""
import json
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from . import ai, crud
from .database import get_db, init_db
from .schemas import AskRequest, Student, StudentCreate, StudentUpdate

STATIC = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="EWB Students Database API",
    description="CRUD API for student records. Interactive docs: /docs",
    version="1.0.0",
    lifespan=lifespan,
)


def _not_found(student_id: int):
    return HTTPException(404, f"Student with id {student_id} was not found")


def _duplicate():
    return HTTPException(409, "A student with this email already exists")


@app.post("/students", response_model=Student, status_code=201, tags=["Students"])
def create_student(student: StudentCreate, db=Depends(get_db)):
    try:
        return crud.create_student(db, student)
    except crud.DuplicateEmail:
        raise _duplicate()


@app.get("/students", response_model=list[Student], tags=["Students"])
def list_students(
    name: Optional[str] = Query(None, description="Partial name match"),
    course: Optional[str] = Query(None, description="Partial course match"),
    born_after: Optional[date] = Query(None, description="Date of birth on/after (YYYY-MM-DD)"),
    born_before: Optional[date] = Query(None, description="Date of birth on/before (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db=Depends(get_db),
):
    return crud.list_students(db, name, course, born_after, born_before, skip, limit)


@app.get("/students/{student_id}", response_model=Student, tags=["Students"])
def get_student(student_id: int, db=Depends(get_db)):
    student = crud.get_student(db, student_id)
    if not student:
        raise _not_found(student_id)
    return student


@app.put("/students/{student_id}", response_model=Student, tags=["Students"])
def replace_student(student_id: int, student: StudentCreate, db=Depends(get_db)):
    try:
        updated = crud.update_student(db, student_id, student)
    except crud.DuplicateEmail:
        raise _duplicate()
    if not updated:
        raise _not_found(student_id)
    return updated


@app.patch("/students/{student_id}", response_model=Student, tags=["Students"])
def patch_student(student_id: int, changes: StudentUpdate, db=Depends(get_db)):
    current = crud.get_student(db, student_id)
    if not current:
        raise _not_found(student_id)
    merged = {k: current[k] for k in crud.FIELDS} | changes.model_dump(exclude_unset=True)
    try:
        valid = StudentCreate(**merged)  # re-validate the complete record
    except ValidationError as exc:
        raise HTTPException(422, json.loads(exc.json(include_url=False, include_context=False)))
    try:
        return crud.update_student(db, student_id, valid)
    except crud.DuplicateEmail:
        raise _duplicate()


@app.delete("/students/{student_id}", status_code=204, tags=["Students"])
def delete_student(student_id: int, db=Depends(get_db)):
    if not crud.delete_student(db, student_id):
        raise _not_found(student_id)
    return Response(status_code=204)


@app.post("/ai/ask", tags=["Optional: Ollama"])
def ask_ai(body: AskRequest, db=Depends(get_db)):
    """Natural-language questions answered from retrieved records (needs Ollama running)."""
    try:
        return ai.ask(db, body.question)
    except ai.OllamaUnavailable:
        raise HTTPException(
            503, f"Ollama is not reachable. Start it and run: ollama pull {ai.OLLAMA_MODEL}"
        )


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
