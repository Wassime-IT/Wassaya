
import os
import tkinter as tk
from tkinter import messagebox

from gui import main_app
from db import (
    init_db,
    admin_exists,
    authenticate_admin,
    create_admin,
    migrate_login_json,
    get_db_path
)

DB_PATH = get_db_path()

def _startup_migrations():
    """
    Optional: migrate old login.json admins into SQLite (once).
    """
    init_db(DB_PATH)
    login_json = os.path.join(os.path.dirname(os.path.abspath(__file__)), "login.json")
    # migrate login.json users into SQLite (idempotent)
    if os.path.exists(login_json):
        migrated = migrate_login_json(login_json, DB_PATH)
        # if we imported at least one account, inform the user
        if migrated:
            try:
                messagebox.showinfo("Migration", f"{migrated} compte(s) admin importé(s) depuis login.json.")
            except Exception:
                pass

def login_window():
    _startup_migrations()

    root = tk.Tk()
    root.title("Connexion (Admins)")
    root.geometry("360x250")
    root.resizable(False, False)

    tk.Label(root, text="Nom d'utilisateur (admin)").pack(pady=6)
    entry_user = tk.Entry(root)
    entry_user.pack(pady=2)

    tk.Label(root, text="Mot de passe").pack(pady=6)
    entry_pass = tk.Entry(root, show="*")
    entry_pass.pack(pady=2)

    def do_login(event=None):
        username = entry_user.get().strip()
        password = entry_pass.get().strip()

        if not username or not password:
            messagebox.showwarning("Attention", "Tous les champs sont obligatoires")
            return

        if authenticate_admin(username, password, DB_PATH):
            root.destroy()
            main_app(username)  # Launch address book for this admin
        else:
            messagebox.showerror("Erreur", "Compte admin ou mot de passe incorrect")
            entry_pass.delete(0, tk.END)
            entry_user.focus()

    def open_create_admin():
        # If at least one admin exists, we do not allow creating new admins here
        # (you can extend later if needed).
        if admin_exists(DB_PATH):
            messagebox.showinfo("Info", "Un compte admin existe déjà.\nCréez les autres admins via un script (create_admin.py).")
            return

        win = tk.Toplevel(root)
        win.title("Créer le 1er admin")
        win.geometry("360x260")
        win.resizable(False, False)

        tk.Label(win, text="Créer le premier compte administrateur").pack(pady=8)

        tk.Label(win, text="Nom d'utilisateur").pack()
        e_u = tk.Entry(win)
        e_u.pack(pady=2)

        tk.Label(win, text="Mot de passe").pack()
        e_p1 = tk.Entry(win, show="*")
        e_p1.pack(pady=2)

        tk.Label(win, text="Confirmer mot de passe").pack()
        e_p2 = tk.Entry(win, show="*")
        e_p2.pack(pady=2)

        def create():
            u = e_u.get().strip()
            p1 = e_p1.get().strip()
            p2 = e_p2.get().strip()

            if not u or not p1 or not p2:
                messagebox.showwarning("Attention", "Tous les champs sont obligatoires")
                return
            if p1 != p2:
                messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas")
                return

            ok = create_admin(u, p1, DB_PATH, is_admin=True)
            if ok:
                messagebox.showinfo("Succès", "Admin créé. Vous pouvez vous connecter.")
                win.destroy()
                entry_user.delete(0, tk.END)
                entry_pass.delete(0, tk.END)
                entry_user.insert(0, u)
                entry_pass.focus()
            else:
                messagebox.showerror("Erreur", "Nom d'utilisateur déjà utilisé")

        tk.Button(win, text="Créer admin", width=20, bg="#28a745", fg="white", command=create).pack(pady=14)

    # Buttons
    tk.Button(
        root,
        text="Se connecter",
        width=22,
        bg="#007bff",
        fg="white",
        font=("Helvetica", 11, "bold"),
        command=do_login
    ).pack(pady=18)

    tk.Button(
        root,
        text="Créer le 1er admin",
        width=22,
        bg="#6c757d",
        fg="white",
        command=open_create_admin
    ).pack(pady=2)

    # Bind Enter
    root.bind("<Return>", do_login)

    # If no admin exists, suggest creating one
    if not admin_exists(DB_PATH):
        messagebox.showinfo("Initialisation", "Aucun admin trouvé.\nCliquez sur 'Créer le 1er admin'.")

    root.mainloop()

if __name__ == "__main__":
    login_window()
