import tkinter as tk
from tkinter import messagebox
import json
import os
from gui import main_app  # main_app(filename) accepte le fichier JSON spécifique

# ---------- Chargement des utilisateurs ----------
def load_users():
    if not os.path.exists("login.json") or os.path.getsize("login.json") == 0:
        return []
    with open("login.json", "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

# ---------- Récupérer le fichier contacts pour un utilisateur ----------
def get_user_contact_file(username, password):
    for u in load_users():
        if u["username"] == username and u["password"] == password:
            return u.get("contact_file")
    return None

# ---------- Fenêtre de login ----------
def login_window():
    root = tk.Tk()
    root.title("Connexion")
    root.geometry("320x200")
    root.resizable(False, False)

    tk.Label(root, text="Nom d'utilisateur").pack(pady=5)
    entry_user = tk.Entry(root)
    entry_user.pack(pady=2)

    tk.Label(root, text="Mot de passe").pack(pady=5)
    entry_pass = tk.Entry(root, show="*")
    entry_pass.pack(pady=2)

    # ---------- Fonction de connexion ----------
    def login():
        username = entry_user.get().strip()
        password = entry_pass.get().strip()

        if not username or not password:
            messagebox.showwarning("Attention", "Tous les champs sont obligatoires")
            return

        contact_file = get_user_contact_file(username, password)

        if contact_file:
            root.destroy()
            main_app(contact_file)  # Lancer le carnet avec le fichier JSON spécifique
        else:
            messagebox.showerror("Erreur", "Nom d'utilisateur ou mot de passe incorrect")
            entry_pass.delete(0, tk.END)  # Effacer le mot de passe
            entry_user.focus()

    # ---------- Bouton de connexion ----------
    tk.Button(
        root,
        text="Se connecter",
        width=20,
        bg="#007bff",
        fg="white",
        font=("Helvetica", 11, "bold"),
        command=login
    ).pack(pady=20)

    root.mainloop()

# ---------- Lancement ----------
if __name__ == "__main__":
    login_window()

