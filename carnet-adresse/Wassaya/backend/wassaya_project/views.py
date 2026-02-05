from django.http import JsonResponse

def home(request):
    return JsonResponse({
        "message": "Wassaya API is running",
        "endpoints": ["/admin/", "/api/auth/", "/api/clinic/", "/api/rdv/"]
    })
# EXPL: Vue pour la route racine du projet.
