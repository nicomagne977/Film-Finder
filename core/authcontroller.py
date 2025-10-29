import json
import os
from typing import Optional, Dict, Any
from datetime import datetime
from core.users import User
from core.admins import Admin

class AuthController:
    def __init__(self, users_file: str = "data/users.json"):
        self.users_file = users_file
        self.current_user: Optional[User] = None
        self.users: Dict[int, User] = {}
        self._load_users()

    def _load_users(self) -> None:
        """Charge les utilisateurs depuis le fichier JSON"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for user_data in data.get('users', []):
                    if user_data.get('user_type') == 'admin':
                        user = Admin.from_dict(user_data)
                    else:
                        user = User.from_dict(user_data)
                    self.users[user.id] = user

        except Exception as e:
            print(f"Erreur chargement utilisateurs: {e}")
            self.users = {}

    def _save_users(self) -> bool:
        """Sauvegarde les utilisateurs dans le fichier JSON"""
        try:
            # Créer le dossier si nécessaire
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)

            data = {
                'users': [user.to_dict() for user in self.users.values()],
                'last_updated': datetime.now().isoformat()
            }

            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Erreur sauvegarde utilisateurs: {e}")
            return False

    def _get_next_user_id(self) -> int:
        """Génère le prochain ID utilisateur"""
        if not self.users:
            return 1
        return max(self.users.keys()) + 1

    def register_user(self, first_name: str, last_name: str, email: str,
                     username: str, password: str, is_admin: bool = False) -> Optional[User]:
        """
        Inscrit un nouvel utilisateur
        """
        # Vérifier si l'email ou username existe déjà
        for user in self.users.values():
            if user.email.lower() == email.lower():
                print("Email déjà utilisé")
                return None
            if user.username.lower() == username.lower():
                print("Nom d'utilisateur déjà utilisé")
                return None

        # Créer l'utilisateur
        user_id = self._get_next_user_id()

        if is_admin:
            user = Admin.create_user(user_id, first_name, last_name, email, username, password)
        else:
            user = User.create_user(user_id, first_name, last_name, email, username, password)

        if user:
            self.users[user_id] = user
            if self._save_users():
                return user
            else:
                # Rollback en cas d'erreur de sauvegarde
                del self.users[user_id]

        return None

    def login_user(self, email: str, password: str) -> Optional[User]:
        """
        Connecte un utilisateur
        """
        # Chercher l'utilisateur par email
        user = None
        for u in self.users.values():
            if u.email.lower() == email.lower():
                user = u
                break

        if user and user.verify_password(password):
            self.current_user = user
            print(f"Connexion réussie: {user.get_full_name()}")
            return user
        else:
            print("Email ou mot de passe incorrect")
            return None

    def logout(self) -> None:
        """Déconnecte l'utilisateur actuel"""
        if self.current_user:
            print(f"Déconnexion de {self.current_user.username}")
        self.current_user = None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Retourne un utilisateur par son ID"""
        return self.users.get(user_id)

    def is_admin(self) -> bool:
        """Vérifie si l'utilisateur actuel est un admin"""
        return isinstance(self.current_user, Admin)

    def get_current_user(self) -> Optional[User]:
        """Retourne l'utilisateur actuel"""
        return self.current_user

    def get_users_count(self) -> int:
        """Retourne le nombre total d'utilisateurs"""
        return len(self.users)
