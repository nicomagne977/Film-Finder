# test_core.py - Test complet des classes
from datetime import date
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.database import Database
from core.users import User
from core.admins import Admin
from core.films import Film
from core.authcontroller import AuthController
from core.filmcontroller import FilmController

def test_complet():
    # Initialisation
    auth = AuthController()
    films = FilmController()

    # Nettoyer les données existantes pour le test
    import os
    if os.path.exists("data/users.json"):
        os.remove("data/users.json")
    if os.path.exists("data/films.json"):
        os.remove("data/films.json")

    # Recréer les contrôleurs
    auth = AuthController()
    films = FilmController()

    print("=== TEST COMPLET FILM FINDER ===\n")

    # 1. Inscription utilisateurs
    print("1. INSCRIPTION UTILISATEURS")
    user1 = auth.register_user("Jean", "Dupont", "jean@email.com", "jdupont", "Pass123!")
    admin1 = auth.register_user("Admin", "System", "admin@email.com", "admin", "Admin123!", True)

    print(f"Utilisateur créé: {user1}")
    print(f"Admin créé: {admin1}")
    print(f"Total utilisateurs: {auth.get_users_count()}\n")

    # 2. Connexion
    print("2. CONNEXION")
    logged_user = auth.login_user("jean@email.com", "Pass123!")
    print(f"Utilisateur connecté: {logged_user}\n")

    # 3. Proposition de film
    print("3. PROPOSITION FILM")
    film_data = {
        'title': "Inception",
        'genre': "Science-Fiction",
        'release_date': date(2010, 7, 16),
        'description': "Un voleur qui s'infiltre dans les rêves."
    }

    success = films.add_film(film_data, logged_user)
    print(f"Film proposé: {success}")
    print(f"Films en attente: {len(films.get_pending_films())}\n")

    # 4. Connexion admin et validation
    print("4. VALIDATION PAR ADMIN")
    auth.logout()
    admin_logged = auth.login_user("admin@email.com", "Admin123!")
    print(f"Admin connecté: {admin_logged}, est admin: {auth.is_admin()}")

    # Valider le film
    if films.get_pending_films():
        film = films.get_pending_films()[0]
        success = films.validate_film(film.id, admin_logged)
        print(f"Film validé: {success}")

    # 5. Recherche
    print("\n5. RECHERCHE")
    results = films.search_films(title="inception")
    print(f"Résultats recherche: {len(results)} films")
    for film in results:
        print(f"  - {film}")

    # 6. Statistiques
    print(f"\n6. STATISTIQUES")
    print(f"Total films: {films.get_films_count()}")
    print(f"Films approuvés: {len(films.get_approved_films())}")
    print(f"Films en attente: {len(films.get_pending_films())}")

if __name__ == "__main__":
    test_complet()
