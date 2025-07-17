# sauvegarder_bdd.py
import os
import shutil
from datetime import datetime

# Répertoire du projet Django
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Chemin vers la base SQLite
db_path = os.path.join(BASE_DIR, 'db.sqlite3')

# Dossier de sauvegarde
backup_dir = os.path.join(BASE_DIR, 'sauvegardes')

# Nom de fichier avec date et heure
timestamp = datetime.now().strftime('%Y-%m-%d_%Hh%M')
backup_filename = f'db_backup_{timestamp}.sqlite3'

# Chemin complet de la sauvegarde
backup_path = os.path.join(backup_dir, backup_filename)

# Copier le fichier
shutil.copy2(db_path, backup_path)

print(f"✅ Sauvegarde effectuée : {backup_filename}")
