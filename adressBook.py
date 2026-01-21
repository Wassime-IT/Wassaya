import json
import os
import re
import uuid
from contact import Contact

class AddressBook:
    def __init__(self, filename="contact.json"):
        self.filename = filename
        self.contacts = []
        self.load_contacts()

    # ---------- FICHIER ----------
    def load_contacts(self):
        self.contacts = []
        if not os.path.exists(self.filename) or os.path.getsize(self.filename) == 0:
            return
        with open(self.filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                self.contacts.append(Contact.from_dict(item))

    def save_contacts(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(
                [c.to_dict() for c in self.contacts],
                f,
                indent=4,
                ensure_ascii=False
            )

    # ---------- VALIDATION ----------
    @staticmethod
    def is_valid_email(email):
        return re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email) is not None

    @staticmethod
    def is_valid_phone(phone):
        return re.match(r'^(?:\+212|0)[5-7]\d{8}$', phone) is not None

    @staticmethod
    def normaliser_nom_prenom(nom, prenom):
        nom = nom.strip().upper()
        prenom = prenom.strip().capitalize()
        return nom, prenom

    # ---------- CRUD ----------
    def add_contact(self, nom, prenom, email, phone):
        phone = str(phone)
        if not self.is_valid_email(email):
            return False
        if not self.is_valid_phone(phone):
            return False

        nom, prenom = self.normaliser_nom_prenom(nom, prenom)
        contact_id = str(uuid.uuid4())  # Génère un ID unique

        self.contacts.append(Contact(nom, prenom, email, phone, contact_id))
        self.save_contacts()
        return True

    def remove_contact(self, contact_id):
        for c in self.contacts:
            if c.id == contact_id:
                self.contacts.remove(c)
                self.save_contacts()
                return True
        return False

    def update_contact(self, contact_id, new_nom, new_prenom, new_email, new_phone):
        new_nom, new_prenom = self.normaliser_nom_prenom(new_nom, new_prenom)
        new_phone = str(new_phone)
        for c in self.contacts:
            if c.id == contact_id:
                c.nom = new_nom
                c.prenom = new_prenom
                c.email = new_email
                c.phone = new_phone if new_phone.startswith("0") else "0" + new_phone
                self.save_contacts()
                return True
        return False

    def display_contacts(self):
        if not self.contacts:
            print("Aucun contact dans le carnet d'adresses.")
            return
        for c in self.contacts:
            print(c)

    def search_contacts(self, keyword):
        keyword = keyword.lower()
        results = []
        for c in self.contacts:
            if (keyword in c.nom.lower() or
                keyword in c.prenom.lower() or
                keyword in c.email.lower() or
                keyword in c.phone):
                results.append(c)
        return results