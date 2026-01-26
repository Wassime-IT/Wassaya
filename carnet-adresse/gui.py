
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkFont

from adressBook import AddressBook

def _guess_legacy_json(username: str) -> str:
    """
    Tries to find legacy JSON contact file used by the old version:
    - contact_<username>.json
    - contact_user.json / contact_wassime.json ...
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, f"contact_{username}.json"),
        os.path.join(base_dir, "contact_user.json") if username == "user" else "",
    ]
    return next((c for c in candidates if c and os.path.exists(c)), "")

def main_app(username: str):
    root = tk.Tk()
    root.title(f"Carnet d'adresses - {username}")
    root.geometry("780x560")
    root.resizable(False, False)

    # ---------- Carnet (SQLite) ----------
    book = AddressBook(owner_username=username)

    # Optional: migrate contacts from legacy JSON for this user (only if DB is empty)
    legacy_json = _guess_legacy_json(username)
    if legacy_json:
        book.migrate_from_json_if_needed(legacy_json)

    # ---------- Fonctions ----------
    def afficher_contacts(contacts=None):
        tree.delete(*tree.get_children())
        if contacts is None:
            contacts = book.get_all_contacts()
        for c in contacts:
            tree.insert("", tk.END, iid=c.id, values=(c.nom, c.prenom, c.email, c.phone))

    def clear_entries():
        entry_nom.delete(0, tk.END)
        entry_prenom.delete(0, tk.END)
        entry_email.delete(0, tk.END)
        entry_phone.delete(0, tk.END)

    def ajouter_contact():
        nom = entry_nom.get().strip()
        prenom = entry_prenom.get().strip()
        email = entry_email.get().strip()
        phone = entry_phone.get().strip()

        if not nom or not prenom or not email or not phone:
            messagebox.showwarning("Erreur", "Tous les champs sont obligatoires")
            return

        if book.add_contact(nom, prenom, email, phone):
            messagebox.showinfo("Succès", "Contact ajouté")
            clear_entries()
            afficher_contacts()
        else:
            messagebox.showerror("Erreur", "Email ou téléphone invalide")

    def supprimer_contact():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Attention", "Sélectionnez un contact")
            return
        contact_id = selected[0]
        if messagebox.askyesno("Confirmation", "Supprimer ce contact ?"):
            if book.remove_contact(contact_id):
                afficher_contacts()
                clear_entries()
                messagebox.showinfo("Succès", "Contact supprimé")
            else:
                messagebox.showerror("Erreur", "Impossible de supprimer le contact")

    def modifier_contact():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Attention", "Sélectionnez un contact")
            return
        contact_id = selected[0]

        new_nom = entry_nom.get().strip()
        new_prenom = entry_prenom.get().strip()
        new_email = entry_email.get().strip()
        new_phone = entry_phone.get().strip()

        if not new_nom or not new_prenom or not new_email or not new_phone:
            messagebox.showwarning("Erreur", "Tous les champs sont obligatoires")
            return

        ok = book.update_contact(contact_id, new_nom, new_prenom, new_email, new_phone)
        if ok:
            afficher_contacts()
            clear_entries()
            messagebox.showinfo("Succès", "Contact modifié")
        else:
            messagebox.showerror("Erreur", "Email/téléphone invalide ou contact introuvable")

    def on_tree_select(event):
        selected = tree.selection()
        if not selected:
            return
        contact_id = selected[0]
        contact = book.get_contact(contact_id)
        if contact:
            clear_entries()
            entry_nom.insert(0, contact.nom)
            entry_prenom.insert(0, contact.prenom)
            entry_email.insert(0, contact.email)
            entry_phone.insert(0, contact.phone)

    def rechercher_contact(*args):
        query = search_var.get().strip()
        if not query:
            afficher_contacts()
            return
        afficher_contacts(book.search_contacts(query))

    def exporter_csv():
        filepath = filedialog.asksaveasfilename(
            title="Exporter en CSV",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")]
        )
        if not filepath:
            return
        try:
            n = book.export_to_csv(filepath)
            messagebox.showinfo("Export CSV", f"{n} contact(s) exporté(s) vers:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Erreur export", str(e))

    # ---------- Frames ----------
    frame_form = tk.LabelFrame(root, text="Informations du contact", padx=10, pady=10)
    frame_form.pack(fill="x", padx=10, pady=5)

    frame_buttons = tk.Frame(root)
    frame_buttons.pack(pady=5)

    frame_search = tk.Frame(root)
    frame_search.pack(fill="x", padx=10)

    frame_table = tk.Frame(root)
    frame_table.pack(fill="both", expand=True, padx=10, pady=5)

    # ---------- Formulaire ----------
    tk.Label(frame_form, text="Nom").grid(row=0, column=0, sticky="w")
    entry_nom = tk.Entry(frame_form, width=32)
    entry_nom.grid(row=0, column=1, pady=2)

    tk.Label(frame_form, text="Prénom").grid(row=1, column=0, sticky="w")
    entry_prenom = tk.Entry(frame_form, width=32)
    entry_prenom.grid(row=1, column=1, pady=2)

    tk.Label(frame_form, text="Email").grid(row=2, column=0, sticky="w")
    entry_email = tk.Entry(frame_form, width=32)
    entry_email.grid(row=2, column=1, pady=2)

    tk.Label(frame_form, text="Téléphone").grid(row=3, column=0, sticky="w")
    entry_phone = tk.Entry(frame_form, width=32)
    entry_phone.grid(row=3, column=1, pady=2)

    # ---------- Boutons ----------
    button_font = tkFont.Font(family="Helvetica", size=11, weight="bold")
    tk.Button(frame_buttons, text="Ajouter", width=14, font=button_font, bg="#28a745", fg="white", command=ajouter_contact).grid(row=0, column=0, padx=5, pady=2)
    tk.Button(frame_buttons, text="Modifier", width=14, font=button_font, bg="#007bff", fg="white", command=modifier_contact).grid(row=0, column=1, padx=5, pady=2)
    tk.Button(frame_buttons, text="Supprimer", width=14, font=button_font, bg="#dc3545", fg="white", command=supprimer_contact).grid(row=0, column=2, padx=5, pady=2)
    tk.Button(frame_buttons, text="Exporter CSV", width=14, font=button_font, bg="#17a2b8", fg="white", command=exporter_csv).grid(row=0, column=3, padx=5, pady=2)
    tk.Button(frame_buttons, text="Quitter", width=14, font=button_font, bg="#6c757d", fg="white", command=root.quit).grid(row=0, column=4, padx=5, pady=2)

    # ---------- Recherche ----------
    tk.Label(frame_search, text="Rechercher").pack(anchor="w")
    search_var = tk.StringVar(master=root)
    search_var.trace_add("write", rechercher_contact)
    entry_search = tk.Entry(frame_search, textvariable=search_var)
    entry_search.pack(fill="x", pady=3)

    # ---------- Tableau ----------
    columns = ("Nom", "Prénom", "Email", "Téléphone")
    tree = ttk.Treeview(frame_table, columns=columns, show="headings", height=14)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=175)
    tree.pack(fill="both", expand=True)
    tree.bind("<<TreeviewSelect>>", on_tree_select)

    # ---------- Lancer l'affichage ----------
    afficher_contacts()
    root.mainloop()
