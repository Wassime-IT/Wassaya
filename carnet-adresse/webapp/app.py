from __future__ import annotations
from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
from functools import wraps

from db import init_db, get_conn
from security import validate_email, validate_phone, hash_password, verify_password

def create_app():
    app = Flask(__name__)
    app.secret_key = "CHANGE_ME__dev_secret_key"
    init_db()

    def now_iso() -> str:
        return datetime.utcnow().isoformat(timespec="seconds")

    def current_user():
        uid = session.get("user_id")
        if not uid:
            return None
        conn = get_conn()
        user = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
        conn.close()
        return user

    def login_required(roles=None):
        roles_set = set(roles) if roles else None
        def decorator(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                user = current_user()
                if not user:
                    flash("Veuillez vous connecter.", "err")
                    return redirect(url_for("login"))
                if roles_set and user["role"] not in roles_set:
                    flash("Accès refusé.", "err")
                    return redirect(url_for("dashboard"))
                return fn(*args, **kwargs)
            return wrapper
        return decorator

    @app.context_processor
    def inject_user():
        return {"me": current_user()}

    @app.get("/setup")
    @app.post("/setup")
    def setup():
        conn = get_conn()
        exists = conn.execute("SELECT 1 FROM users WHERE role='superadmin' LIMIT 1").fetchone()
        if exists:
            conn.close()
            flash("Le super-admin existe déjà.", "err")
            return redirect(url_for("login"))

        if request.method == "POST":
            first = request.form.get("first_name","").strip()
            last = request.form.get("last_name","").strip()
            email = request.form.get("email","").strip().lower()
            phone = request.form.get("phone","").strip()
            password = request.form.get("password","")
            if not (first and last and email and phone and password):
                flash("Tous les champs sont obligatoires.", "err")
                conn.close()
                return render_template("setup.html")
            if not validate_email(email):
                flash("Email invalide.", "err"); conn.close(); return render_template("setup.html")
            if not validate_phone(phone):
                flash("Téléphone invalide.", "err"); conn.close(); return render_template("setup.html")

            try:
                conn.execute(
                    "INSERT INTO users(role, first_name, last_name, email, phone, password_hash, created_at) VALUES(?,?,?,?,?,?,?)",
                    ("superadmin", first, last, email, phone, hash_password(password), now_iso())
                )
                conn.commit()
                flash("Super-admin créé. Connectez-vous.", "ok")
                conn.close()
                return redirect(url_for("login"))
            except Exception:
                flash("Erreur: email déjà utilisé.", "err")
                conn.close()
                return render_template("setup.html")

        conn.close()
        return render_template("setup.html")

    @app.get("/")
    def home():
        if current_user():
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.get("/login")
    @app.post("/login")
    def login():
        if request.method == "POST":
            email = request.form.get("email","").strip().lower()
            password = request.form.get("password","")
            conn = get_conn()
            user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            conn.close()
            if not user or not verify_password(user["password_hash"], password):
                flash("Email ou mot de passe incorrect.", "err")
                return render_template("login.html")
            session["user_id"] = user["id"]
            flash("Connexion réussie.", "ok")
            return redirect(url_for("dashboard"))
        return render_template("login.html")

    @app.get("/logout")
    def logout():
        session.clear()
        flash("Déconnecté.", "ok")
        return redirect(url_for("login"))

    @app.get("/dashboard")
    @login_required()
    def dashboard():
        user = current_user()
        if user["role"] == "superadmin":
            return redirect(url_for("superadmin_panel"))
        if user["role"] == "admin":
            return redirect(url_for("admin_panel"))
        return redirect(url_for("contact_panel"))

    @app.get("/superadmin")
    @login_required(roles=["superadmin"])
    def superadmin_panel():
        conn = get_conn()
        admins = conn.execute("SELECT * FROM users WHERE role IN ('superadmin','admin') ORDER BY role DESC, created_at DESC").fetchall()
        conn.close()
        return render_template("superadmin.html", admins=admins)

    @app.get("/superadmin/admins/new")
    @app.post("/superadmin/admins/new")
    @login_required(roles=["superadmin"])
    def superadmin_create_admin():
        if request.method == "POST":
            first = request.form.get("first_name","").strip()
            last = request.form.get("last_name","").strip()
            email = request.form.get("email","").strip().lower()
            phone = request.form.get("phone","").strip()
            password = request.form.get("password","")
            role = request.form.get("role","admin").strip()
            if role not in ("admin","superadmin"):
                role = "admin"

            if not (first and last and email and phone and password):
                flash("Tous les champs sont obligatoires.", "err")
                return render_template("admin_form.html")
            if not validate_email(email):
                flash("Email invalide.", "err"); return render_template("admin_form.html")
            if not validate_phone(phone):
                flash("Téléphone invalide.", "err"); return render_template("admin_form.html")

            conn = get_conn()
            try:
                conn.execute(
                    "INSERT INTO users(role, first_name, last_name, email, phone, password_hash, created_at) VALUES(?,?,?,?,?,?,?)",
                    (role, first, last, email, phone, hash_password(password), now_iso())
                )
                conn.commit()
                conn.close()
                flash("Admin créé.", "ok")
                return redirect(url_for("superadmin_panel"))
            except Exception:
                conn.close()
                flash("Email déjà utilisé.", "err")
                return render_template("admin_form.html")

        return render_template("admin_form.html")

    @app.post("/superadmin/admins/<int:user_id>/delete")
    @login_required(roles=["superadmin"])
    def superadmin_delete_admin(user_id: int):
        me = current_user()
        if me["id"] == user_id:
            flash("Vous ne pouvez pas supprimer votre propre compte.", "err")
            return redirect(url_for("superadmin_panel"))

        conn = get_conn()
        user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        if not user or user["role"] not in ("admin","superadmin"):
            conn.close()
            flash("Compte introuvable.", "err")
            return redirect(url_for("superadmin_panel"))

        conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
        conn.close()
        flash("Compte supprimé.", "ok")
        return redirect(url_for("superadmin_panel"))

    @app.get("/superadmin/db")
    @login_required(roles=["superadmin"])
    def superadmin_db_info():
        conn = get_conn()
        counts = {
            "superadmins": conn.execute("SELECT COUNT(*) FROM users WHERE role='superadmin'").fetchone()[0],
            "admins": conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0],
            "contacts": conn.execute("SELECT COUNT(*) FROM users WHERE role='contact'").fetchone()[0],
            "appointments": conn.execute("SELECT COUNT(*) FROM appointments").fetchone()[0],
        }
        conn.close()
        return render_template("db_info.html", counts=counts)

    @app.get("/admin")
    @login_required(roles=["admin","superadmin"])
    def admin_panel():
        conn = get_conn()
        q = (request.args.get("q") or "").strip().lower()
        if q:
            like = f"%{q}%"
            contacts = conn.execute(
                """SELECT * FROM users
                    WHERE role='contact' AND (lower(first_name) LIKE ? OR lower(last_name) LIKE ? OR lower(email) LIKE ? OR phone LIKE ?)
                    ORDER BY created_at DESC""",
                (like, like, like, like)
            ).fetchall()
        else:
            contacts = conn.execute("SELECT * FROM users WHERE role='contact' ORDER BY created_at DESC").fetchall()
        conn.close()
        return render_template("admin.html", contacts=contacts, q=q)

    @app.get("/admin/contacts/new")
    @app.post("/admin/contacts/new")
    @login_required(roles=["admin","superadmin"])
    def admin_create_contact():
        if request.method == "POST":
            first = request.form.get("first_name","").strip()
            last = request.form.get("last_name","").strip()
            email = request.form.get("email","").strip().lower()
            phone = request.form.get("phone","").strip()
            password = request.form.get("password","")
            if not (first and last and email and phone and password):
                flash("Tous les champs sont obligatoires.", "err")
                return render_template("contact_form.html", mode="create")
            if not validate_email(email):
                flash("Email invalide.", "err"); return render_template("contact_form.html", mode="create")
            if not validate_phone(phone):
                flash("Téléphone invalide.", "err"); return render_template("contact_form.html", mode="create")

            conn = get_conn()
            try:
                conn.execute(
                    "INSERT INTO users(role, first_name, last_name, email, phone, password_hash, created_at) VALUES(?,?,?,?,?,?,?)",
                    ("contact", first, last, email, phone, hash_password(password), now_iso())
                )
                conn.commit()
                conn.close()
                flash("Contact créé.", "ok")
                return redirect(url_for("admin_panel"))
            except Exception:
                conn.close()
                flash("Email déjà utilisé.", "err")
                return render_template("contact_form.html", mode="create")

        return render_template("contact_form.html", mode="create")

    @app.get("/admin/contacts/<int:contact_id>/edit")
    @app.post("/admin/contacts/<int:contact_id>/edit")
    @login_required(roles=["admin","superadmin"])
    def admin_edit_contact(contact_id: int):
        conn = get_conn()
        contact = conn.execute("SELECT * FROM users WHERE id=? AND role='contact'", (contact_id,)).fetchone()
        if not contact:
            conn.close()
            flash("Contact introuvable.", "err")
            return redirect(url_for("admin_panel"))

        if request.method == "POST":
            first = request.form.get("first_name","").strip()
            last = request.form.get("last_name","").strip()
            phone = request.form.get("phone","").strip()
            if not (first and last and phone):
                flash("Nom, prénom et téléphone sont obligatoires.", "err")
                return render_template("contact_form.html", mode="edit", contact=contact)
            if not validate_phone(phone):
                flash("Téléphone invalide.", "err")
                return render_template("contact_form.html", mode="edit", contact=contact)

            conn.execute("UPDATE users SET first_name=?, last_name=?, phone=? WHERE id=?", (first, last, phone, contact_id))
            conn.commit()
            conn.close()
            flash("Contact mis à jour.", "ok")
            return redirect(url_for("admin_panel"))

        conn.close()
        return render_template("contact_form.html", mode="edit", contact=contact)

    @app.post("/admin/contacts/<int:contact_id>/delete")
    @login_required(roles=["admin","superadmin"])
    def admin_delete_contact(contact_id: int):
        conn = get_conn()
        conn.execute("DELETE FROM appointments WHERE contact_id=?", (contact_id,))
        conn.execute("DELETE FROM users WHERE id=? AND role='contact'", (contact_id,))
        conn.commit()
        conn.close()
        flash("Contact supprimé.", "ok")
        return redirect(url_for("admin_panel"))

    @app.get("/admin/password")
    @app.post("/admin/password")
    @login_required(roles=["admin","superadmin"])
    def admin_change_password():
        user = current_user()
        if request.method == "POST":
            current = request.form.get("current_password","")
            newp = request.form.get("new_password","")
            if not (current and newp):
                flash("Champs manquants.", "err"); return render_template("change_password.html")
            if not verify_password(user["password_hash"], current):
                flash("Mot de passe actuel incorrect.", "err"); return render_template("change_password.html")
            conn = get_conn()
            conn.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(newp), user["id"]))
            conn.commit(); conn.close()
            flash("Mot de passe modifié.", "ok")
            return redirect(url_for("admin_panel"))
        return render_template("change_password.html")

    @app.get("/register")
    @app.post("/register")
    def register():
        if request.method == "POST":
            first = request.form.get("first_name","").strip()
            last = request.form.get("last_name","").strip()
            email = request.form.get("email","").strip().lower()
            phone = request.form.get("phone","").strip()
            password = request.form.get("password","")
            if not (first and last and email and phone and password):
                flash("Tous les champs sont obligatoires.", "err")
                return render_template("register.html")
            if not validate_email(email):
                flash("Email invalide.", "err"); return render_template("register.html")
            if not validate_phone(phone):
                flash("Téléphone invalide.", "err"); return render_template("register.html")

            conn = get_conn()
            try:
                conn.execute(
                    "INSERT INTO users(role, first_name, last_name, email, phone, password_hash, created_at) VALUES(?,?,?,?,?,?,?)",
                    ("contact", first, last, email, phone, hash_password(password), now_iso())
                )
                conn.commit()
                user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
                conn.close()
                session["user_id"] = user["id"]
                flash("Compte créé.", "ok")
                return redirect(url_for("contact_panel"))
            except Exception:
                conn.close()
                flash("Email déjà utilisé.", "err")
                return render_template("register.html")

        return render_template("register.html")

    @app.get("/contact")
    @login_required(roles=["contact"])
    def contact_panel():
        user = current_user()
        conn = get_conn()
        appts = conn.execute(
            "SELECT * FROM appointments WHERE contact_id=? ORDER BY created_at DESC", (user["id"],)
        ).fetchall()
        conn.close()
        return render_template("contact.html", appts=appts)

    @app.get("/contact/profile")
    @app.post("/contact/profile")
    @login_required(roles=["contact"])
    def contact_profile():
        user = current_user()
        if request.method == "POST":
            phone = request.form.get("phone","").strip()
            if not validate_phone(phone):
                flash("Téléphone invalide.", "err"); return render_template("profile.html", user=user)
            conn = get_conn()
            conn.execute("UPDATE users SET phone=? WHERE id=?", (phone, user["id"]))
            conn.commit(); conn.close()
            flash("Profil mis à jour.", "ok")
            return redirect(url_for("contact_profile"))
        return render_template("profile.html", user=user)

    @app.get("/contact/password")
    @app.post("/contact/password")
    @login_required(roles=["contact"])
    def contact_change_password():
        user = current_user()
        if request.method == "POST":
            current = request.form.get("current_password","")
            newp = request.form.get("new_password","")
            if not (current and newp):
                flash("Champs manquants.", "err"); return render_template("change_password.html")
            if not verify_password(user["password_hash"], current):
                flash("Mot de passe actuel incorrect.", "err"); return render_template("change_password.html")
            conn = get_conn()
            conn.execute("UPDATE users SET password_hash=? WHERE id=?", (hash_password(newp), user["id"]))
            conn.commit(); conn.close()
            flash("Mot de passe modifié.", "ok")
            return redirect(url_for("contact_panel"))
        return render_template("change_password.html")

    @app.get("/contact/appointments/new")
    @app.post("/contact/appointments/new")
    @login_required(roles=["contact"])
    def contact_new_appointment():
        user = current_user()
        if request.method == "POST":
            scheduled_at = request.form.get("scheduled_at","").strip()
            note = request.form.get("note","").strip() or None
            if not scheduled_at:
                flash("Veuillez choisir une date/heure.", "err")
                return render_template("appointment_form.html")

            try:
                dt = datetime.fromisoformat(scheduled_at)
            except Exception:
                flash("Format date/heure invalide.", "err")
                return render_template("appointment_form.html")

            conn = get_conn()
            conn.execute(
                "INSERT INTO appointments(contact_id, scheduled_at, note, status, created_at) VALUES(?,?,?,?,?)",
                (user["id"], dt.isoformat(timespec="minutes"), note, "pending", now_iso())
            )
            conn.commit(); conn.close()
            flash("Rendez-vous demandé.", "ok")
            return redirect(url_for("contact_panel"))

        return render_template("appointment_form.html")

    return app

app = create_app()
