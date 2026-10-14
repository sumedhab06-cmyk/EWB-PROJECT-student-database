"""All database operations (parameterised SQL only)."""
import sqlite3
from datetime import date
from typing import Optional

from .schemas import StudentCreate

FIELDS = ["name", "date_of_birth", "email", "phone", "course", "address", "enrollment_date"]


class DuplicateEmail(Exception):
    pass


def _values(s: StudentCreate) -> list:
    d = s.model_dump(mode="json")
    return [d[f] for f in FIELDS]


def create_student(db, s: StudentCreate) -> dict:
    try:
        cur = db.execute(
            f"INSERT INTO students ({', '.join(FIELDS)}) VALUES ({', '.join('?' * len(FIELDS))})",
            _values(s),
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise DuplicateEmail()
    return get_student(db, cur.lastrowid)


def get_student(db, student_id: int) -> Optional[dict]:
    row = db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    return dict(row) if row else None


def list_students(db, name: Optional[str] = None, course: Optional[str] = None,
                  born_after: Optional[date] = None, born_before: Optional[date] = None,
                  skip: int = 0, limit: int = 100) -> list[dict]:
    where, args = [], []
    if name:
        where.append("name LIKE ?"); args.append(f"%{name}%")
    if course:
        where.append("course LIKE ?"); args.append(f"%{course}%")
    if born_after:
        where.append("date_of_birth >= ?"); args.append(born_after.isoformat())
    if born_before:
        where.append("date_of_birth <= ?"); args.append(born_before.isoformat())
    sql = "SELECT * FROM students"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id LIMIT ? OFFSET ?"
    return [dict(r) for r in db.execute(sql, (*args, limit, skip)).fetchall()]


def update_student(db, student_id: int, s: StudentCreate) -> Optional[dict]:
    if not get_student(db, student_id):
        return None
    try:
        db.execute(
            f"UPDATE students SET {', '.join(f + ' = ?' for f in FIELDS)} WHERE id = ?",
            (*_values(s), student_id),
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise DuplicateEmail()
    return get_student(db, student_id)


def delete_student(db, student_id: int) -> bool:
    cur = db.execute("DELETE FROM students WHERE id = ?", (student_id,))
    db.commit()
    return cur.rowcount > 0
