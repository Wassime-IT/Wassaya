from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from .utils_slots import get_available_slots_for_doctor
from wassaya_rdv.models import EmailLog, Appointment

from wassaya_clinic.models import PatientProfile, DoctorProfile, Speciality

from .forms import RegisterForm, AppointmentForm
from .ics_service import appointment_to_ics
from .email_service import (
    notify_appointment_created,
    notify_appointment_status,
    notify_appointment_cancelled,
    notify_doctor_new_request,
    notify_appointment_reminder,
)


# =========================
# HELPERS
# =========================
def _normalize_dt(dt):
    """
    EXPL: Assure que datetime est timezone-aware.
    Certains widgets/forms peuvent renvoyer un dt naive.
    """
    if dt is None:
        return None
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


# =========================
# PAGES PUBLIQUES
# =========================
def home_page(request):
    """
    EXPL: Page d'accueil du site (HTML).
    """
    return render(request, "webui/home.html")


def doctor_list(request):
    """
    EXPL:
    - Filtre spécialité: ?speciality=<id>
    - Recherche: ?q=<texte>
    - Tri: ?sort=fee_asc|fee_desc|name
    - Pagination: ?page=<n>
    """
    speciality_id = (request.GET.get("speciality") or "").strip()
    q = (request.GET.get("q") or "").strip()
    sort = (request.GET.get("sort") or "name").strip()
    page_number = request.GET.get("page")

    qs = DoctorProfile.objects.filter(is_active=True).select_related("user", "speciality")

    # Filtre spécialité
    if speciality_id.isdigit():
        qs = qs.filter(speciality_id=int(speciality_id))

    # Recherche
    if q:
        qs = qs.filter(
            Q(user__first_name__icontains=q)
            | Q(user__last_name__icontains=q)
            | Q(user__username__icontains=q)
            | Q(speciality__name__icontains=q)
        )

    # Tri
    if sort == "fee_asc":
        qs = qs.order_by("fee", "user__first_name", "user__last_name", "user__username")
    elif sort == "fee_desc":
        qs = qs.order_by("-fee", "user__first_name", "user__last_name", "user__username")
    else:
        qs = qs.order_by("user__first_name", "user__last_name", "user__username")

    # Pagination
    paginator = Paginator(qs, 9)
    page_obj = paginator.get_page(page_number)

    # Spécialités (pour select)
    specialities = Speciality.objects.all().order_by("name")

    # Libellé spécialité sélectionnée (pour chips)
    selected_speciality_name = ""
    if speciality_id.isdigit():
        selected_speciality_name = (
            specialities.filter(id=int(speciality_id)).values_list("name", flat=True).first() or ""
        )

    return render(
        request,
        "webui/doctors_list.html",
        {
            "page_obj": page_obj,
            "doctors": page_obj.object_list,
            "specialities": specialities,
            "selected_speciality": speciality_id,
            "selected_speciality_name": selected_speciality_name,
            "q": q,
            "sort": sort,
        },
    )


def doctor_detail(request, pk):
    """
    EXPL: Détails d'un médecin (profil).
    """
    doctor = get_object_or_404(
        DoctorProfile.objects.select_related("user", "speciality"),
        pk=pk,
        is_active=True,
    )
    return render(request, "webui/doctor_detail.html", {"doctor": doctor})


# =========================
# AUTH (SESSION DJANGO)
# =========================
def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()  # ✅ role forcé dans form.save()
            messages.success(request, "Compte créé avec succès. Vous pouvez vous connecter.")
            return redirect("login_view")
        messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = RegisterForm()

    return render(request, "webui/register.html", {"form": form})


def login_view(request):
    """
    EXPL: Connexion via username/password.
    - authenticate vérifie les identifiants
    - login démarre la session
    - redirection selon role
    """
    error = None

    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)
        if user is None:
            error = "Identifiants incorrects."
            messages.error(request, error)
        else:
            login(request, user)

            if user.role == "DOCTOR":
                return redirect("doctor_dashboard")
            if user.role == "PATIENT":
                return redirect("patient_dashboard")
            return redirect("/admin/")

    return render(request, "webui/login.html", {"error": error})


def logout_view(request):
    """
    EXPL: Déconnexion (session).
    """
    logout(request)
    return redirect("home_page")


# =========================
# DASHBOARDS
# =========================
@login_required
def patient_dashboard(request):
    """
    EXPL: Dashboard patient + stats simples.
    """
    if request.user.role != "PATIENT":
        return redirect("home_page")

    patient_profile, _ = PatientProfile.objects.get_or_create(user=request.user)

    total = Appointment.objects.filter(patient=patient_profile).count()
    pending = Appointment.objects.filter(patient=patient_profile, status="PENDING").count()
    confirmed = Appointment.objects.filter(patient=patient_profile, status="CONFIRMED").count()

    return render(
        request,
        "webui/patient_dashboard.html",
        {"total": total, "pending": pending, "confirmed": confirmed},
    )


