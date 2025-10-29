from typing import Optional, List
from core.users import User
from core.films import Film
from datetime import datetime

class Admin(User):
    def __init__(self, id: int, first_name: str, last_name: str, email: str,
                 username: str, password_hash: str, admin_level: int = 1,
                 created_at: Optional[datetime] = None):
        super().__init__(id, first_name, last_name, email, username, password_hash, created_at)
        self.admin_level = admin_level  # 1: modérateur, 2: admin complet, 3: super admin

    def create_film(self, film: Film) -> bool:
        """
        Crée un nouveau film (admin peut créer directement approuvé)
        """
        try:
            film.approved = True
            film.added_by_user_id = self.id
            film.add_log("created_by_admin", self.id)
            return True
        except Exception as e:
            print(f"Erreur création film par admin: {e}")
            return False

    def validate_film(self, film: Film) -> bool:
        """
        Valide un film proposé par un utilisateur
        """
        try:
            film.approve(self.id)
            return True
        except Exception as e:
            print(f"Erreur validation film: {e}")
            return False

    def update_film(self, film: Film, **updates) -> bool:
        """
        Met à jour les informations d'un film
        """
        try:
            film.update_info(user_id=self.id, **updates)
            return True
        except Exception as e:
            print(f"Erreur mise à jour film: {e}")
            return False

    def delete_film(self, film_id: int, film_controller) -> bool:
        """
        Supprime un film via le FilmController
        """
        try:
            return film_controller.delete_film(film_id, self)
        except Exception as e:
            print(f"Erreur suppression film: {e}")
            return False

    def manage_user(self, user_id: int, action: str, auth_controller) -> bool:
        """
        Gère les utilisateurs (bannir, promouvoir, etc.)
        """
        try:
            if action == "ban":
                # Implémentation de la logique de bannissement
                print(f"Admin {self.username} a banni l'utilisateur {user_id}")
                return True
            elif action == "promote":
                # Implémentation de la promotion admin
                print(f"Admin {self.username} a promu l'utilisateur {user_id}")
                return True
            else:
                print(f"Action inconnue: {action}")
                return False
        except Exception as e:
            print(f"Erreur gestion utilisateur: {e}")
            return False

    def to_dict(self) -> dict:
        """Convertit l'admin en dictionnaire"""
        data = super().to_dict()
        data['admin_level'] = self.admin_level
        data['user_type'] = 'admin'
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'Admin':
        """Crée un admin à partir d'un dictionnaire"""
        user = super().from_dict(data)
        return cls(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            username=user.username,
            password_hash=user.password_hash,
            admin_level=data.get('admin_level', 1),
            created_at=user.created_at
        )

    def __str__(self) -> str:
        return f"Admin({self.id}, level={self.admin_level}) '{self.username}'"
