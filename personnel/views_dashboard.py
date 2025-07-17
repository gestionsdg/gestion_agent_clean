from django.shortcuts import render
from django.contrib.auth.models import Group
from .models import Employe

def tableau_de_bord(request):
    total_employes = Employe.objects.count()
    actifs = Employe.objects.filter(statut='Actif').count()
    retraites = Employe.objects.filter(statut='Mise à la retraite').count()
    decedes = Employe.objects.filter(statut='Décédé').count()
    licences = Employe.objects.filter(statut='Licencié').count()
    demissionnaires = Employe.objects.filter(statut='Démission').count()
    en_detachement = Employe.objects.filter(statut='En détachement').count()
    en_disponibilite = Employe.objects.filter(statut='Mise en disponibilité').count()

    # Vérifie si l'utilisateur est superuser ou membre du groupe Administrateur RH
    is_admin_rh = request.user.is_superuser or request.user.groups.filter(name='Administrateur RH').exists()

    context = {
        'total': total_employes,
        'actifs': actifs,
        'retraites': retraites,
        'decedes': decedes,
        'licences': licences,
        'demissionnaires': demissionnaires,
        'en_detachement': en_detachement,
        'en_disponibilite': en_disponibilite,
        'is_admin_rh': is_admin_rh,  # ← Ajout de cette variable pour le template
    }
    return render(request, 'dashboard.html', context)
