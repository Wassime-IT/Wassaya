from django.apps import AppConfig

class WassayaClinicConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "wassaya_clinic"

    def ready(self):
        """
        EXPL: ready() s’exécute au chargement de l’app.
        Importer signals ici active les receivers.
        """
        import wassaya_clinic.signals  # noqa
# EXPL: Configuration de l'application Wassaya Clinic, avec l'activation des signaux lors du chargement.
