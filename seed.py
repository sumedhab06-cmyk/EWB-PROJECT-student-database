"""Fill the database with DUMMY students. Usage: python seed.py [--reset]"""
import sys

from app import crud
from app.database import get_conn, init_db
from app.schemas import StudentCreate

DUMMY = [
    ("Aarav Sharma", "2004-05-17", "aarav.sharma@example.com", "+91 98765 00001", "Python Backend", "2024-07-01"),
    ("Diya Patel", "2005-11-02", "diya.patel@example.com", "+91 98765 00002", "Data Science", "2024-07-01"),
    ("Kabir Singh", "2003-02-21", "kabir.singh@example.com", None, "Python Backend", "2023-07-10"),
    ("Ananya Iyer", "2006-08-30", "ananya.iyer@example.com", "+91 98765 00004", "Web Development", "2025-01-15"),
    ("Rohan Mehta", "2005-01-09", None, "+91 98765 00005", "Data Science", "2024-01-20"),
    ("Isha Reddy", "2004-12-12", "isha.reddy@example.com", "+91 98765 00006", "Web Development", "2024-07-01"),
    ("Vihaan Gupta", "2007-03-25", "vihaan.gupta@example.com", None, "Python Backend", "2025-07-01"),
    ("Meera Nair", "2002-09-14", "meera.nair@example.com", "+91 98765 00008", "Cloud Computing", "2022-07-05"),
    ("Arjun Das", "2006-06-06", "arjun.das@example.com", "+91 98765 00009", "Cloud Computing", "2025-01-15"),
    ("Saanvi Rao", "2005-04-18", "saanvi.rao@example.com", "+91 98765 00010", "Python Backend", "2024-07-01"),
]

if __name__ == "__main__":
    init_db()
    db = get_conn()
    if "--reset" in sys.argv:
        db.execute("DELETE FROM students"); db.commit()
    if db.execute("SELECT COUNT(*) FROM students").fetchone()[0]:
        sys.exit("Database already has students. Use --reset to replace them.")
    for n, dob, em, ph, course, enr in DUMMY:
        crud.create_student(db, StudentCreate(name=n, date_of_birth=dob, email=em, phone=ph,
                                              course=course, enrollment_date=enr))
    print(f"Seeded {len(DUMMY)} dummy students.")
