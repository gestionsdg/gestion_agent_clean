from django.shortcuts import render, redirect, get_object_or_404 
from django.core.paginator import Paginator
from .models import Employe
from .forms import EmployeForm  # 👈 important : importer ton formulaire
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib.auth import logout

# 🔄 Vue pour rediriger depuis l’admin vers la liste des employés
@login_required
def redirection_vers_liste_employes(request):
    return redirect('liste_employes')  # Ce nom correspond bien à ta vue principale

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')  # ou l’URL de votre choix après déconnexion
# 🔍 Liste paginée + filtres

@login_required
def liste_employes(request):
    employes = Employe.objects.all().order_by('nom')

    query = request.GET.get('q', '')
    grade = request.GET.get('grade', '')
    entite = request.GET.get('entite', '')
    statut = request.GET.get('statut', '')

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
# ➕ Ajouter un employé
@login_required
def ajouter_employe(request):
    user_groups = request.user.groups.values_list('name', flat=True)
    if 'Lecture seule' in user_groups:
        return render(request, 'personnel/acces_refuse.html', {
            'message': "⛔ Saisie réservée aux utilisateurs pour la mise à jour."
        })

    if request.method == "POST":
        form = EmployeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('liste_employes')
    else:
        form = EmployeForm()

    return render(request, 'personnel/ajouter_employe.html', {'form': form})

# ✏️ Modifier un employé
# ✏️ Modifier un employé
@login_required
def modifier_employe(request, pk):
    user_groups = request.user.groups.values_list('name', flat=True)
    if 'Lecture seule' in user_groups:
        return render(request, 'personnel/acces_refuse.html', {
            'message': "⛔ Modification réservée aux utilisateurs pour la mise à jour."
        })

    employe = get_object_or_404(Employe, pk=pk)

    if request.method == "POST":
        form = EmployeForm(request.POST, request.FILES, instance=employe)
        if form.is_valid():
            form.save()
            return redirect('liste_employes')
    else:
        form = EmployeForm(instance=employe)

    return render(request, 'personnel/modifier_employe.html', {'form': form, 'employe': employe})

def accueil(request):
    return render(request, 'accueil.html')