from datetime import date
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
    return texte.replace(" ans ans", " ans").replace(" an ans", " an").replace(" an an", " an")
# --------------------------------

# ... (tout le reste de ton fichier inchangé jusqu'à la fonction liste_licencies_pdf)

def liste_licencies_pdf(request):
    agents = Employe.objects.filter(statut="Licencié").order_by("nom")
    donnees = []
    for i, agent in enumerate(agents, start=1):
        donnee = [
            i,
            agent.nom,
            agent.matricule,
            agent.grade_actuel,
            agent.sexe,
            agent.date_engagement,
            agent.date_statut,
            # --- Correction appliquée ici ---
            nettoyer_unite_ans(format_duree(calcul_duree_detaillee(agent.date_engagement))),
            # --------------------------------
            agent.entite
        ]
        donnees.append(donnee)

    html_string = render_to_string("personnel/liste_licencies_pdf.html", {
        "titre": "Liste des Agents Licenciés",
        "colonnes": ["N°", "Nom", "Matricule", "Grade actuel", "Sexe", "Date engagement", "Date licenciement", "Carrière", "Entité"],
        "donnees": donnees,
    })

    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    css = CSS(string='@page { size: landscape; }')
    pdf = html.write_pdf(stylesheets=[css])
    return HttpResponse(pdf, content_type='application/pdf')

# ... (tout le reste de ton fichier reste inchangé)
