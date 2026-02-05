# webui/email_service.py
from __future__ import annotations

import logging
from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse, NoReverseMatch
from django.utils import timezone

from .ics_service import appointment_to_ics
from wassaya_rdv.models import EmailLog  # ✅ EmailLog est dans wassaya_rdv

logger = logging.getLogger(__name__)


# -----------------------------
# Utils
# -----------------------------
def _get_site_url() -> str:
    site_url = getattr(settings, "SITE_URL", "http://127.0.0.1:8000")
    return str(site_url).rstrip("/")


def _abs_url(path: str) -> str:
    base = _get_site_url() + "/"
    return urljoin(base, str(path).lstrip("/"))


def _safe_email(addr) -> str | None:
    if not addr:
        return None
    addr = str(addr).strip()
    return addr if "@" in addr else None


def _fullname_or_username(user) -> str:
    if not user:
        return ""
    full = (getattr(user, "get_full_name", lambda: "")() or "").strip()
    return full or getattr(user, "username", "") or ""


def _format_dt(dt) -> str:
    if not dt:
        return ""
    return timezone.localtime(dt).strftime("%d/%m/%Y %H:%M")


def _badge_for_status(status: str) -> tuple[str, str]:
    status = (status or "").upper()
    mapping = {
        "CONFIRMED": ("#e8fff1", "#0a7a35"),
        "REJECTED": ("#ffecec", "#b10012"),
        "CANCELLED": ("#f1f3f5", "#495057"),
        "PENDING": ("#fff6e6", "#8a5a00"),
    }
    return mapping.get(status, ("#fff6e6", "#8a5a00"))


def _base_ctx(appointment) -> dict:
    patient_user = getattr(getattr(appointment, "patient", None), "user", None)
    doctor_user = getattr(getattr(appointment, "doctor", None), "user", None)

    return {
        "patient_name": _fullname_or_username(patient_user),
        "doctor_name": _fullname_or_username(doctor_user),
        "dt": _format_dt(getattr(appointment, "datetime", None)),
        "reason": getattr(appointment, "reason", "") or "",
        "site_url": _get_site_url(),
    }


def _build_ics_url(appointment) -> str | None:
    try:
        ics_path = reverse("rdv_ics_download", kwargs={"rdv_id": appointment.id})
        return _abs_url(ics_path)
    except NoReverseMatch:
        return _abs_url(f"/site/rdv/ics/{appointment.id}/")


# -----------------------------
# Email logging (DB)
# -----------------------------

def _log_email(
    *,
    kind: str,
    to_email: str,
    subject: str,
    appointment_id: int | None,
    status: str,
    error_message: str = "",
    template: str = "",
    has_ics: bool = False,
) -> None:
    try:
        EmailLog.objects.create(
            kind=kind,
            to_email=to_email,
            subject=subject,
            appointment_id=appointment_id,
            status=status,
            error_message=error_message or "",
            template=template or "",
            has_ics=has_ics,
        )
    except Exception:
        logger.exception("EmailLog create failed")


def _send_html_email(
    *,
    subject: str,
    to_email: str,
    text_body: str,
    html_template: str,
    ctx: dict,
    attach_ics: bool = False,
    ics_filename: str = "rdv.ics",
    ics_content: str | None = None,

    # ✅ NEW (optionnels => pas de TypeError)
    kind: str = "GENERIC",
    appointment_id: int | None = None,
) -> None:
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "Wassaya <no-reply@wassaya.local>")
    html_body = render_to_string(html_template, ctx)

    message = EmailMultiAlternatives(subject, text_body, from_email, [to_email])
    message.attach_alternative(html_body, "text/html")

    if attach_ics:
        if not ics_content:
            ics_content = "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n"
        message.attach(ics_filename, ics_content, "text/calendar; charset=utf-8")

    try:
        message.send(fail_silently=False)
        _log_email(
            kind=kind,
            to_email=to_email,
            subject=subject,
            appointment_id=appointment_id,
            status="SENT",
            template=html_template,
            has_ics=attach_ics,
        )
    except Exception as e:
        logger.exception("Email send failed (to=%s subject=%s)", to_email, subject)
        _log_email(
            kind=kind,
            to_email=to_email,
            subject=subject,
            appointment_id=appointment_id,
            status="FAILED",
            error_message=str(e),
            template=html_template,
            has_ics=attach_ics,
        )


