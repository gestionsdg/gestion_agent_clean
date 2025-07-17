import pandas as pd
from datetime import datetime
from personnel.models import Employe

def convertir_date(valeur):
    if pd.isna(valeur):
        return None
    try:
        return pd.to_datetime(valeur).date()
    except Exception as e:
        print(f"⚠️ Erreur conversion date : {valeur} -> {e}")
        return None

def importer_employes(fichier_excel):
    print("📂 Lecture du fichier Excel en cours...")
    try:
        df = pd.read_excel(fichier_excel, engine="openpyxl")
    except Exception as e:
        print(f"❌ Erreur de lecture du fichier : {e}")
        return

    print("✅ Fichier lu. Lignes chargées :", len(df))

    # Nettoyage des noms de colonnes
    df.columns = [col.strip().lower() for col in df.columns]

    total, erreurs = 0, 0

    for index, row in df.iterrows():
        try:
            matricule = row.get("matricule")
            if pd.isna(matricule) or str(matricule).strip() == "":
                print(f"⏩ Ligne {index+1} ignorée : matricule vide.")
                continue

            Employe.objects.update_or_create(
                matricule=str(matricule).strip(),
                defaults={
                    'nom': str(row.get("nom") or "").strip(),
                    'prenom': str(row.get("prenom") or "").strip(),
                    'sexe': str(row.get("sexe") or "").strip(),
                    'date_naissance': convertir_date(row.get("date_naissance")),
                    'grade_engagement': row.get("grade_engagement"),
                    'date_engagement': convertir_date(row.get("date_engagement")),
                    'grade_actuel': row.get("grade_actuel"),
                    'date_derniere_promotion': convertir_date(row.get("date_derniere_promotion")),
                    'etat_civil': row.get("etat_civil"),
                    'nom_conjoint': row.get("nom_conjoint"),
                    'adresse': row.get("adresse"),
                    'entite': row.get("entite"),
                    'niveau_etudes': row.get("niveau_etudes"),
                    'option': row.get("option"),
                    'service': row.get("service"),
                    'date_affectation': convertir_date(row.get("date_affectation")),
                    'fonction': row.get("fonction"),
                    'date_prise_fonction': convertir_date(row.get("date_prise_fonction")),
                    'statut': row.get("statut"),
                    'date_statut': convertir_date(row.get("date_statut")),
                    'telephone1': str(row.get("telephone1") or "").strip(),
                    'telephone2': str(row.get("telephone2") or "").strip(),
                    'parcours_professionnel': row.get("parcours_professionnel"),
                    'formations_suivies': row.get("formations_suivies"),
                    'besoin_en_formation': row.get("besoin_en_formation"),
                }
            )
            total += 1
            if total % 100 == 0:
                print(f"🟢 {total} employés traités...")

        except Exception as e:
            erreurs += 1
            print(f"❌ Erreur à la ligne {index+1} (matricule : {matricule}) : {e}")

    print(f"\n✅ {total} lignes importées avec succès.")
    print(f"⚠️ {erreurs} erreurs détectées.")
