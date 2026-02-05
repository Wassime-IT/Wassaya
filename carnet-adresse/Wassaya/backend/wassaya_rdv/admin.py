# wassaya_rdv/admin.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Appointment, EmailLog


# =========================
# EmailLog
# =========================
@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "created_at",
        "kind",
        "to_email",
        "status",
        "subject",
        "has_ics",
        "appointment_link",
        "short_error",
    )
    list_filter = ("kind", "status", "has_ics", "created_at")
    search_fields = ("to_email", "subject", "error_message", "template")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_per_page = 50

    readonly_fields = (
        "created_at",
        "kind",
        "to_email",
        "subject",
        "status",
        "appointment_id",
        "template",
        "has_ics",
        "error_message",
    )

    fieldsets = (
        ("Infos", {"fields": ("created_at", "kind", "status", "to_email", "subject")}),
        ("Lien RDV", {"fields": ("appointment_id", "has_ics")}),
        ("Technique", {"fields": ("template", "error_message")}),
    )

    def appointment_link(self, obj):
        """Lien cliquable vers l'Appointment dans l'admin."""
        if not obj.appointment_id:
            return "-"
        try:
            url = reverse("admin:wassaya_rdv_appointment_change", args=[obj.appointment_id])
            return format_html('<a href="{}">RDV #{}</a>', url, obj.appointment_id)
        except Exception:
            return f"RDV #{obj.appointment_id}"

    appointment_link.short_description = "RDV"

    def short_error(self, obj):
        if not obj.error_message:
            return "-"
        msg = str(obj.error_message)
        return (msg[:80] + "…") if len(msg) > 80 else msg

    short_error.short_description = "Erreur"


# =========================
# Appointment
# =========================
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "datetime",
        "status",
        "doctor",
        "patient",
        "reminder_24h_sent",
        "reminder_1h_sent",
        "emails_count",
    )
    list_filter = ("status", "doctor", "reminder_24h_sent", "reminder_1h_sent")
    search_fields = (
        "doctor__user__username",
        "doctor__user__first_name",
        "doctor__user__last_name",
        "patient__user__username",
        "patient__user__first_name",
        "patient__user__last_name",
    )
    ordering = ("-datetime",)
    date_hierarchy = "datetime"
    list_per_page = 50

    actions = ["reset_reminders_flags"]

    @admin.action(description="Réinitialiser les flags de rappel (24h + 1h)")
    def reset_reminders_flags(self, request, queryset):
        updated = queryset.update(reminder_24h_sent=False, reminder_1h_sent=False)
        self.message_user(request, f"{updated} RDV mis à jour (flags reset).")

    def emails_count(self, obj):
        """Compter les emails liés au RDV (EmailLog.appointment_id)."""
        return EmailLog.objects.filter(appointment_id=obj.id).count()

    emails_count.short_description = "Emails"
    emails_count.admin_order_field = "emails_count"
# EXPL: Fichier d'administration pour l'application wassaya_rdv, incluant la configuration de l'interface d'administration pour les modèles Appointment et EmailLog.
