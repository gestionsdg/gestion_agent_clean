from django.shortcuts import render
from django.contrib.auth.models import Group
from .models import Employe
from django.core.paginator import Paginator

def tableau_de_bord(request):
    total_employes = Employe.objects.count()
    actifs = Employe.objects.filter(statut='Actif').count()
    retraites = Employe.objects.filter(statut='Mise à la retraite').count()
    decedes = Employe.objects.filter(statut='Décédé').count()
    agents_ayant_ete_licencies = Employe.objects.filter(statut='Licencié').count()  # Nouveau calcul
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
        'agents_ayant_ete_licencies': agents_ayant_ete_licencies,  # Nouveau champ
        'demissionnaires': demissionnaires,
        'en_detachement': en_detachement,
        'en_disponibilite': en_disponibilite,
        'is_admin_rh': is_admin_rh,
    }
    return render(request, 'dashboard.html', context)
 
def total_agents_view(request):
    agents = Employe.objects.all().order_by('nom')

    paginator = Paginator(agents, 50)  # pagine 50 par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'total_agents.html', {'page_obj': page_obj})
