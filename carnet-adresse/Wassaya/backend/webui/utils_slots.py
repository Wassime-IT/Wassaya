# webui/utils_slots.py
from __future__ import annotations

from datetime import timedelta
from typing import List

from django.utils import timezone

from wassaya_rdv.models import Appointment


def round_up_to_step(dt, step_minutes: int = 15):
    """
    Arrondit dt au prochain pas (ex: 15 minutes).
    """
    dt = timezone.localtime(dt)
    minutes = dt.minute
    remainder = minutes % step_minutes
    if remainder == 0 and dt.second == 0 and dt.microsecond == 0:
        return dt.replace(second=0, microsecond=0)
    add = step_minutes - remainder
    dt = dt + timedelta(minutes=add)
    return dt.replace(second=0, microsecond=0)


def build_candidate_slots(
    *,
    start_dt,
    days: int = 7,
    start_hour: int = 9,
    end_hour: int = 18,
    step_minutes: int = 30,
) -> List:
    """
    Génère des créneaux (datetime aware) de start_dt à start_dt+days.
    """
    start_dt = timezone.localtime(start_dt)
    start_dt = round_up_to_step(start_dt, step_minutes=step_minutes)

    slots = []
    current = start_dt
    end_dt = start_dt + timedelta(days=days)

    while current < end_dt:
        local = timezone.localtime(current)
        # uniquement heures de travail
        if start_hour <= local.hour < end_hour:
            slots.append(current)
        current = current + timedelta(minutes=step_minutes)

    return slots


def get_available_slots_for_doctor(
    *,
    doctor,
    start_dt=None,
    days: int = 7,
    start_hour: int = 9,
    end_hour: int = 18,
    step_minutes: int = 30,
    max_results: int = 12,
):
    """
    Retourne une liste de créneaux disponibles (datetime aware).
    """
    if start_dt is None:
        start_dt = timezone.now() + timedelta(minutes=10)

    candidates = build_candidate_slots(
        start_dt=start_dt,
        days=days,
        start_hour=start_hour,
        end_hour=end_hour,
        step_minutes=step_minutes,
    )

    # RDV déjà pris (non annulés / non refusés)
    busy = set(
        Appointment.objects.filter(
            doctor=doctor,
            datetime__gte=timezone.now() - timedelta(days=1),
        )
        .exclude(status__in=["REJECTED", "CANCELLED"])
        .values_list("datetime", flat=True)
    )

    avail = []
    for dt in candidates:
        if dt > timezone.now() and dt not in busy:
            avail.append(dt)
            if len(avail) >= max_results:
                break

    return avail
def format_slot_datetime(dt):
    """
    Formate une datetime aware en chaîne lisible.
    """
    return timezone.localtime(dt).strftime("%d/%m/%Y à %H:%M")