from django.db import models
from django.utils.functional import cached_property  # ← AJOUT

# ==== CHOIX ====

SEXE_CHOICES = [
    ('M', 'Masculin'),
    ('F', 'Féminin'),
]

GRADE_CHOICES = [
    ('-', '-'),
    ('Directeur', 'Directeur'),
    ('Sous-Directeur', 'Sous-Directeur'),
    ('Chef de Division', 'Chef de Division'),
    ('Chef de Sce Ppal', 'Chef de Sce Ppal'),
    ('Chef de Service', 'Chef de Service'),
    ('Chef de Sce Adjt', 'Chef de Sce Adjt'),
    ('Chef de Section', 'Chef de Section'),
    ('Rédacteur Ppal', 'Rédacteur Ppal'),
    ('Rédacteur', 'Rédacteur'),
    ('Rédacteur Adjt', 'Rédacteur Adjt'),
    ('Commis Chef', 'Commis Chef'),
    ('Commis Ppal', 'Commis Ppal'),
    ('Commis', 'Commis'),
    ('Commis Adjt', 'Commis Adjt'),
    ('Agent Aux 1ère Cl', 'Agent Aux 1ère Cl'),
    ('Agent Aux 2è Cl', 'Agent Aux 2è Cl'),
    ('Manœuvre Sp', 'Manœuvre Sp'),
    ('Manœuvre Lourd', 'Manœuvre Lourd'),
    ('Manœuvre Ord', 'Manœuvre Ord'),
]

