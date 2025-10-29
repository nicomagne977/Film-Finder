import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any

class Database:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.backup_dir = os.path.join(data_dir, "backups")
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self, filename: str) -> bool:
        """Crée une sauvegarde du fichier"""
        try:
            if os.path.exists(filename):
                backup_name = f"{os.path.basename(filename)}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                backup_path = os.path.join(self.backup_dir, backup_name)
                shutil.copy2(filename, backup_path)
                return True
        except Exception as e:
            print(f"Erreur création backup: {e}")
        return False

    def load_json(self, filename: str) -> Dict[str, Any]:
        """Charge un fichier JSON"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Erreur chargement {filename}: {e}")
        return {}

    def save_json(self, filename: str, data: Dict[str, Any]) -> bool:
        """Sauvegarde des données dans un fichier JSON"""
        try:
            # Créer le dossier si nécessaire
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # Créer une sauvegarde
            self.create_backup(filename)

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Erreur sauvegarde {filename}: {e}")
            return False

    def get_file_info(self, filename: str) -> Dict[str, Any]:
        """Retourne des informations sur le fichier"""
        try:
            if os.path.exists(filename):
                stat = os.stat(filename)
                return {
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'exists': True
                }
        except Exception as e:
            print(f"Erreur info fichier {filename}: {e}")
        return {'exists': False}
