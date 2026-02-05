from django import forms
from django.contrib.auth import get_user_model

from wassaya_rdv.models import Appointment

User = get_user_model()


class RegisterForm(forms.ModelForm):
    """
    Inscription publique:
    - role forcé à PATIENT (pas de champ role dans le form)
    - password + password2
    """

    password = forms.CharField(widget=forms.PasswordInput, min_length=6, label="Mot de passe")
    password2 = forms.CharField(widget=forms.PasswordInput, min_length=6, label="Confirmation")

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]  # ✅ role supprimé

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        return username

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("password")
        p2 = cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Les mots de passe ne correspondent pas.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])

        # ✅ FORCER le rôle PATIENT (même si quelqu'un bidouille le POST)
        user.role = "PATIENT"

        if commit:
            user.save()
        return user


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["datetime", "reason"]
        widgets = {
            "datetime": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "form-control"},
                format="%Y-%m-%dT%H:%M",
            ),
            "reason": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Décrivez brièvement le motif de votre rendez-vous..., Ex: consultation de suivi, nouvelle douleur, renouvellement d'ordonnance, etc."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["datetime"].input_formats = ["%Y-%m-%dT%H:%M"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Pour que la valeur initiale s’affiche correctement dans <input type="datetime-local">
        self.fields["datetime"].input_formats = ["%Y-%m-%dT%H:%M"]

        # Labels
        self.fields["datetime"].label = "Date & heure"
        self.fields["reason"].label = "Motif"


# EXPL: Formulaire d'inscription pour les utilisateurs avec les champs username, email, rôle et mot de passe.
