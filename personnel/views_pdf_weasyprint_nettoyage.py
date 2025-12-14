from datetime import date
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string, get_template
from django.http import HttpResponse
from django.utils.dateformat import DateFormat
from django.utils.timezone import now
from weasyprint import HTML, CSS
from django.db.models import Q, Count
from .models import Employe
from .utils import calcul_duree_detaillee, format_duree
from collections import defaultdict
from io import BytesIO
import tempfile

# --- Correction ajoutée ici ---
def nettoyer_unite_ans(texte):
    """
    Supprime les doublons 'ans ans' ou 'an ans' dans les chaînes générées
    par format_duree().
    """
    if not texte:
        return "-"
    return (texte
            .replace(" ans ans", " ans")
            .replace(" an ans", " an")
            .replace(" an an", " an"))
# --------------------------------

# ... (tout le reste de ton fichier inchangé jusqu'à la fonction liste_licencies_pdf)

@login_required
def liste_licencies_pdf(request):
    agents = Employe.objects.filter(statut="Licencié").order_by("nom")

    donnees = []
    for i, agent in enumerate(agents, start=1):
        # Carrière = durée entre engagement et date de licenciement (si les 2 existent)
        carriere = "-"
        if agent.date_engagement and agent.date_statut:
            carriere = nettoyer_unite_ans(
                format_duree(
                    calcul_duree_detaillee(agent.date_engagement, agent.date_statut)
                )
            )

        donnee = [
            i,
            agent.nom or "-",
            agent.matricule or "-",
            agent.grade_actuel or "-",
            agent.sexe or "-",
            agent.date_engagement.strftime("%d/%m/%Y") if agent.date_engagement else "-",
            agent.date_statut.strftime("%d/%m/%Y") if agent.date_statut else "-",
            carriere,
            agent.entite or "-",
        ]
        donnees.append(donnee)

    html_string = render_to_string(
        "personnel/liste_licencies_pdf.html",
        {
            "titre": "Liste des Agents Licenciés",
            "colonnes": [
                "N°", "Nom", "Matricule", "Grade actuel", "Sexe",
                "Date engagement", "Date licenciement", "Carrière", "Entité"
            ],
            "donnees": donnees,
        }
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="liste_licencies.pdf"'
    css = CSS(string='@page { size: A4 landscape; }')

    # base_url pour que WeasyPrint résolve correctement les chemins relatifs (images, css)
    HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf(
        response, stylesheets=[css]
    )
    return response

# ... (tout le reste de ton fichier reste inchangé)
