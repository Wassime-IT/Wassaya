# Partie 6 — Application Web (Flask + SQLite)

## Rôles
- **Super-admin** : gère l'application, la base de données et les admins.
- **Admin** : gère les contacts, l'authentification, et le changement de mot de passe.
- **Contact** : crée un compte, se connecte, gère son profil, réserve un rendez-vous.

## Installation
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

## Lancer
```bash
cd webapp
flask --app app run --debug
```

Ouvre ensuite: http://127.0.0.1:5000

## Première configuration
- Va sur `/setup` pour créer le **premier super-admin** (uniquement si aucun super-admin n'existe).
