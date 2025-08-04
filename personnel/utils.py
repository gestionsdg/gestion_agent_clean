
from datetime import date

def calcul_duree_detaillee(date_debut, date_fin=None):
    if not date_debut:
        return (0, 0, 0)

    if date_fin is None:
        date_fin = date.today()

    # Calcul en jours
    jours_total = (date_fin - date_debut).days

    # Approximation : 1 an = 365 jours, 1 mois = 30 jours
    annees = jours_total // 365
    jours_restants = jours_total % 365
    mois = jours_restants // 30
    jours = jours_restants % 30

    return annees, mois, jours


def format_duree(duree_tuple):
    annees, mois, jours = duree_tuple
    parties = []

    # Années
    if annees:
        if annees == 1:
            parties.append("1 an")
        else:
            parties.append(f"{annees} ans")

    # Mois
    if mois:
        if mois == 1:
            parties.append("1 mois")
        else:
            parties.append(f"{mois} mois")

    # Jours
    if jours:
        if jours == 1:
            parties.append("1 jour")
        else:
            parties.append(f"{jours} jours")

    # Si aucune partie n'est présente
    if not parties:
        return "0 jour"

    return " ".join(parties)
