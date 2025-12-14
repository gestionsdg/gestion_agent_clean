# personnel/views_dashboard.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Count, Q
import logging

from .models import Employe

log = logging.getLogger(__name__)


@login_required(login_url='connexion')  # ✅ force la redirection vers /connexion/
def tableau_de_bord(request):
    """
    Tableau de bord principal.
    - Utilise les libellés EXACTS de statut fournis
    - Calcule toutes les métriques en une seule agrégation (Count + filter)
    - Conserve les alias attendus par dashboard.html
    """
    qs = Employe.objects.all()

    counts = qs.aggregate(
        total=Count("pk"),
        actifs=Count("pk", filter=Q(statut="Actif")),
        retraites=Count("pk", filter=Q(statut="Mise à la retraite")),
        licencies=Count("pk", filter=Q(statut="Licencié")),
        decedes=Count("pk", filter=Q(statut="Décédé")),
        demissionnaires=Count("pk", filter=Q(statut="Démission")),
        en_detachement=Count("pk", filter=Q(statut="En détachement")),
        en_disponibilite=Count("pk", filter=Q(statut="Mise en disponibilité")),
    )

    ctx = dict(counts)
    # Alias utilisés dans le template dashboard.html
    ctx.update({
        "total_agents": ctx.get("total", 0),
        "agents_ayant_ete_licencies": ctx.get("licencies", 0),
        "is_admin_rh": bool(
            getattr(request.user, "is_superuser", False)
            or request.user.groups.filter(name="Administrateur RH").exists()
        ),
    })

    try:
        log.info("DASHBOARD_CTX %s", {k: v for k, v in ctx.items()})
    except Exception:
        # En cas de type non sérialisable, on ignore simplement le log
        pass

    # 🔎 Vérifie que ton template existe. Si tu utilises 'personnel/dashboard.html',
    # remplace simplement la ligne ci-dessous par: return render(request, "personnel/dashboard.html", ctx)
    return render(request, "dashboard.html", ctx)


@login_required(login_url='connexion')  # ✅ idem : protection explicite
def total_agents_view(request):
    """
    /employes/total/ — liste paginée.
    N.B. : Cette vue n'est utilisée que si mappée dans urls.py.
           Si votre route /employes/total/ pointe déjà vers views_export.total_agents,
           vous pouvez conserver celle-ci comme fallback.
    Template : 'personnel/total_agents.html'
    """
    from django.core.paginator import Paginator
    agents = Employe.objects.all().order_by("nom")
    paginator = Paginator(agents, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "personnel/total_agents.html", {"page_obj": page_obj})
