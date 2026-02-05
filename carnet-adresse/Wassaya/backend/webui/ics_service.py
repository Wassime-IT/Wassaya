from datetime import timedelta, timezone as dt_timezone
from django.utils import timezone


def _ensure_aware(dt):
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def _dt_utc(dt):
    dt = _ensure_aware(dt)
    return dt.astimezone(dt_timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _dt_local(dt):
    # format local sans "Z" (pour DTSTART;TZID=...)
    dt = _ensure_aware(dt)
    return timezone.localtime(dt).strftime("%Y%m%dT%H%M%S")


def _escape_ics(text: str) -> str:
    # échappement ICS (\, ; , et nouvelles lignes)
    if text is None:
        return ""
    text = str(text)
    text = text.replace("\\", "\\\\")
    text = text.replace(";", "\\;")
    text = text.replace(",", "\\,")
    text = text.replace("\n", "\\n")
    return text


def appointment_to_ics(appointment, duration_minutes=30):
    start = _ensure_aware(appointment.datetime)
    end = start + timedelta(minutes=duration_minutes)

    # timezone id du serveur (ex: Africa/Casablanca)
    tzid = getattr(timezone.get_current_timezone(), "key", "UTC")

    doctor_name = appointment.doctor.user.get_full_name() or appointment.doctor.user.username
    patient_name = appointment.patient.user.get_full_name() or appointment.patient.user.username

    summary = f"RDV Wassaya - Dr {doctor_name}"
    description = (
        f"Rendez-vous Wassaya\n"
        f"Docteur: Dr {doctor_name}\n"
        f"Patient: {patient_name}\n"
        f"Statut: {appointment.status}\n"
        f"Motif: {appointment.reason or '-'}\n"
    )

    # (optionnel) location si tu ajoutes plus tard clinic address
    location = "Wassaya Clinic"

    uid = f"wassaya-rdv-{appointment.id}@wassaya.local"
    dtstamp = _dt_utc(timezone.now())

    # Lien vers l’ICS download (utile sur mobile)
    # En prod tu mettras ton domaine
    url = f"http://127.0.0.1:8000/site/rdv/ics/{appointment.id}/"

    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Wassaya//Clinic//FR",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{dtstamp}",

        # ✅ DTSTART local avec TZID (mieux pour les calendriers)
        f"DTSTART;TZID={tzid}:{_dt_local(start)}",
        f"DTEND;TZID={tzid}:{_dt_local(end)}",

        f"SUMMARY:{_escape_ics(summary)}",
        f"DESCRIPTION:{_escape_ics(description)}",
        f"LOCATION:{_escape_ics(location)}",
        f"URL:{_escape_ics(url)}",

        # ✅ reminder 30 min avant
        "BEGIN:VALARM",
        "TRIGGER:-PT30M",
        "ACTION:DISPLAY",
        "DESCRIPTION:Rappel RDV Wassaya",
        "END:VALARM",

        "END:VEVENT",
        "END:VCALENDAR",
        ""
    ]
    return "\r\n".join(ics_lines)
# ===== END OF FILE =====
