import json
import os
from core.users import Users
from core.films import Films
from core.admins import Admins


class FilmController:
    """Using this class to control film operations in the application
    respecting class diagramm in docs/diagramme_de_classe.txt.
    Class Diagram:class FilmController {
    attributes:
    - films_manager : Films
    - admins_manager : Admins
    --
    methods:
    + add_film_as_admin(admin_id: int, film: Film) : bool
    + remove_film_as_admin(admin_id: int, film_id: int) : bool
}"""

    def __init__(self):
        self.films_manager = Films()
        self.admins_manager = Admins()

    def add_film_as_admin(self, admin_id, film):
        """Allow an admin to add a new film to the collection."""
        admin = next((a for a in self.admins_manager.admins if a['id'] == admin_id), None)
        if admin:
            self.films_manager.add_film(film)
            return True
        return False

    def remove_film_as_admin(self, admin_id, film_id):
        """Allow an admin to remove a film from the collection."""
        admin = next((a for a in self.admins_manager.admins if a['id'] == admin_id), None)
        if admin:
            self.films_manager.remove_film(film_id)
            return True
        return False
