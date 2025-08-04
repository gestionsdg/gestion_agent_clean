from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import logout

# 🔄 Redirection depuis l'admin vers la liste des employés
@login_required
def redirection_vers_liste_employes(request):
    return redirect('liste_employes')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

# 🔍 Liste paginée + filtres
@login_required
def liste_employes(request):
    from .models import Employe  # ✅ import déplacé ici pour éviter les erreurs au démarrage Render
    query = request.GET.get('q', '')
    grade = request.GET.get('grade', '')
    entite = request.GET.get('entite', '')
    statut = request.GET.get('statut', '')

    employes = Employe.objects.all().order_by('nom')

    if query:
        employes = employes.filter(
            nom__icontains=query
        ) | employes.filter(
            prenom__icontains=query
        ) | employes.filter(
            matricule__icontains=query
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

    grades = Employe.objects.values_list('grade_actuel', flat=True).distinct().order_by('grade_actuel')
    entites = Employe.objects.values_list('entite', flat=True).distinct().order_by('entite')
    statuts = Employe.objects.values_list('statut', flat=True).distinct().order_by('statut')

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
    from .models import Employe  # ✅ Ajout ici si des champs dépendants sont appelés

    if request.method == "POST":
        form = EmployeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('liste_employes')
    else:
        form = EmployeForm()

    return render(request, 'personnel/ajouter_employe.html', {'form': form})

# ✏️ Modifier un employé
@login_required
@permission_required('personnel.change_employe', raise_exception=True)
def modifier_employe(request, pk):
    from .forms import EmployeForm
    from .models import Employe

    employe = get_object_or_404(Employe, pk=pk)

    if request.method == "POST":
        form = EmployeForm(request.POST, request.FILES, instance=employe)
        if form.is_valid():
            form.save()
            return redirect('liste_employes')
    else:
        form = EmployeForm(instance=employe)

    return render(request, 'personnel/modifier_employe.html', {'form': form, 'employe': employe})

# 🏠 Vue accueil
@login_required(login_url='/connexion/')
def accueil(request):
    return render(request, 'accueil.html')

# ===============================
# NOUVELLE VUE : Effectif par grade (HTML)
# ===============================
@login_required
def effectif_detaille_par_grade(request):
    from .models import Employe  # Import ici pour éviter erreurs Render

    GRADES_ORDONNES = [
        "Directeur", "Sous-Directeur", "Chef de Division", "Chef de Sce Ppal", "Chef de Service",
        "Chef de Sce Adjt", "Chef de Section", "Rédacteur Ppal", "Rédacteur", "Rédacteur Adjt",
        "Commis Chef", "Commis Ppal", "Commis", "Commis Adjt", "Agent Aux 1ère Cl",
        "Agent Aux 2è Cl", "Manœuvre Sp", "Manœuvre Lourd", "Manœuvre Ord"
    ]

    # Récupérer les entités
    entites = Employe.objects.values_list('entite', flat=True).distinct()
    entite_choisie = request.GET.get("entite")

    if entite_choisie:
        data = []
        total_general = 0

        for idx, grade in enumerate(GRADES_ORDONNES, start=1):
            count = Employe.objects.filter(entite=entite_choisie, grade_actuel=grade).count()
            data.append({
                "numero": idx,
                "grade": grade,
                "effectif": count
            })
            total_general += count

        return render(request, "personnel/effectif_par_grade.html", {
            "titre": f"Effectif des agents par grade : {entite_choisie}",
            "data": data,
            "total_general": total_general,
            "entites": entites,
            "entite_choisie": entite_choisie
        })
    else:
        return render(request, "personnel/effectif_par_grade.html", {
            "entites": entites
        })

# ===============================
# Gestion des permissions refusées
# ===============================
def custom_permission_denied_view(request, exception=None):
    return render(request, 'personnel/acces_refuse.html', {
        'message': "⛔ Vous n’avez pas la permission d’accéder à cette page."
    })
