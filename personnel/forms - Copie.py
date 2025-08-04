from django import forms
from .models import Employe
from datetime import datetime

DATE_INPUT_FORMAT = '%d/%m/%Y'
ALL_DATE_FORMATS = ['%d/%m/%Y', '%Y-%m-%d']

class EmployeForm(forms.ModelForm):
    date_naissance = forms.DateField(
        required=False,
        widget=forms.DateInput(format='%d/%m/%Y'),
        input_formats=['%d/%m/%Y', '%Y-%m-%d']
    )
    date_engagement = forms.DateField(
        required=False,
        widget=forms.DateInput(format='%d/%m/%Y'),
        input_formats=['%d/%m/%Y', '%Y-%m-%d']
    )
    date_derniere_promotion = forms.DateField(
        required=False,
        widget=forms.DateInput(format='%d/%m/%Y'),
        input_formats=['%d/%m/%Y', '%Y-%m-%d']
    )
    date_affectation = forms.DateField(
        required=False,
        widget=forms.DateInput(format='%d/%m/%Y'),
        input_formats=['%d/%m/%Y', '%Y-%m-%d']
    )
    date_prise_fonction = forms.DateField(
        required=False,
        widget=forms.DateInput(format='%d/%m/%Y'),
        input_formats=['%d/%m/%Y', '%Y-%m-%d']
    )
    date_statut = forms.DateField(
        required=False,
        widget=forms.DateInput(format='%d/%m/%Y'),
        input_formats=['%d/%m/%Y', '%Y-%m-%d']
    )

    class Meta:
        model = Employe
        fields = [
            'photo', 'nom', 'prenom', 'grade_engagement', 'date_engagement',
            'grade_actuel', 'date_derniere_promotion', 'matricule', 'nom_conjoint',
            'sexe', 'date_naissance', 'niveau_etudes', 'option', 'etat_civil', 'service',
            'date_affectation', 'fonction', 'date_prise_fonction', 'adresse',
            'telephone1', 'telephone2', 'parcours_professionnel', 'formations_suivies',
            'besoin_en_formation', 'statut', 'date_statut', 'entite'
        ]

    def clean(self):
        cleaned_data = super().clean()
        today = datetime.today().date()

        def compute_duration(start_date):
            if start_date:
                delta = today.year - start_date.year - ((today.month, today.day) < (start_date.month, start_date.day))
                return f"{delta} {'ans' if delta > 1 else 'an'}"
            return ""

        cleaned_data['Anc_societé'] = compute_duration(cleaned_data.get('date_engagement'))
        cleaned_data['Anc_grade'] = compute_duration(cleaned_data.get('date_derniere_promotion'))
        cleaned_data['Age'] = compute_duration(cleaned_data.get('date_naissance'))
        cleaned_data['Duree_affectation'] = compute_duration(cleaned_data.get('date_affectation'))
        cleaned_data['Duree_prise_fonction'] = compute_duration(cleaned_data.get('date_prise_fonction'))
        cleaned_data['Duree_statut'] = compute_duration(cleaned_data.get('date_statut'))

        return cleaned_data