ENTITE_CHOICES = [
    ('Secrétariat du DG', 'Secrétariat du DG'),
    ('Dir. des Ressources Humaines', 'Dir. des Ressources Humaines'),
    ('Dir. des Etudes et Organisation', 'Dir. des Etudes et Organisation'),
    ('Direction Technique', 'Direction Technique'),
    ('Direction Juridique', 'Direction Juridique'),
    ('Direction Financière', 'Direction Financière'),
    ('Direction des Services Généraux', 'Direction des Services Généraux'),
    ('Direction de Recouvrement', 'Direction de Recouvrement'),
    ('Direction de Prévention', 'Direction de Prévention'),
    ("Direction de l'Audit Interne", "Direction de l'Audit Interne"),
    ("Direction de l'Action San et Soc", "Direction de l'Action San et Soc"),
    ('Direction de Formation', 'Direction de Formation'),
    ('Dir. de la Gestion Imm-Ouest', 'Dir. de la Gestion Imm-Ouest'),
    ('Pompes Funèbres Pop', 'Pompes Funèbres Pop'),
    ('Secrétariat des Organes Statutaires', 'Secrétariat des Organes Statutaires'),
    ('Collège d’Experts', 'Collège d’Experts'),
    ('Centre Médical Matonge', 'Centre Médical Matonge'),
    ('Dir. Urbaine de Kin-Sud', 'Dir. Urbaine de Kin-Sud'),
    ('Dir. Urbaine de Kin-Ouest', 'Dir. Urbaine de Kin-Ouest'),
    ('Dir. Urbaine de Kin-Nord', 'Dir. Urbaine de Kin-Nord'),
    ('Dir. Urbaine de Kin-Est', 'Dir. Urbaine de Kin-Est'),
    ('Dir. Urbaine de Kin-Centre', 'Dir. Urbaine de Kin-Centre'),
    ('Dir. Urbaine de Kin Sud-Est', 'Dir. Urbaine de Kin Sud-Est'),
    ('Dir. Urbaine de Kin Nord-Est', 'Dir. Urbaine de Kin Nord-Est'),
    ('Dir. Urbaine de Kin Centre-Ouest', 'Dir. Urbaine de Kin Centre-Ouest'),
    ('CP Révolution/Duk-Nord', 'CP Révolution/Duk-Nord'),
    ('CP Makala/Duk-Centre', 'CP Makala/Duk-Centre'),
    ('CP Lemba/Duk-Sud', 'CP Lemba/Duk-Sud'),
    ('CP Matete/Duk-Sud', 'CP Matete/Duk-Sud'),  # ✅ AJOUT ICI
    ('CP Kinshasa/Duk-Centre', 'CP Kinshasa/Duk-Centre'),
    ('CP Kimbanseke/Duk-Est', 'CP Kimbanseke/Duk-Est'),
    ('CP Commerce/Duk-Nord', 'CP Commerce/Duk-Nord'),
    ('CP Golf/Lubumbashi', 'CP Golf/Lubumbashi'),
    ('CP Kenya/Lubumbashi', 'CP Kenya/Lubumbashi'),  # ✅ ajout après "CP Golf/Lubumbashi"
    ('Corps de Surveillance', 'Corps de Surveillance'),
    ('DP Uvira', 'DP Uvira'),
    ('DP Tanganyika', 'DP Tanganyika'),
    ('DP Mbuji Mayi', 'DP Mbuji Mayi'),
    ('DP Mbanza-Ngungu', 'DP Mbanza-Ngungu'),
    ('DP Mbandaka', 'DP Mbandaka'),
    ('DP Matadi', 'DP Matadi'),
    ('DP Maniema', 'DP Maniema'),
    ('DP Lubumbashi', 'DP Lubumbashi'),
    ('DP Likasi', 'DP Likasi'),
    ('DP Kolwezi', 'DP Kolwezi'),
    ('DP Kisangani', 'DP Kisangani'),
    ('DP Kikwit', 'DP Kikwit'),
    ('DP Kasumbalesa', 'DP Kasumbalesa'),
    ('DP Kananga', 'DP Kananga'),
    ('DP Kamina', 'DP Kamina'),
    ('DP Goma', 'DP Goma'),
    ('DP Bunia', 'DP Bunia'),
    ('DP Bukavu', 'DP Bukavu'),
    ('DP Boma', 'DP Boma'),
    ('DP Bandundu', 'DP Bandundu'),
    ('Dir. de la Gestion Imm-Est', 'Dir. de la Gestion Imm-Est'),
    ("Bureau d'Isiro", "Bureau d'Isiro"),
    ("Bureau d'Inongo", "Bureau d'Inongo"),
    ("Bureau d'Ilebo", "Bureau d'Ilebo"),
    ('Bureau de Tshikapa', 'Bureau de Tshikapa'),
    ('Bureau de Mwene-Ditu', 'Bureau de Mwene-Ditu'),
    ('Bureau de Lodja', 'Bureau de Lodja'),
    ('Bureau de Lisala', 'Bureau de Lisala'),
    ('Bureau de Kasaji', 'Bureau de Kasaji'),
    ('Bureau de Kabinda', 'Bureau de Kabinda'),
    ('Bureau de Gemena', 'Bureau de Gemena'),
    ('Bureau de Gbadolite', 'Bureau de Gbadolite'),
    ('Bureau de Butembo', 'Bureau de Butembo'),
    ('Bureau de Buta', 'Bureau de Buta'),
    ('Bureau de Boende', 'Bureau de Boende'),
    ("Antenne d'Idiofa", "Antenne d'Idiofa"),
    ("Antenne de Watsa", "Antenne de Watsa"),
    ('Antenne de Tshimbulu', 'Antenne de Tshimbulu'),
    ('Antenne de Sandoa', 'Antenne de Sandoa'),
    ('Antenne de Rutshuru', 'Antenne de Rutshuru'),
    ('Antenne de Pweto', 'Antenne de Pweto'),
    ('Antenne de Malemba Nkulu', 'Antenne de Malemba Nkulu'),
    ('Antenne de Mweka', 'Antenne de Mweka'),
    ('Antenne de Muanda', 'Antenne de Muanda'),
    ('Antenne de Masisi', 'Antenne de Masisi'),
    ('Antenne de Kipushi', 'Antenne de Kipushi'),
    ('Antenne de Kasenga', 'Antenne de Kasenga'),
    ('Antenne de Kalima', 'Antenne de Kalima'),
    ('Antenne de Kabare', 'Antenne de Kabare'),
    ('Antenne de Gungu', 'Antenne de Gungu'),
    ('Antenne de Fizi', 'Antenne de Fizi'),
    ('Antenne de Dilolo', 'Antenne de Dilolo'),
    ('Antenne de Bumba', 'Antenne de Bumba'),
    ('Antenne de Beni', 'Antenne de Beni'),
    ("Antenne d'Aru", "Antenne d'Aru"),
]

