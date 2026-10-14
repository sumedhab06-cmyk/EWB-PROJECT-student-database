# EWB Students Database: FastAPI + SQLite

A Python backend for managing student records with full **Create / Read / Update / Delete** support, built for the EWB Edu Tech internship assignment. It includes a small web interface and an **optional local AI assistant** (Ollama).

**Stack:** Python 3.9+, FastAPI, SQLite (standard library `sqlite3`), Pydantic validation.

## Features

- All four CRUD operations with persistent SQLite storage (`students.db`, created automatically)
- Filtering by name, course and date of birth, plus pagination
- Input validation (name, email/phone format, date of birth in the past, at least one contact) and clear error handling (`404` missing record, `409` duplicate email, `422` invalid input)
- Web UI at `/` and interactive Swagger docs at `/docs`
- Optional Ollama extension that answers questions grounded in database records
- Automated tests (`pytest`) and dummy seed data

## Prerequisites

- Python 3.9 or newer
- (Optional, for the AI bonus) [Ollama](https://ollama.com) installed

## Installation

```bash
git clone <your-repo-url> students-crud
cd students-crud
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python seed.py                     # optional: load 10 dummy students
uvicorn app.main:app --reload
```

- Web UI: http://127.0.0.1:8000
- API docs (try every endpoint in the browser): http://127.0.0.1:8000/docs

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/students` | Create a student |
| GET | `/students` | List / filter (`name`, `course`, `born_after`, `born_before`, `skip`, `limit`) |
| GET | `/students/{student_id}` | View one student |
| PUT | `/students/{student_id}` | Replace all details |
| PATCH | `/students/{student_id}` | Update only the fields you send |
| DELETE | `/students/{student_id}` | Delete a student (`204`) |
| POST | `/ai/ask` | Optional: ask a question in plain English |

**Student fields:** `id` (auto), `name`, `date_of_birth` (YYYY-MM-DD), `email` and/or `phone` (at least one required), and optional `course`, `address`, `enrollment_date`.

## Testing the API with curl

```bash
# Create
curl -X POST http://127.0.0.1:8000/students -H "Content-Type: application/json" \
  -d '{"name":"Nisha Verma","date_of_birth":"2005-03-14","email":"nisha@example.com","course":"Python Backend"}'

# List and filter
curl "http://127.0.0.1:8000/students"
curl "http://127.0.0.1:8000/students?course=Python&born_after=2005-01-01"

# View one
curl http://127.0.0.1:8000/students/1

# Update (partial)
curl -X PATCH http://127.0.0.1:8000/students/1 -H "Content-Type: application/json" -d '{"course":"Data Science"}'

# Delete
curl -X DELETE http://127.0.0.1:8000/students/1

# Missing record -> 404
curl -i http://127.0.0.1:8000/students/9999
```

## Run the tests

```bash
pytest
```

Tests use a temporary database, so your `students.db` is never touched.

## Optional: ask questions with Ollama

1. Install Ollama, then pull a small model: `ollama pull llama3.2:1b`
2. Make sure Ollama is running (default `http://localhost:11434`).
3. Ask from the web UI, or:

```bash
curl -X POST http://127.0.0.1:8000/ai/ask -H "Content-Type: application/json" \
  -d '{"question":"List students born after 2005"}'
```

**How it stays accurate and safe**

1. Backend code reads the question (years, course names, student names) and fetches matching records using fixed, parameterised queries.
2. The records, plus the total student count, are passed to the model as context. It is told to answer only from that data.
3. The model **never writes or runs SQL**.
4. The response includes `records_used`, so every answer can be checked against its source.

Change the model or server with environment variables `OLLAMA_MODEL` and `OLLAMA_URL`. If Ollama is not running, `/ai/ask` returns a clear `503` message and the rest of the app works normally.

## Project structure

```
app/
  main.py       routes and error handling
  crud.py       SQLite operations
  schemas.py    Pydantic models and validation
  database.py   connection and schema
  ai.py         optional Ollama integration
static/index.html   web interface
tests/test_api.py   automated tests
seed.py             dummy data loader
```

## Data and security notes

- All seed data is fictional (`example.com` emails, made-up numbers). Do not commit real student information.
- `.gitignore` excludes `*.db` and `.env`; no secrets are stored in this project.
