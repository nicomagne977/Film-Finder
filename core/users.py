import hashlib
import re
from datetime import datetime
from typing import Optional

class User:
    def __init__(self, id: int, first_name: str, last_name: str, email: str,
                 username: str, password_hash: str, created_at: Optional[datetime] = None):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.username = username
        self.password_hash = password_hash
        self.created_at = created_at or datetime.now()

    def get_full_name(self) -> str:
        """Retourne le nom complet de l'utilisateur"""
        return f"{self.first_name} {self.last_name}".strip()

    @staticmethod
    def check_password_rules(password: str, username: str = "", first_name: str = "", last_name: str = "") -> bool:
        """
        Vérifie si le mot de passe respecte les règles de sécurité
        - Au moins 8 caractères
        - Au moins une majuscule
        - Au moins un chiffre
        - Au moins un caractère spécial
        - Ne contient pas le nom d'utilisateur, prénom ou nom
        """
        if len(password) < 8:
            return False

        # Vérification des caractères requis
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)

        if not (has_upper and has_digit and has_special):
            return False

        # Vérification que le mot de passe ne contient pas d'informations personnelles
        personal_info = [username.lower(), first_name.lower(), last_name.lower()]
        personal_info = [info for info in personal_info if info and len(info) > 2]  # Éviter les noms trop courts

        for info in personal_info:
            if info and info in password.lower():
                return False

        return True

    def verify_password(self, password: str) -> bool:
        """Vérifie si le mot de passe correspond au hash stocké"""
        try:
            # Hash le mot de passe fourni avec la même méthode
            password_hash = self._hash_password(password)
            return password_hash == self.password_hash
        except Exception:
            return False

    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash le mot de passe en utilisant SHA-256"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    @classmethod
    def create_user(cls, id: int, first_name: str, last_name: str, email: str,
                   username: str, password: str) -> Optional['User']:
        """
        Crée un nouvel utilisateur avec validation du mot de passe
        Retourne None si le mot de passe ne respecte pas les règles
        """
        if not cls.check_password_rules(password, username, first_name, last_name):
            return None

        password_hash = cls._hash_password(password)
        return cls(id, first_name, last_name, email, username, password_hash)

    def propose_film(self, film) -> bool:
        """
        Permet à l'utilisateur de proposer un film
        Retourne True si la proposition est réussie
        """
        # Cette méthode sera complétée lorsque la classe Film sera implémentée
        # Pour l'instant, on retourne True pour simuler le succès
        print(f"Utilisateur {self.username} a proposé le film : {film.title if hasattr(film, 'title') else 'Nouveau film'}")
        return True

    def to_dict(self) -> dict:
        """Convertit l'utilisateur en dictionnaire pour stockage JSON"""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'username': self.username,
            'password_hash': self.password_hash,
            'created_at': self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Crée un utilisateur à partir d'un dictionnaire"""
        created_at = datetime.fromisoformat(data['created_at']) if 'created_at' in data else None
        return cls(
            id=data['id'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            username=data['username'],
            password_hash=data['password_hash'],
            created_at=created_at
        )

    def __str__(self) -> str:
        return f"User(id={self.id}, username='{self.username}', email='{self.email}')"

    def __repr__(self) -> str:
        return self.__str__()