# -----------------------------
# Notifications (patient)
# -----------------------------
def notify_appointment_created(appointment) -> None:
    """
    Email au patient quand il crée une demande (PENDING).
    (Pas besoin d’ICS ici)
    """
    patient_user = getattr(getattr(appointment, "patient", None), "user", None)
    patient_email = _safe_email(getattr(patient_user, "email", None))
    if not patient_email:
        return

    ctx = _base_ctx(appointment)
    badge_bg, badge_color = _badge_for_status("PENDING")

    try:
        dashboard_url = _abs_url(reverse("patient_rdvs"))
    except NoReverseMatch:
        dashboard_url = _abs_url("/site/patient/rdv/")

    ctx.update(
        {
            "email_title": "Demande de rendez-vous",
            "badge_text": "PENDING",
            "badge_bg": badge_bg,
            "badge_color": badge_color,
            "dashboard_url": dashboard_url,
        }
    )

    subject = "Wassaya - Demande de RDV (PENDING)"
    text_body = (
        "Votre demande de rendez-vous a été reçue.\n\n"
        f"Médecin: Dr {ctx['doctor_name']}\n"
        f"Date: {ctx['dt']}\n"
        "Statut: PENDING\n\n"
        "Merci."
    )

    _send_html_email(
        subject=subject,
        to_email=patient_email,
        text_body=text_body,
        html_template="email/appointment_created.html",
        ctx=ctx,
        attach_ics=False,                 # ✅ pas d’ICS ici
        kind="APPOINTMENT_CREATED",       # ✅ pour EmailLog
        appointment_id=appointment.id,    # ✅ pour EmailLog
    )




def notify_appointment_status(appointment) -> None:
    patient_user = getattr(getattr(appointment, "patient", None), "user", None)
    patient_email = _safe_email(getattr(patient_user, "email", None))
    if not patient_email:
        return

    status = (getattr(appointment, "status", "") or "").upper()
    badge_bg, badge_color = _badge_for_status(status)

    ctx = _base_ctx(appointment)
    ctx.update(
        {
            "email_title": "Mise à jour de votre rendez-vous",
            "badge_text": status,
            "badge_bg": badge_bg,
            "badge_color": badge_color,
            "status": status,
        }
    )

    attach = (status == "CONFIRMED")
    ctx["ics_url"] = _build_ics_url(appointment) if attach else None

    subject = f"Wassaya - RDV {status}"
    text_body = (
        "Votre rendez-vous a été mis à jour.\n\n"
        f"Médecin: Dr {ctx['doctor_name']}\n"
        f"Date: {ctx['dt']}\n"
        f"Nouveau statut: {status}\n\n"
        "Merci."
    )

    ics_filename = f"rdv_{appointment.id}.ics" if attach else "rdv.ics"
    ics_content = appointment_to_ics(appointment) if attach else None

    _send_html_email(
        kind="APPOINTMENT_STATUS",
        appointment_id=appointment.id,
        subject=subject,
        to_email=patient_email,
        text_body=text_body,
        html_template="email/appointment_status.html",
        ctx=ctx,
        attach_ics=attach,
        ics_filename=ics_filename,
        ics_content=ics_content,
    )


def notify_appointment_cancelled(appointment) -> None:
    patient_user = getattr(getattr(appointment, "patient", None), "user", None)
    patient_email = _safe_email(getattr(patient_user, "email", None))
    if not patient_email:
        return

    ctx = _base_ctx(appointment)
    badge_bg, badge_color = _badge_for_status("CANCELLED")

    try:
        booking_url = _abs_url(reverse("doctor_list"))
    except NoReverseMatch:
        booking_url = _abs_url("/site/doctors/")

    ctx.update(
        {
            "email_title": "Annulation de rendez-vous",
            "badge_text": "CANCELLED",
            "badge_bg": badge_bg,
            "badge_color": badge_color,
            "booking_url": booking_url,
        }
    )

    subject = "Wassaya - RDV annulé"
    text_body = (
        "Votre rendez-vous a été annulé.\n\n"
        f"Médecin: Dr {ctx['doctor_name']}\n"
        f"Date: {ctx['dt']}\n\n"
        "Merci."
    )

    _send_html_email(
        kind="APPOINTMENT_CANCELLED",
        appointment_id=appointment.id,
        subject=subject,
        to_email=patient_email,
        text_body=text_body,
        html_template="email/appointment_cancelled.html",
        ctx=ctx,
        attach_ics=False,
    )