@login_required
def doctor_dashboard(request):
    """
    EXPL: Dashboard docteur + stats simples.
    """
    if request.user.role != "DOCTOR":
        return redirect("home_page")

    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)

    total = Appointment.objects.filter(doctor=doctor_profile).count()
    pending = Appointment.objects.filter(doctor=doctor_profile, status="PENDING").count()
    confirmed = Appointment.objects.filter(doctor=doctor_profile, status="CONFIRMED").count()

    return render(
        request,
        "webui/doctor_dashboard.html",
        {"total": total, "pending": pending, "confirmed": confirmed},
    )


# =========================
# RDV (PATIENT)
# =========================
@login_required
def patient_create_rdv(request, doctor_id):
    """
    EXPL: Un patient crée une demande de RDV (PENDING).
    - Vérifie date future
    - Vérifie conflit créneau (doctor + datetime)
    - Propose des créneaux alternatifs (suggested_slots)
    - Envoie email au patient
    """
    if request.user.role != "PATIENT":
        return redirect("home_page")

    doctor = get_object_or_404(DoctorProfile, pk=doctor_id, is_active=True)

    # ✅ min_dt (affiché dans la page)
    min_dt_obj = timezone.localtime(timezone.now() + timezone.timedelta(minutes=10))
    min_dt = min_dt_obj.strftime("%d/%m/%Y %H:%M")

    # ✅ suggestions (affichées dans la page)
    suggested_slots = get_available_slots_for_doctor(
        doctor=doctor,
        start_dt=min_dt_obj,
        days=7,
        start_hour=9,
        end_hour=18,
        step_minutes=30,
        max_results=12,
    )

    if request.method == "POST":
        form = AppointmentForm(request.POST)

        if form.is_valid():
            patient_profile, _ = PatientProfile.objects.get_or_create(user=request.user)
            dt = _normalize_dt(form.cleaned_data["datetime"])

            # 1) date future
            if dt <= timezone.now():
                form.add_error("datetime", "La date doit être dans le futur.")
            else:
                # 2) créneau déjà pris ?
                taken = (
                    Appointment.objects.filter(doctor=doctor, datetime=dt)
                    .exclude(status__in=["REJECTED", "CANCELLED"])
                    .exists()
                )

                if taken:
                    form.add_error("datetime", "Créneau déjà pris. Choisis un créneau suggéré ci-dessous.")
                else:
                    rdv = Appointment.objects.create(
                        doctor=doctor,
                        patient=patient_profile,
                        datetime=dt,
                        reason=form.cleaned_data.get("reason", ""),
                        status=Appointment.Status.PENDING,
                    )

                    notify_appointment_created(rdv)
                    messages.success(request, "Demande de rendez-vous envoyée ✅")
                    return redirect("patient_rdvs")
        else:
            messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = AppointmentForm()

    return render(
        request,
        "webui/patient_create_rdv.html",
        {
            "doctor": doctor,
            "form": form,
            "min_dt": min_dt,
            "suggested_slots": suggested_slots,
        },
    )


@login_required
def patient_rdvs(request):
    """
    EXPL:
    - Onglets: upcoming/past
    - Filtre statut optionnel
    - Tri date_asc/date_desc
    - Pagination séparée
    """
    if request.user.role != "PATIENT":
        return redirect("home_page")

    now = timezone.now()
    tab = (request.GET.get("tab") or "upcoming").strip()  # upcoming | past
    status = (request.GET.get("status") or "").strip()  # "" = tous
    sort = (request.GET.get("sort") or "").strip()  # date_asc | date_desc

    patient_profile, _ = PatientProfile.objects.get_or_create(user=request.user)

    base_qs = Appointment.objects.filter(patient=patient_profile).select_related(
        "doctor__user", "doctor__speciality"
    )

    if status:
        base_qs = base_qs.filter(status=status)

    upcoming_qs = base_qs.filter(datetime__gte=now)
    past_qs = base_qs.filter(datetime__lt=now)

    if sort == "date_desc":
        upcoming_qs = upcoming_qs.order_by("-datetime")
        past_qs = past_qs.order_by("-datetime")
    else:
        upcoming_qs = upcoming_qs.order_by("datetime")
        past_qs = past_qs.order_by("-datetime")  # historique: récent d'abord

    page_up = request.GET.get("page_up")
    page_past = request.GET.get("page_past")

    upcoming_page = Paginator(upcoming_qs, 6).get_page(page_up)
    past_page = Paginator(past_qs, 6).get_page(page_past)

    return render(
        request,
        "webui/patient_rdvs.html",
        {
            "now": now,
            "active_tab": tab,
            "status": status,
            "sort": (sort or "date_asc"),
            "upcoming_page": upcoming_page,
            "past_page": past_page,
        },
    )


