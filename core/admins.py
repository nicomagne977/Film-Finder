import json
import os
from core.users import Users
from core.films import Films

class Admins(Users):
    """Using this class to manage admin information in the application with file json
    respecting class diagramm in docs/diagramme_de_classe.txt.
    Class Diagram:class Admin extends User {
    attributes:
    - admin_level : int
    --
    methods:
    + ban_user(user_id: int) : bool
    + unban_user(user_id: int) : bool
    + add_film(f: Film) : bool
    + remove_film(film_id: int) : bool
}"""

    def __init__(self, json_file='admins.json'):
        super().__init__(json_file)
        self.admins = self.load_admins()

    def load_admins(self):
        """Load admins from a JSON file."""
        if not os.path.exists(self.json_file):
            return []
        with open(self.json_file, 'r') as file:
            return json.load(file)

    def save_admins(self):
        """Save admins to a JSON file."""
        with open(self.json_file, 'w') as file:
            json.dump(self.admins, file, indent=4)

    def ban_user(self, user_id):
        """Ban a user by their ID."""
        for user in self.users:
            if user['id'] == user_id:
                user['banned'] = True
                self.save_users()
                return True
        return False

    def unban_user(self, user_id):
        """Unban a user by their ID."""
        for user in self.users:
            if user['id'] == user_id:
                user['banned'] = False
                self.save_users()
                return True
        return False

    def add_film(self, film):
        """Add a new film to the collection."""
        films_manager = Films()
        films_manager.add_film(film)
        return True

    def remove_film(self, film_id):
        """Remove a film by its ID."""
        films_manager = Films()
        films_manager.remove_film(film_id)
        return True

    def update_film(self, film_id, updated_info):
        """Update film information by its ID."""
        films_manager = Films()
        return films_manager.update_film(film_id, updated_info)

    def list_films(self):
        """List all films in the collection."""
        films_manager = Films()
        return films_manager.list_films()
