"""Pydantic models: request validation and response shapes."""
import re
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\+?[0-9 ()-]{7,20}$")


class StudentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100, examples=["Aarav Sharma"])
    date_of_birth: date = Field(examples=["2004-05-17"])
    email: Optional[str] = Field(None, examples=["aarav@example.com"])
    phone: Optional[str] = Field(None, examples=["+91 98765 43210"])
    course: Optional[str] = Field(None, max_length=100, examples=["Python Backend"])
    address: Optional[str] = Field(None, max_length=255)
    enrollment_date: Optional[date] = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("name must have at least 2 characters")
        return v

    @field_validator("email")
    @classmethod
    def check_email(cls, v):
        if v in (None, ""):
            return None
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("invalid email address")
        return v

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v):
        if v in (None, ""):
            return None
        v = v.strip()
        if not PHONE_RE.match(v):
            raise ValueError("invalid phone number")
        return v

    @field_validator("course", "address")
    @classmethod
    def blank_to_none(cls, v):
        return (v.strip() or None) if v else None

    @field_validator("date_of_birth")
    @classmethod
    def dob_in_past(cls, v: date) -> date:
        if v >= date.today():
            raise ValueError("date_of_birth must be in the past")
        return v

    @model_validator(mode="after")
    def need_contact(self):
        if not self.email and not self.phone:
            raise ValueError("provide at least one contact: email or phone")
        return self


class StudentUpdate(BaseModel):
    """PATCH body: every field optional. The merged result is re-validated."""
    name: Optional[str] = None
    date_of_birth: Optional[date] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    course: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: Optional[date] = None


class Student(BaseModel):
    id: int
    name: str
    date_of_birth: date
    email: Optional[str] = None
    phone: Optional[str] = None
    course: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: Optional[date] = None
    created_at: Optional[str] = None


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=300, examples=["How many students are there?"])