@login_required
def patient_cancel_rdv(request, rdv_id):
    """
    EXPL: Annulation RDV côté patient.
    - Passe status à CANCELLED (si pas déjà final)
    - Email HTML (annulation)
    """
    if request.user.role != "PATIENT":
        return redirect("home_page")

    patient_profile, _ = PatientProfile.objects.get_or_create(user=request.user)
    rdv = get_object_or_404(Appointment, pk=rdv_id, patient=patient_profile)

    if rdv.status in ["CANCELLED", "REJECTED"]:
        messages.info(request, "Ce rendez-vous est déjà annulé/refusé.")
        return redirect("patient_rdvs")

    rdv.status = Appointment.Status.CANCELLED
    rdv.save()

    # ✅ EMAIL (HTML) annulation
    notify_appointment_cancelled(rdv)

    messages.success(request, "Rendez-vous annulé ✅")
    return redirect("patient_rdvs")


# =========================
# RDV (DOCTOR)
# =========================
@login_required
def doctor_rdvs(request):
    """
    EXPL:
    - Par défaut status=PENDING (utile)
    - Onglets upcoming/past
    - Tri
    - Pagination
    """
    if request.user.role != "DOCTOR":
        return redirect("home_page")

    now = timezone.now()
    tab = (request.GET.get("tab") or "upcoming").strip()

    # ✅ Par défaut : PENDING only
    status = request.GET.get("status", "PENDING").strip()  # "" = tous
    sort = (request.GET.get("sort") or "").strip()

    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)

    base_qs = Appointment.objects.filter(doctor=doctor_profile).select_related("patient__user")

    if status:
        base_qs = base_qs.filter(status=status)

    upcoming_qs = base_qs.filter(datetime__gte=now)
    past_qs = base_qs.filter(datetime__lt=now)

    if sort == "date_desc":
        upcoming_qs = upcoming_qs.order_by("-datetime")
        past_qs = past_qs.order_by("-datetime")
    else:
        upcoming_qs = upcoming_qs.order_by("datetime")
        past_qs = past_qs.order_by("-datetime")

    page_up = request.GET.get("page_up")
    page_past = request.GET.get("page_past")

    upcoming_page = Paginator(upcoming_qs, 8).get_page(page_up)
    past_page = Paginator(past_qs, 8).get_page(page_past)

    return render(
        request,
        "webui/doctor_rdvs.html",
        {
            "now": now,
            "active_tab": tab,
            "status": status,
            "sort": (sort or "date_asc"),
            "upcoming_page": upcoming_page,
            "past_page": past_page,
        },
    )


@login_required
def doctor_confirm_rdv(request, rdv_id):
    """
    EXPL: Le docteur confirme un RDV.
    - status = CONFIRMED (si PENDING)
    - email HTML au patient (status)
    """
    if request.user.role != "DOCTOR":
        return redirect("home_page")

    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    rdv = get_object_or_404(Appointment, pk=rdv_id, doctor=doctor_profile)

    if rdv.status != "PENDING":
        messages.info(request, "Seuls les RDV en attente peuvent être confirmés.")
        return redirect("doctor_rdvs")

    rdv.status = Appointment.Status.CONFIRMED
    rdv.save()

    # ✅ EMAIL (HTML) status
    notify_appointment_status(rdv)

    messages.success(request, "Rendez-vous confirmé ✅")
    return redirect("doctor_rdvs")


@login_required
def doctor_reject_rdv(request, rdv_id):
    """
    EXPL: Le docteur refuse un RDV.
    - status = REJECTED (si PENDING)
    - email HTML au patient (status)
    """
    if request.user.role != "DOCTOR":
        return redirect("home_page")

    doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
    rdv = get_object_or_404(Appointment, pk=rdv_id, doctor=doctor_profile)

    if rdv.status != "PENDING":
        messages.info(request, "Seuls les RDV en attente peuvent être refusés.")
        return redirect("doctor_rdvs")

    rdv.status = Appointment.Status.REJECTED
    rdv.save()

    # ✅ EMAIL (HTML) status
    notify_appointment_status(rdv)

    messages.success(request, "Rendez-vous refusé ✅")
    return redirect("doctor_rdvs")


