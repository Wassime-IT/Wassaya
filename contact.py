import uuid

class Contact:
    def __init__(self, nom, prenom, email, phone, contact_id=None):
        self.nom = nom
        self.prenom = prenom
        self.email = email
        self.phone = phone
        self.id = contact_id or str(uuid.uuid4())  # Génère un id unique automatiquement

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "prenom": self.prenom,
            "email": self.email,
            "phone": self.phone
        }

    @staticmethod
    def from_dict(data):
        return Contact(
            data["nom"],
            data["prenom"],
            data["email"],
            data["phone"],
            contact_id=data.get("id")
        )

    def __str__(self):
        return f"{self.nom} {self.prenom} | {self.email} | {self.phone}"
