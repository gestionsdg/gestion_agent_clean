# personnel/views_actifs.py
from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from weasyprint import HTML, CSS

from .models import Employe


# 🔧 Durée simple en années révolues depuis une date (ou "-")
def calcul_duree(date_debut):
    if not date_debut:
        return "-"
    today = date.today()
    delta = (
        today.year
        - date_debut.year
        - ((today.month, today.day) < (date_debut.month, date_debut.day))
    )
    return f"{delta} an" if delta == 1 else f"{delta} ans"


@login_required
def liste_actifs_cnss(request):
    """
    Liste HTML des agents Actifs, triés par nom.
    """
    actifs = Employe.objects.filter(statut="Actif").order_by("nom")
    for emp in actifs:
        emp.duree_affectation = calcul_duree(emp.date_affectation)
    agents = list(enumerate(actifs, start=1))
    return render(request, "personnel/liste_actifs_cnss.html", {"agents": agents})


@login_required
def liste_actifs_cnss_pdf(request):
    """
    Version PDF de la liste des agents Actifs.
    """
    actifs = Employe.objects.filter(statut="Actif").order_by("nom")
    for emp in actifs:
        emp.duree_affectation = calcul_duree(emp.date_affectation)
    agents = list(enumerate(actifs, start=1))

    html_string = render_to_string("personnel/liste_actifs_cnss_pdf.html", {"agents": agents})

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="actifs_cnss.pdf"'

    css = CSS(string='@page { size: A4 landscape; margin: 1cm; }')
    HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf(
        response, stylesheets=[css]
    )
    return response