# =========================
# RDV ICS DOWNLOAD
# =========================
@login_required
def rdv_ics_download(request, rdv_id):
    """
    EXPL:
    - Télécharge un fichier .ics pour un RDV
    - Sécurité: patient -> son rdv, doctor -> ses rdv
    """
    rdv = get_object_or_404(Appointment, pk=rdv_id)

    if request.user.role == "PATIENT":
        patient_profile, _ = PatientProfile.objects.get_or_create(user=request.user)
        if rdv.patient_id != patient_profile.id:
            return redirect("home_page")

    elif request.user.role == "DOCTOR":
        doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
        if rdv.doctor_id != doctor_profile.id:
            return redirect("home_page")
    else:
        return redirect("home_page")

    ics_content = appointment_to_ics(rdv)

    resp = HttpResponse(ics_content, content_type="text/calendar; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="rdv_{rdv.id}.ics"'
    return resp



@login_required
def patient_email_logs(request):
    """
    Liste des emails liés au patient connecté (via Appointment).
    Filtre simple: status/kind + recherche + pagination.
    """
    if request.user.role != "PATIENT" and not request.user.is_staff:
        return redirect("home_page")

    status = (request.GET.get("status") or "").strip()
    kind = (request.GET.get("kind") or "").strip()
    q = (request.GET.get("q") or "").strip()
    page = request.GET.get("page")

    qs = EmailLog.objects.all().order_by("-created_at")

    if not request.user.is_staff:
        patient_profile, _ = PatientProfile.objects.get_or_create(user=request.user)
        # emails liés à ses RDV (appointment_id)
        patient_appt_ids = Appointment.objects.filter(patient=patient_profile).values_list("id", flat=True)
        qs = qs.filter(appointment_id__in=list(patient_appt_ids))

    if status:
        qs = qs.filter(status=status)
    if kind:
        qs = qs.filter(kind=kind)
    if q:
        qs = qs.filter(
            Q(to_email__icontains=q) |
            Q(subject__icontains=q) |
            Q(error_message__icontains=q) |
            Q(template__icontains=q)
        )

    page_obj = Paginator(qs, 12).get_page(page)

    return render(request, "webui/email_logs_list.html", {
        "page_obj": page_obj,
        "logs": page_obj.object_list,
        "role_label": "Patient",
        "filters": {"status": status, "kind": kind, "q": q},
        "kinds": EmailLog.Kind.choices,
        "statuses": EmailLog.Status.choices,
    })


@login_required
def doctor_email_logs(request):
    """
    Liste des emails liés au docteur connecté (via Appointment).
    """
    if request.user.role != "DOCTOR" and not request.user.is_staff:
        return redirect("home_page")

    status = (request.GET.get("status") or "").strip()
    kind = (request.GET.get("kind") or "").strip()
    q = (request.GET.get("q") or "").strip()
    page = request.GET.get("page")

    qs = EmailLog.objects.all().order_by("-created_at")

    if not request.user.is_staff:
        doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
        doctor_appt_ids = Appointment.objects.filter(doctor=doctor_profile).values_list("id", flat=True)
        qs = qs.filter(appointment_id__in=list(doctor_appt_ids))

    if status:
        qs = qs.filter(status=status)
    if kind:
        qs = qs.filter(kind=kind)
    if q:
        qs = qs.filter(
            Q(to_email__icontains=q) |
            Q(subject__icontains=q) |
            Q(error_message__icontains=q) |
            Q(template__icontains=q)
        )

    page_obj = Paginator(qs, 12).get_page(page)

    return render(request, "webui/email_logs_list.html", {
        "page_obj": page_obj,
        "logs": page_obj.object_list,
        "role_label": "Docteur",
        "filters": {"status": status, "kind": kind, "q": q},
        "kinds": EmailLog.Kind.choices,
        "statuses": EmailLog.Status.choices,
    })


@login_required
def email_log_detail(request, pk):
    """
    Détail d'un log email + (optionnel) RDV associé.
    Sécurité:
    - staff: tout
    - patient: seulement logs liés à ses RDV
    - doctor: seulement logs liés à ses RDV
    """
    log = get_object_or_404(EmailLog, pk=pk)

    appt = None
    if log.appointment_id:
        appt = get_object_or_404(Appointment, pk=log.appointment_id)

        if request.user.is_staff:
            pass
        elif request.user.role == "PATIENT":
            patient_profile, _ = PatientProfile.objects.get_or_create(user=request.user)
            if appt.patient_id != patient_profile.id:
                return redirect("home_page")
        elif request.user.role == "DOCTOR":
            doctor_profile = get_object_or_404(DoctorProfile, user=request.user)
            if appt.doctor_id != doctor_profile.id:
                return redirect("home_page")
        else:
            return redirect("home_page")
    else:
        # logs sans RDV => staff only
        if not request.user.is_staff:
            return redirect("home_page")

    return render(request, "webui/email_log_detail.html", {"log": log, "appt": appt})
# =========================
# PAGES PUBLIQUES (SUITE)
def about_page(request):
    return render(request, "webui/about.html")
# (exemples de pages supplémentaires)
def contact_page(request):
    return render(request, "webui/contact.html")
# (exemples de pages supplémentaires)
def privacy_page(request):
    return render(request, "webui/privacy.html")
# ===== EXAMPLE SETTINGS.PY EMAIL CONFIGURATION =====
