"""Tests unitaires pour le coeur de l'application Film Finder.

Ce fichier remplace l'ancien script `tests_core.py` par des tests basés sur
`unittest`. Il couvre le flux principal : enregistrement, connexion,
proposition de film, validation par admin, recherche et vérification des logs.
"""

import os
import sys
import unittest
from datetime import date

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.authcontroller import AuthController
from core.filmcontroller import FilmController


class CoreWorkflowTests(unittest.TestCase):
    def setUp(self):
        # Nettoyer les fichiers JSON pour un état propre
        for f in ("data/users.json", "data/films.json"):
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass

        self.auth = AuthController()
        self.films = FilmController()

    def tearDown(self):
        # Nettoyage après chaque test
        for f in ("data/users.json", "data/films.json"):
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass

    def test_register_login_propose_validate_search_and_logs(self):
        # 1) Inscription
        user = self.auth.register_user(
            "Jean", "Dupont", "jean@email.com", "jdupont", "Pass123!"
        )
        self.assertIsNotNone(user, "L'utilisateur doit être créé avec un mot de passe valide")

        # Utiliser un mot de passe qui ne contient pas d'informations personnelles
        admin = self.auth.register_user(
            "Admin", "System", "admin@email.com", "admin", "Secure!234", True
        )
        self.assertIsNotNone(admin, "L'admin doit être créé")

        # Au moins 2 utilisateurs
        self.assertGreaterEqual(self.auth.get_users_count(), 2)

        # 2) Connexion utilisateur
        logged = self.auth.login_user("jean@email.com", "Pass123!")
        self.assertIsNotNone(logged)

        # 3) Proposer un film
        film_data = {
            'title': "Inception",
            'genre': "Science-Fiction",
            'release_date': date(2010, 7, 16),
            'description': "Un voleur qui s'infiltre dans les rêves."
        }

        added = self.films.add_film(film_data, logged)
        self.assertTrue(added, "Le film doit être proposé avec succès")

        pending = self.films.get_pending_films()
        self.assertEqual(len(pending), 1)

        # 4) Validation par admin
        self.auth.logout()
        # Se connecter avec le mot de passe défini lors de l'inscription ci-dessus
        admin_logged = self.auth.login_user("admin@email.com", "Secure!234")
        self.assertIsNotNone(admin_logged)
        self.assertTrue(self.auth.is_admin(), "L'utilisateur connecté doit être considéré comme admin")

        film = self.films.get_pending_films()[0]
        validated = self.films.validate_film(film.id, admin_logged)
        self.assertTrue(validated, "Le film doit pouvoir être validé par l'admin")

        # 5) Recherche (devrait retourner le film approuvé)
        results = self.films.search_films(title="inception")
        self.assertGreaterEqual(len(results), 1)

        # 6) Vérifier les logs: doit contenir 'proposed' et 'approved'
        film_after = self.films.get_film_by_id(film.id)
        actions = [log.get('action') for log in film_after.logs]
        self.assertIn('proposed', actions)
        self.assertIn('approved', actions)


if __name__ == '__main__':
    unittest.main()
