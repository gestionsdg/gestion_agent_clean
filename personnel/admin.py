# personnel/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Employe

# ---- Personnalisation de l’interface d’administration ----
admin.site.site_header = _("Administration CNSS")
admin.site.site_title = _("CNSS - Gestion des employés")
admin.site.index_title = _("Tableau de bord de l’administration")

# ---- Configuration du modèle Employe ----
@admin.register(Employe)
class EmployeAdmin(admin.ModelAdmin):
    list_display = (
        'nom', 'matricule', 'grade_actuel', 'service', 'fonction', 'statut', 'entite'
    )
    list_filter = ('grade_actuel', 'entite', 'statut', 'sexe')
    search_fields = ('nom', 'prenom', 'matricule')
    ordering = ('nom',)

    fieldsets = (
        (None, {
            'fields': ('nom', 'prenom', 'matricule', 'photo', 'sexe', 'date_naissance')
        }),
        ('Engagement', {
            'fields': ('grade_engagement', 'date_engagement')
        }),
        ('Grade actuel et promotion', {
            'fields': ('grade_actuel', 'date_derniere_promotion')
        }),
        ('Affectation', {
            'fields': ('entite', 'service', 'date_affectation', 'annee_affectation')
        }),
        ('Fonction', {
            'fields': ('fonction', 'date_prise_fonction')
        }),
        ('État civil', {
            'fields': ('etat_civil', 'nom_conjoint', 'adresse')
        }),
        ('Formation & parcours', {
            'fields': ('niveau_etudes', 'option', 'formations_suivies', 'besoin_en_formation')
        }),
        ('Statut', {
            'fields': ('statut', 'date_statut')
        }),
        ('Téléphones', {
            'fields': ('telephone1', 'telephone2')
        }),
        ('Divers', {
            'fields': ('parcours_professionnel',)
        }),
    )
