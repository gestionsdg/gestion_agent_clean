from django.shortcuts import render
from django.http import HttpResponse
from .models import Employe
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from datetime import date

# 🔧 Ajout local de la fonction calcul_duree
def calcul_duree(date_debut):
    if not date_debut:
        return "-"
    today = date.today()
    delta = today.year - date_debut.year - ((today.month, today.day) < (date_debut.month, date_debut.day))
    return f"{delta} an" if delta == 1 else f"{delta} ans"

def liste_actifs_cnss(request):
    actifs = Employe.objects.filter(statut="Actif").order_by("nom")
    for emp in actifs:
        emp.duree_affectation = calcul_duree(emp.date_affectation)
    agents = list(enumerate(actifs, 1))
    return render(request, "personnel/liste_actifs_cnss.html", {"agents": agents})

def liste_actifs_cnss_pdf(request):
    actifs = Employe.objects.filter(statut="Actif").order_by("nom")
    for emp in actifs:
        emp.duree_affectation = calcul_duree(emp.date_affectation)
    agents = list(enumerate(actifs, 1))

    html_string = render_to_string("personnel/liste_actifs_cnss_pdf.html", {"agents": agents})
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=actifs_cnss.pdf"

    css = CSS(string='@page { size: A4 landscape; margin: 1cm; }')
    HTML(string=html_string).write_pdf(response, stylesheets=[css])
    return response
