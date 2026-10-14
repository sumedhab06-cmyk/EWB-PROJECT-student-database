import os
import tempfile

os.environ["STUDENTS_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")

from fastapi.testclient import TestClient  # noqa: E402

from app import ai  # noqa: E402
from app.database import get_conn  # noqa: E402
from app.main import app  # noqa: E402

GOOD = {"name": "Test Student", "date_of_birth": "2004-01-01", "email": "t@example.com", "course": "Python"}


def test_crud_flow():
    with TestClient(app) as c:
        r = c.post("/students", json=GOOD)
        assert r.status_code == 201
        sid = r.json()["id"]
        assert c.get(f"/students/{sid}").json()["name"] == "Test Student"
        assert len(c.get("/students", params={"name": "test"}).json()) == 1
        assert c.patch(f"/students/{sid}", json={"course": "Data"}).json()["course"] == "Data"
        put = c.put(f"/students/{sid}", json={**GOOD, "name": "Renamed One"})
        assert put.json()["name"] == "Renamed One"
        assert c.delete(f"/students/{sid}").status_code == 204
        assert c.get(f"/students/{sid}").status_code == 404


def test_validation_and_errors():
    with TestClient(app) as c:
        assert c.post("/students", json={**GOOD, "email": "bad"}).status_code == 422
        assert c.post("/students", json={"name": "No Contact", "date_of_birth": "2004-01-01"}).status_code == 422
        assert c.post("/students", json={**GOOD, "date_of_birth": "2999-01-01"}).status_code == 422
        assert c.get("/students/9999").status_code == 404
        assert c.delete("/students/9999").status_code == 404
        assert c.put("/students/9999", json=GOOD).status_code == 404
        c.post("/students", json={**GOOD, "email": "dup@example.com"})
        assert c.post("/students", json={**GOOD, "email": "dup@example.com"}).status_code == 409


def test_filters_and_ai_retrieval():
    with TestClient(app) as c:
        c.post("/students", json={**GOOD, "email": "a@example.com", "date_of_birth": "2006-03-03"})
        rows = c.get("/students", params={"born_after": "2006-01-01"}).json()
        assert rows and all(s["date_of_birth"] >= "2006-01-01" for s in rows)
        db = get_conn()
        ctx = ai.retrieve(db, "List students born after 2005")
        assert ctx["matched"] >= 1 and all(r["date_of_birth"] >= "2006-01-01" for r in ctx["records"])
        assert ai.retrieve(db, "How many students are there?")["total"] >= 1
        db.close()
