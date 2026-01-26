import re
from werkzeug.security import generate_password_hash, check_password_hash

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^[0-9+\s-]{6,20}$")

def validate_email(email: str) -> bool:
    return bool(EMAIL_RE.match((email or "").strip()))

def validate_phone(phone: str) -> bool:
    return bool(PHONE_RE.match((phone or "").strip()))

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(stored_hash: str, password: str) -> bool:
    return check_password_hash(stored_hash, password)
