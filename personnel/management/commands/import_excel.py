from django.core.management.base import BaseCommand
import pandas as pd
from personnel.models import Employe
from datetime import datetime

class Command(BaseCommand):
    help = "Importer les employés depuis un fichier Excel avec vérification des doublons par matricule"

    def add_arguments(self, parser):
        parser.add_argument('fichier_excel', type=str, help='Chemin du fichier Excel à importer')

    def nettoyer_date(self, valeur):
        """Nettoyer et convertir les dates"""
        if valeur in [None, '-', '–', '—', '“–”', '”-”', 'nan', '']:
            return None
        if isinstance(valeur, str):
            valeur = valeur.strip()
            if valeur in ['', '-', '–', '—']:
                return None
        try:
            if isinstance(valeur, datetime):
                return valeur.date()
            return datetime.strptime(str(valeur), "%Y-%m-%d").date()
        except:
            return None

    def nettoyer_texte(self, valeur, remplacement="Inconnu"):
        """Nettoyer texte et remplacer les valeurs invalides"""
        if valeur in [None, '-', '–', '—', '“–”', '”-”', 'nan', '']:
            return remplacement
        return str(valeur).strip()

    def handle(self, *args, **kwargs):
        fichier_excel = kwargs['fichier_excel']
        try:
            df = pd.read_excel(fichier_excel)
            df = df.where(pd.notnull(df), None)

            # Récupérer les matricules existants pour éviter les doublons
            matricules_existants = set(Employe.objects.values_list('matricule', flat=True))

            employes_a_creer = []
            lignes_ignorees = 0

            for _, row in df.iterrows():
                matricule = self.nettoyer_texte(row['matricule'], None)

                # Vérifier doublon
                if matricule in matricules_existants:
                    lignes_ignorees += 1
                    continue

                employes_a_creer.append(Employe(
                    nom=self.nettoyer_texte(row['nom'], "Inconnu"),
                    prenom=self.nettoyer_texte(row['prenom'], "Inconnu"),
                    matricule=matricule,
                    sexe=self.nettoyer_texte(row['sexe'], "Inconnu"),
                    date_naissance=self.nettoyer_date(row['date_naissance']),
                    grade_engagement=row['grade_engagement'],
                    date_engagement=self.nettoyer_date(row['date_engagement']),
                    grade_actuel=row['grade_actuel'],
                    date_derniere_promotion=self.nettoyer_date(row['date_derniere_promotion']),
                    etat_civil=row['etat_civil'],
                    nom_conjoint=row['nom_conjoint'],
                    adresse=row['adresse'],
                    entite=row['entite'],
                    niveau_etudes=row['niveau_etudes'],
                    option=row['option'],
                    service=row['service'],
                    date_affectation=self.nettoyer_date(row['date_affectation']),
                    annee_affectation=row['annee_affectation'],
                    fonction=row['fonction'],
                    date_prise_fonction=self.nettoyer_date(row['date_prise_fonction']),
                    statut=row['statut'],
                    date_statut=self.nettoyer_date(row['date_statut']),
                    date_fin_disponibilite=self.nettoyer_date(row['date_fin_disponibilite']),
                    date_fin_detachement=self.nettoyer_date(row['date_fin_detachement']),
                    telephone1=row['telephone1'],
                    telephone2=row['telephone2'],
                    photo=row['photo'],
                    parcours_professionnel=row['parcours_professionnel'],
                    formations_suivies=row['formations_suivies'],
                    besoin_en_formation=row['besoin_en_formation']
                ))

            # Import par lots de 500
            BATCH_SIZE = 500
            total = len(employes_a_creer)
            for i in range(0, total, BATCH_SIZE):
                Employe.objects.bulk_create(employes_a_creer[i:i+BATCH_SIZE])
                self.stdout.write(self.style.SUCCESS(f"Importé {min(i+BATCH_SIZE, total)}/{total} employés"))

            self.stdout.write(self.style.SUCCESS(
                f"Importation terminée : {total} nouveaux employés ajoutés, {lignes_ignorees} ignorés (doublons)."
            ))

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.stdout.write(self.style.ERROR(f"Erreur lors de l'importation : {e}"))
