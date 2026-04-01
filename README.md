Wassaya 🏥 — Hospital Appointment Management System (Django)

Wassaya est une application web (Django) de gestion de rendez-vous médicaux qui connecte patients et médecins autour d’un workflow simple et sécurisé : réservation, validation et suivi des rendez-vous.

🔥 Fonctionnalités principales
Authentification + rôles : Admin / Doctor / Patient
Espace Patient
Consulter la liste des médecins (filtre spécialité, recherche, pagination)
Prendre un rendez-vous (validation date future + anti-conflit créneau)
Suivre ses rendez-vous (tabs À venir / Passés, tri, filtres)
Annuler un rendez-vous
Espace Docteur
Voir les demandes de RDV (par défaut : PENDING)
Confirmer ou refuser un rendez-vous
Suivi complet des RDV (tabs + filtres + tri)
Notifications Email (HTML) :
RDV créé (PENDING)
RDV confirmé/refusé (status update)
RDV annulé
Export Calendrier (.ics) :
Téléchargement ICS depuis le site
Pièce jointe ICS dans l’email lors du RDV CONFIRMED
🧱 Stack technique
Backend : Django + (DRF optionnel)
DB : SQLite (dev) / extensible vers PostgreSQL
Auth : Session Django (webui) + JWT (API si activée)
UI : Templates Django + Bootstrap 5
Email : EmailMultiAlternatives (HTML + texte) + Mailpit/Mailtrap en dev


--LANCER LE PROJET
dans powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
