import tkinter as tk
from tkinter import messagebox
import json
import os
import hashlib
import secrets

from gui import main_app  # main_app(filename) accepte le fichier JSON spécifique

LOGIN_DB = "login.json"

# =========================
# Sécurité : hachage sha256 + sel
# =========================
def _hash_password(password: str, salt: str) -> str:
    """Retourne le hash SHA-256 de (salt + password)."""
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

def _ensure_user_has_hash(user: dict) -> bool:
    """
    Compatibilité: si l'utilisateur est au format ancien (password en clair),
    on le migre automatiquement vers (salt + password_hash).
    Retourne True si une migration a eu lieu.
    """
    if "password_hash" in user and "salt" in user:
        return False

    plain = user.get("password")
    if plain is None:
        return False

    salt = secrets.token_hex(16)
    user["salt"] = salt
    user["password_hash"] = _hash_password(str(plain), salt)
    user.pop("password", None)
    return True

# =========================
# Accès données (login.json)
# =========================
def load_users() -> list[dict]:
    if not os.path.exists(LOGIN_DB) or os.path.getsize(LOGIN_DB) == 0:
        return []
    with open(LOGIN_DB, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

def save_users(users: list[dict]) -> None:
    with open(LOGIN_DB, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

# =========================
# Authentification ADMIN
# =========================
def authenticate_admin(username: str, password: str) -> tuple[bool, str | None, str | None]:
    """
    Retourne: (ok, contact_file, error_message)
    - ok: True si authentifié ET admin
    - contact_file: fichier json contacts à ouvrir
    - error_message: message d'erreur si ok=False
    """
    users = load_users()
    changed = False

    for u in users:
        if u.get("username") != username:
            continue

        if _ensure_user_has_hash(u):
            changed = True

        if not bool(u.get("is_admin", False)):
            return False, None, "Accès réservé aux administrateurs."

        salt = u.get("salt", "")
        stored = u.get("password_hash", "")

        if salt and stored and _hash_password(password, salt) == stored:
            if changed:
                save_users(users)
            return True, u.get("contact_file"), None

        return False, None, "Nom d'utilisateur ou mot de passe incorrect."

    return False, None, "Nom d'utilisateur ou mot de passe incorrect."

# =========================
# Fenêtre Tkinter
# =========================
def login_window():
    root = tk.Tk()
    root.title("Connexion (Admin)")
    root.geometry("340x210")
    root.resizable(False, False)

    tk.Label(root, text="Nom d'utilisateur").pack(pady=(10, 3))
    entry_user = tk.Entry(root)
    entry_user.pack(pady=2)

    tk.Label(root, text="Mot de passe").pack(pady=(8, 3))
    entry_pass = tk.Entry(root, show="*")
    entry_pass.pack(pady=2)

    status = tk.Label(root, text="", fg="red")
    status.pack(pady=(6, 0))

    def login():
        username = entry_user.get().strip()
        password = entry_pass.get().strip()

        if not username or not password:
            messagebox.showwarning("Attention", "Tous les champs sont obligatoires")
            return

        ok, contact_file, err = authenticate_admin(username, password)
        if ok and contact_file:
            root.destroy()
            main_app(contact_file)
            return

        status.config(text=err or "Échec de connexion.")
        entry_pass.delete(0, tk.END)
        entry_user.focus()

    def on_enter(_event):
        login()

    entry_user.bind("<Return>", on_enter)
    entry_pass.bind("<Return>", on_enter)

    tk.Button(
        root,
        text="Se connecter",
        width=20,
        bg="#007bff",
        fg="white",
        font=("Helvetica", 11, "bold"),
        command=login
    ).pack(pady=16)

    tk.Label(
        root,
        text="Note : accès limité aux comptes admin.\nMots de passe stockés hachés (SHA-256 + sel).",
        fg="#555555",
        justify="center",
        font=("Helvetica", 8)
    ).pack(pady=(0, 8))

    root.mainloop()

if __name__ == "__main__":
    login_window()
