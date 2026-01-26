
import os
import re
import uuid
import sqlite3
import csv
from typing import List, Optional

from contact import Contact
from db import init_db, connect, get_db_path

class AddressBook:
    """
    AddressBook backend powered by SQLite.
    Each connected admin sees only their own contacts (owner_username).
    """

    def __init__(self, owner_username: str, db_path: Optional[str] = None):
        self.owner_username = owner_username.strip()
        self.db_path = db_path or get_db_path()
        init_db(self.db_path)

    # ---------- VALIDATION ----------
    @staticmethod
    def is_valid_email(email: str) -> bool:
        return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email) is not None

    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        # Morocco format: 0[5-7]XXXXXXXX or +212[5-7]XXXXXXXX
        return re.match(r'^(?:\+212|0)[5-7]\d{8}$', phone) is not None

    @staticmethod
    def normaliser_nom_prenom(nom: str, prenom: str):
        nom = nom.strip().upper()
        prenom = prenom.strip().capitalize()
        return nom, prenom

    # ---------- SQLITE CRUD ----------
    def get_all_contacts(self) -> List[Contact]:
        with connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id, nom, prenom, email, phone FROM contacts WHERE owner_username = ? ORDER BY nom, prenom;",
                (self.owner_username,)
            ).fetchall()
            return [Contact(row["nom"], row["prenom"], row["email"], row["phone"], row["id"]) for row in rows]

    def add_contact(self, nom: str, prenom: str, email: str, phone: str) -> bool:
        phone = str(phone).strip()
        email = email.strip()
        if not self.is_valid_email(email):
            return False
        if not self.is_valid_phone(phone):
            return False

        nom, prenom = self.normaliser_nom_prenom(nom, prenom)
        contact_id = str(uuid.uuid4())

        with connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO contacts(id, owner_username, nom, prenom, email, phone) VALUES(?,?,?,?,?,?);",
                (contact_id, self.owner_username, nom, prenom, email, phone)
            )
            conn.commit()
        return True

    def remove_contact(self, contact_id: str) -> bool:
        with connect(self.db_path) as conn:
            cur = conn.execute(
                "DELETE FROM contacts WHERE id = ? AND owner_username = ?;",
                (contact_id, self.owner_username)
            )
            conn.commit()
            return cur.rowcount > 0

    def update_contact(self, contact_id: str, new_nom: str, new_prenom: str, new_email: str, new_phone: str) -> bool:
        new_nom, new_prenom = self.normaliser_nom_prenom(new_nom, new_prenom)
        new_email = new_email.strip()
        new_phone = str(new_phone).strip()

        if not self.is_valid_email(new_email):
            return False
        if not self.is_valid_phone(new_phone):
            return False

        with connect(self.db_path) as conn:
            cur = conn.execute(
                """
                UPDATE contacts
                SET nom = ?, prenom = ?, email = ?, phone = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND owner_username = ?;
                """,
                (new_nom, new_prenom, new_email, new_phone, contact_id, self.owner_username)
            )
            conn.commit()
            return cur.rowcount > 0


    def get_contact(self, contact_id: str):
        with connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT id, nom, prenom, email, phone FROM contacts WHERE id = ? AND owner_username = ?;",
                (contact_id, self.owner_username)
            ).fetchone()
            if row is None:
                return None
            return Contact(row["nom"], row["prenom"], row["email"], row["phone"], row["id"])
    def search_contacts(self, keyword: str) -> List[Contact]:
        keyword = (keyword or "").strip().lower()
        if not keyword:
            return self.get_all_contacts()

        like = f"%{keyword}%"
        with connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT id, nom, prenom, email, phone
                FROM contacts
                WHERE owner_username = ?
                  AND (LOWER(nom) LIKE ?
                       OR LOWER(prenom) LIKE ?
                       OR LOWER(email) LIKE ?
                       OR phone LIKE ?)
                ORDER BY nom, prenom;
                """,
                (self.owner_username, like, like, like, like)
            ).fetchall()
            return [Contact(row["nom"], row["prenom"], row["email"], row["phone"], row["id"]) for row in rows]

    # ---------- EXPORT CSV ----------
    def export_to_csv(self, filepath: str) -> int:
        """
        Export current owner's contacts to a CSV file.
        Returns number of exported contacts.
        """
        contacts = self.get_all_contacts()
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "nom", "prenom", "email", "phone"])
            for c in contacts:
                writer.writerow([c.id, c.nom, c.prenom, c.email, c.phone])
        return len(contacts)

    # ---------- MIGRATION (optional) ----------
    def migrate_from_json_if_needed(self, json_file: str) -> int:
        """
        If there are no contacts for this owner, import from a legacy JSON file.
        Returns number of imported contacts.
        """
        if not json_file or not os.path.exists(json_file):
            return 0

        existing = self.get_all_contacts()
        if existing:
            return 0

        import json
        with open(json_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return 0

        imported = 0
        with connect(self.db_path) as conn:
            for item in data if isinstance(data, list) else []:
                # support old format without id
                cid = item.get("id") or str(uuid.uuid4())
                nom = (item.get("nom") or "").strip()
                prenom = (item.get("prenom") or "").strip()
                email = (item.get("email") or "").strip()
                phone = str(item.get("phone") or "").strip()

                if not (nom and prenom and email and phone):
                    continue

                nom, prenom = self.normaliser_nom_prenom(nom, prenom)

                try:
                    conn.execute(
                        "INSERT INTO contacts(id, owner_username, nom, prenom, email, phone) VALUES(?,?,?,?,?,?);",
                        (cid, self.owner_username, nom, prenom, email, phone)
                    )
                    imported += 1
                except sqlite3.IntegrityError:
                    # duplicated id
                    continue
            conn.commit()
        return imported