# -----------------------------
# Notifications (doctor)
# -----------------------------
def notify_doctor_new_request(appointment) -> None:
    """
    Email au médecin quand un patient crée une demande (PENDING).
    """
    doctor_user = getattr(getattr(appointment, "doctor", None), "user", None)
    doctor_email = _safe_email(getattr(doctor_user, "email", None))
    if not doctor_email:
        return

    ctx = _base_ctx(appointment)
    badge_bg, badge_color = _badge_for_status("PENDING")

    try:
        doctor_rdvs_url = _abs_url(reverse("doctor_rdvs"))
    except NoReverseMatch:
        doctor_rdvs_url = _abs_url("/site/doctor/rdv/")

    try:
        confirm_url = _abs_url(reverse("doctor_confirm_rdv", kwargs={"rdv_id": appointment.id}))
    except NoReverseMatch:
        confirm_url = _abs_url(f"/site/doctor/rdv/confirm/{appointment.id}/")

    try:
        reject_url = _abs_url(reverse("doctor_reject_rdv", kwargs={"rdv_id": appointment.id}))
    except NoReverseMatch:
        reject_url = _abs_url(f"/site/doctor/rdv/reject/{appointment.id}/")

    patient_user = getattr(getattr(appointment, "patient", None), "user", None)
    patient_name = _fullname_or_username(patient_user)

    ctx.update(
        {
            "email_title": "Nouvelle demande de rendez-vous",
            "badge_text": "PENDING",
            "badge_bg": badge_bg,
            "badge_color": badge_color,
            "patient_name": patient_name,
            "doctor_rdvs_url": doctor_rdvs_url,
            "confirm_url": confirm_url,
            "reject_url": reject_url,
        }
    )

    subject = "Wassaya - Nouvelle demande de RDV"
    text_body = (
        "Nouvelle demande de rendez-vous.\n\n"
        f"Patient: {patient_name}\n"
        f"Date: {ctx['dt']}\n"
        f"Motif: {ctx['reason'] or '-'}\n\n"
        f"Voir: {doctor_rdvs_url}\n"
    )

    _send_html_email(
        kind="DOCTOR_NEW_REQUEST",
        appointment_id=appointment.id,
        subject=subject,
        to_email=doctor_email,
        text_body=text_body,
        html_template="email/doctor_new_request.html",
        ctx=ctx,
        attach_ics=False,
    )

def notify_appointment_reminder(appointment, reminder_label: str) -> None:
    patient_user = getattr(getattr(appointment, "patient", None), "user", None)
    patient_email = _safe_email(getattr(patient_user, "email", None))
    if not patient_email:
        return

    ctx = _base_ctx(appointment)
    ctx.update({
        "email_title": "Rappel de rendez-vous",
        "reminder_label": reminder_label,
        "dashboard_url": _abs_url(reverse("patient_rdvs")),
    })

    subject = f"Wassaya - Rappel RDV ({reminder_label})"
    text_body = (
        f"Rappel : vous avez un rendez-vous {reminder_label}.\n\n"
        f"Médecin: Dr {ctx['doctor_name']}\n"
        f"Date: {ctx['dt']}\n"
        "Merci."
    )

    # ✅ kind explicite selon le label (ou tu peux le passer en param)
    kind = "APPOINTMENT_REMINDER_24H" if "24" in reminder_label else "APPOINTMENT_REMINDER_1H"

    _send_html_email(
        subject=subject,
        to_email=patient_email,
        text_body=text_body,
        html_template="email/appointment_reminder.html",
        ctx=ctx,
        attach_ics=False,
        kind=kind,                         # ✅
        appointment_id=appointment.id,      # ✅

    )



# EXPL: Fin de email_service.py