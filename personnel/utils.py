from datetime import date

def calcul_duree(date_debut):
    if not date_debut:
        return 0
    aujourd_hui = date.today()
    duree = aujourd_hui.year - date_debut.year
    if (aujourd_hui.month, aujourd_hui.day) < (date_debut.month, date_debut.day):
        duree -= 1
    return duree

def format_duree(duree):
    return f"{duree} an" if duree == 1 else f"{duree} ans"
