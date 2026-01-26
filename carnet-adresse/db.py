
import os
import sqlite3
import hashlib
import secrets
from typing import Optional, Tuple, List, Dict, Any

DEFAULT_DB_FILENAME = "addressbook.db"

def get_db_path(db_filename: str = DEFAULT_DB_FILENAME) -> str:
    """Return an absolute path to the SQLite DB stored next to the project files."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, db_filename)

def connect(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Optional[str] = None) -> None:
    """Create tables if they don't exist."""
    with connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 1
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id TEXT PRIMARY KEY,
                owner_username TEXT NOT NULL,
                nom TEXT NOT NULL,
                prenom TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_contacts_owner
            ON contacts(owner_username);
        """)
        conn.commit()

# ---------------- Password helpers ----------------
def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Return (salt, password_hash) using SHA-256(salt + password).
    salt is hex string.
    """
    if salt is None:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((salt + password).encode("utf-8")).hexdigest()
    return salt, pwd_hash

def verify_password(password: str, salt: str, password_hash: str) -> bool:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest() == password_hash

# ---------------- Admin CRUD ----------------
def admin_exists(db_path: Optional[str] = None) -> bool:
    init_db(db_path)
    with connect(db_path) as conn:
        row = conn.execute("SELECT 1 FROM admins LIMIT 1;").fetchone()
        return row is not None

def create_admin(username: str, password: str, db_path: Optional[str] = None, is_admin: bool = True) -> bool:
    """
    Create an admin account. Returns True if created, False if username already exists.
    """
    init_db(db_path)
    username = username.strip()
    if not username or not password:
        raise ValueError("username/password required")
    salt, pwd_hash = hash_password(password)
    try:
        with connect(db_path) as conn:
            conn.execute(
                "INSERT INTO admins(username, salt, password_hash, is_admin) VALUES(?,?,?,?);",
                (username, salt, pwd_hash, 1 if is_admin else 0)
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_admin(username: str, password: str, db_path: Optional[str] = None) -> bool:
    init_db(db_path)
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT salt, password_hash, is_admin FROM admins WHERE username = ?;",
            (username.strip(),)
        ).fetchone()
        if row is None:
            return False
        if int(row["is_admin"]) != 1:
            return False
        return verify_password(password, row["salt"], row["password_hash"])

def migrate_login_json(login_json_path: str, db_path: Optional[str] = None) -> int:
    """
    Optional helper: migrate users from old login.json into admins table.
    Only migrates entries with is_admin == true (if present) or all users if no flag.
    Supports either plaintext 'password' or 'salt'+'password_hash'.
    Returns number of migrated accounts.
    """
    import json
    init_db(db_path)
    if not os.path.exists(login_json_path):
        return 0

    with open(login_json_path, "r", encoding="utf-8") as f:
        try:
            users = json.load(f)
        except json.JSONDecodeError:
            return 0

    migrated = 0
    with connect(db_path) as conn:
        for u in users if isinstance(users, list) else []:
            username = (u.get("username") or "").strip()
            if not username:
                continue
            # determine admin flag
            is_admin = u.get("is_admin")
            if is_admin is None:
                is_admin = True  # old file had no roles; treat as admin for compatibility
            if not bool(is_admin):
                continue

            if "salt" in u and "password_hash" in u:
                salt = u["salt"]
                pwd_hash = u["password_hash"]
            elif "password" in u:
                salt, pwd_hash = hash_password(str(u["password"]))
            else:
                continue

            try:
                conn.execute(
                    "INSERT INTO admins(username, salt, password_hash, is_admin) VALUES(?,?,?,1);",
                    (username, salt, pwd_hash)
                )
                migrated += 1
            except sqlite3.IntegrityError:
                pass
        conn.commit()
    return migrated
