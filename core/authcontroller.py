import json
import os
from core.users import Users
from core.films import Films
from core.admins import Admins

class AuthController:
    """Using this class to control authentication operations in the application
    respecting class diagramm in docs/diagramme_de_classe.txt.
    Class Diagram:class AuthController {
    attributes:
    - users_manager : Users
    - admins_manager : Admins
    --
    methods:
    + authenticate_user(username: str, password: str) : bool
    + authenticate_admin(username: str, password: str) : bool
}"""

    def __init__(self):
        self.users_manager = Users()
        self.admins_manager = Admins()

    def authenticate_user(self, username, password):
        """Authenticate a user by their username and password."""
        user = next((u for u in self.users_manager.users if u['username'] == username), None)
        if user and user['password_hash'] == password:  # Simplified for example purposes
            return True
        return False

    def authenticate_admin(self, username, password):
        """Authenticate an admin by their username and password."""
        admin = next((a for a in self.admins_manager.admins if a['username'] == username), None)
        if admin and admin['password_hash'] == password:  # Simplified for example purposes
            return True
        return False
