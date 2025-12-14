# personnel/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import logout
from django.http import HttpResponse
from django.contrib import messages

from .models import Employe  # ✅ import global du modèle


# ============================================================
# Redirections & Authentification
# ============================================================

# 🔄 Redirection depuis l'admin vers la liste des employés
@login_required
def redirection_vers_liste_employes(request):
    # Namespacé pour éviter toute ambiguïté de reverse
    return redirect('personnel:liste_employes')


# 🚪 Déconnexion (protégée pour cohérence UX)
@login_required
def logout_view(request):
    logout(request)
    # Conforme aux réglages LOGIN_URL / LOGOUT_REDIRECT_URL
    return redirect('connexion')  # (au lieu de 'login')


# ============================================================
# Liste des employés (WEB) avec filtres
# ============================================================
@login_required
def liste_employes(request):
    query = request.GET.get('q', '')
    grade = request.GET.get('grade', '')
    entite = request.GET.get('entite', '')
    statut = request.GET.get('statut', '')

    employes = Employe.objects.all().order_by('nom')

    if query:
        employes = (
            employes.filter(nom__icontains=query)
            | employes.filter(prenom__icontains=query)
            | employes.filter(matricule__icontains=query)
        )

    if grade:
        employes = employes.filter(grade_actuel=grade)
    if entite:
        employes = employes.filter(entite=entite)
    if statut:
        employes = employes.filter(statut=statut)

    paginator = Paginator(employes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    grades = (
        Employe.objects.values_list('grade_actuel', flat=True)
        .distinct()
        .order_by('grade_actuel')
    )
    entites = (
        Employe.objects.values_list('entite', flat=True)
        .distinct()
        .order_by('entite')
    )
    statuts = (
        Employe.objects.values_list('statut', flat=True)
        .distinct()
        .order_by('statut')
    )

    context = {
        'page_obj': page_obj,
        'query': query,
        'grade': grade,
        'entite': entite,
        'statut': statut,
        'grades': grades,
        'entites': entites,
        'statuts': statuts,
    }
    return render(request, 'personnel/liste_employes.html', context)


# ➕ Ajouter un employé
@login_required
@permission_required('personnel.add_employe', raise_exception=True)
def ajouter_employe(request):
    from .forms import EmployeForm

    if request.method == "POST":
        form = EmployeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "L’employé a bien été ajouté.")
            return redirect('personnel:liste_employes')
    else:
        form = EmployeForm()
    return render(request, 'personnel/ajouter_employe.html', {'form': form})


# ✏️ Modifier un employé
@login_required
@permission_required('personnel.change_employe', raise_exception=True)
def modifier_employe(request, pk):
    from .forms import EmployeForm

    employe = get_object_or_404(Employe, pk=pk)
    if request.method == "POST":
        form = EmployeForm(request.POST, request.FILES, instance=employe)
        if form.is_valid():
            form.save()
            messages.success(request, "Les modifications ont été enregistrées.")
            return redirect('personnel:liste_employes')
    else:
        form = EmployeForm(instance=employe)
    return render(request, 'personnel/modifier_employe.html', {'form': form, 'employe': employe})


# 🏠 Tableau de bord (version simple – peut être peu utilisée car tu as tableau_de_bord dans views_dashboard)
@login_required
def dashboard(request):
    return render(request, 'accueil.html')


# 🏠 Alias "accueil" (protégé) — utile si des URLs historiques l'utilisent
@login_required
def accueil(request):
    return render(request, 'accueil.html')


# ============================================================
# Effectif par grade (HTML)
# ============================================================
@login_required
def effectif_detaille_par_grade(request):
    """
    Affiche, pour une entité choisie, l'effectif par grade avec :
      - data : liste de dicts {'numero', 'grade', 'effectif'}
      - donnees : alias de data (compatibilité anciens templates)
      - total_general : somme des effectifs
      - titre : 'Effectif des Agents par Grade : {entité}'
    """

    GRADES_ORDONNES = [
        "Directeur", "Sous-Directeur", "Chef de Division", "Chef de Sce Ppal", "Chef de Service",
        "Chef de Sce Adjt", "Chef de Section", "Rédacteur Ppal", "Rédacteur", "Rédacteur Adjt",
        "Commis Chef", "Commis Ppal", "Commis", "Commis Adjt", "Agent Aux 1ère Cl",
        "Agent Aux 2è Cl", "Manœuvre Sp", "Manœuvre Lourd", "Manœuvre Ord",
    ]

    # Entités pour le <select>
    entites = (
        Employe.objects
        .values_list('entite', flat=True)
        .exclude(entite__isnull=True)
        .exclude(entite__exact='')
        .distinct()
        .order_by('entite')
    )

    entite_choisie = (request.GET.get("entite") or "").strip()

    # Valeurs par défaut pour éviter toute VariableDoesNotExist dans le template
    data = []
    total_general = 0
    titre = ""

    if entite_choisie:
        for idx, grade in enumerate(GRADES_ORDONNES, start=1):
            count = Employe.objects.filter(
                entite=entite_choisie, grade_actuel=grade
            ).count()
            data.append({"numero": idx, "grade": grade, "effectif": count})
            total_general += count

        titre = f"Effectif des Agents par Grade : {entite_choisie}"

    context = {
        "titre": titre if entite_choisie else "",
        "data": data,                 # nom "officiel"
        "donnees": data,              # alias pour anciens templates
        "total_general": total_general,
        "entites": entites,
        "entite_choisie": entite_choisie,
    }
    return render(request, "personnel/effectif_par_grade.html", context)


# ============================================================
# Liste totale des agents (WEB) pour total_agents.html
# ============================================================
@login_required
def liste_total_agents(request):
    """
    Vue web pour total_agents.html
    Utilisée par :
      - URL name='liste_total_agents' (personnel/urls.py)
      - Template dashboard.html (carte 'Total Agents')
    """
    employes = Employe.objects.all().order_by("nom", "prenom")
    paginator = Paginator(employes, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
    }
    return render(request, "personnel/total_agents.html", context)


# ============================================================
# Gestion des permissions refusées
# ============================================================
# ⚠️ Vue publique (exemptée du middleware) : ne pas mettre @login_required
def custom_permission_denied_view(request, exception=None):
    return render(request, 'personnel/acces_refuse.html', {
        'message': "⛔ Vous n’avez pas la permission d’accéder à cette page."
    })


# ============================================================
# Aides: redirection d'accueil + health
# ============================================================
# ⚠️ Vue publique (exemptée du middleware) : ne pas mettre @login_required
def redirection_accueil(request):
    """
    Si tu l'utilises comme route racine dans project/urls.py :
    - Si l'utilisateur est connecté -> 'dashboard'
    - Sinon -> 'connexion'
    """
    if request.user.is_authenticated:
        return redirect('dashboard')   # ✅ correspond au name="dashboard" dans gestion_agent/urls.py
    return redirect('connexion')


# ⚠️ Vue publique (exemptée du middleware) : ne pas mettre @login_required
def health(request):
    return HttpResponse("ok")