ETAT_CIVIL_CHOICES = [
    ('Célibataire', 'Célibataire'),
    ('Marié', 'Marié'),
    ('Mariée', 'Mariée'),
    ('Divorcé', 'Divorcé'),
    ('Divorcée', 'Divorcée'),
    ('Veuf', 'Veuf'),
    ('Veuve', 'Veuve'),
]

STATUT_CHOICES = [
    ('Actif', 'Actif'),
    ('Mise à la retraite', 'Mise à la retraite'),
    ('Décédé', 'Décédé'),
    ('En détachement', 'En détachement'),
    ('Licencié', 'Licencié'),
    ('Démission', 'Démission'),
    ('Mise en disponibilité', 'Mise en disponibilité'),
]

# ==== MODEL ====

class Employe(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    matricule = models.CharField(max_length=50, unique=True)

    sexe = models.CharField(max_length=10, choices=SEXE_CHOICES)

    date_naissance = models.DateField(null=True, blank=True)

    grade_engagement = models.CharField(max_length=100, choices=GRADE_CHOICES, null=True, blank=True)
    date_engagement = models.DateField(null=True, blank=True)

    grade_actuel = models.CharField(max_length=100, choices=GRADE_CHOICES, null=True, blank=True)
    date_derniere_promotion = models.DateField(null=True, blank=True)

    etat_civil = models.CharField(max_length=100, choices=ETAT_CIVIL_CHOICES, null=True, blank=True)
    nom_conjoint = models.CharField(max_length=100, null=True, blank=True)
    adresse = models.TextField(null=True, blank=True)

    entite = models.CharField(max_length=100, choices=ENTITE_CHOICES, null=True, blank=True)
    niveau_etudes = models.CharField(max_length=100, null=True, blank=True)
    option = models.CharField(max_length=100, null=True, blank=True)

    service = models.CharField(max_length=100, null=True, blank=True)
    date_affectation = models.DateField(null=True, blank=True)
    annee_affectation = models.IntegerField(null=True, blank=True)
    fonction = models.CharField(max_length=100, null=True, blank=True)
    date_prise_fonction = models.DateField(null=True, blank=True)

    statut = models.CharField(max_length=100, choices=STATUT_CHOICES, null=True, blank=True)
    date_statut = models.DateField(null=True, blank=True)
    date_fin_disponibilite = models.DateField(null=True, blank=True)
    date_fin_detachement = models.DateField(null=True, blank=True)

    telephone1 = models.CharField(max_length=20, null=True, blank=True)
    telephone2 = models.CharField(max_length=20, null=True, blank=True)
    photo = models.ImageField(upload_to='photos/', null=True, blank=True)

    parcours_professionnel = models.TextField(null=True, blank=True)
    formations_suivies = models.TextField(null=True, blank=True)
    besoin_en_formation = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"

    @cached_property
    def photo_url(self) -> str:
        """
        URL d'image safe pour le HTML/PDF (remplace les antislashs Windows).
        Retourne '' si la photo est absente ou inaccessible.
        """
        try:
            url = self.photo.url  # peut lever si pas de fichier
        except Exception:
            return ""
        return url.replace("\\", "/")
