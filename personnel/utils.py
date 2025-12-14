# utils.py
from datetime import date, datetime

# --- Support optionnel de dateutil (différence exacte années/mois/jours) ---
try:
    from dateutil.relativedelta import relativedelta as _relativedelta
    _HAS_DATEUTIL = True
except Exception:
    _HAS_DATEUTIL = False


def _to_date(d):
    """
    Normalise un objet date/datetime/None vers date | None.
    """
    if d is None:
        return None
    if isinstance(d, datetime):
        return d.date()
    return d


def calcul_duree_detaillee(date_debut, date_fin=None):
    """
    Calcule la durée (années, mois, jours) entre date_debut et date_fin.
    - Si python-dateutil est disponible, utilise relativedelta (plus précis).
    - Sinon, retombe sur l'approximation: 1 an=365j, 1 mois=30j.
    - Gère les dates None et inverse automatiquement si date_debut > date_fin.
    """
    date_debut = _to_date(date_debut)
    date_fin = _to_date(date_fin) or date.today()

    if not date_debut:
        return (0, 0, 0)

    # Inversion si nécessaire pour éviter une durée négative
    if date_debut > date_fin:
        date_debut, date_fin = date_fin, date_debut

    if _HAS_DATEUTIL:
        delta = _relativedelta(date_fin, date_debut)
        return (delta.years, delta.months, delta.days)

    # Repli: approximation jour/mois/année
    jours_total = (date_fin - date_debut).days
    annees = jours_total // 365
    jours_restants = jours_total % 365
    mois = jours_restants // 30
    jours = jours_restants % 30
    return (annees, mois, jours)


def format_duree(duree_tuple):
    """
    Formatte (années, mois, jours) en chaîne lisible en français,
    avec gestion de 'an/ans' et singular/pluriel.
    Ex: (1, 0, 0) -> '1 an'; (2, 3, 1) -> '2 ans 3 mois 1 jour'
    """
    annees, mois, jours = duree_tuple or (0, 0, 0)
    parties = []

    # Années
    if annees:
        parties.append("1 an" if annees == 1 else f"{annees} ans")

    # Mois
    if mois:
        parties.append("1 mois" if mois == 1 else f"{mois} mois")

    # Jours
    if jours:
        parties.append("1 jour" if jours == 1 else f"{jours} jours")

    return " ".join(parties) if parties else "0 jour"


def age_en_ans(date_naissance, ref=None):
    """
    Calcule l'âge en années révolues.
    - Retourne None si date_naissance est absente.
    - Si python-dateutil est présent, utilise relativedelta pour exactitude.
    """
    dn = _to_date(date_naissance)
    ref = _to_date(ref) or date.today()

    if not dn:
        return None

    if dn > ref:
        # Naissance dans le futur => âge inconnu
        return None

    if _HAS_DATEUTIL:
        return _relativedelta(ref, dn).years

    # Calcul standard sans dépendance
    return ref.year - dn.year - ((ref.month, ref.day) < (dn.month, dn.day))


def format_age(date_naissance, ref=None, fallback="-"):
    """
    Renvoie l'âge formaté 'X ans' / '1 an', ou fallback si inconnu.
    Utile dans les templates HTML/PDF.
    """
    a = age_en_ans(date_naissance, ref=ref)
    if a is None:
        return fallback
    return "1 an" if a == 1 else f"{a} ans"
