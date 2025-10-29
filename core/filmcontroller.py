import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from core.films import Film
from core.users import User
from core.admins import Admin

class FilmController:
    def __init__(self, films_file: str = "data/films.json"):
        self.films_file = films_file
        self.films: List[Film] = []
        self._load_films()

    def _load_films(self) -> None:
        """Charge les films depuis le fichier JSON"""
        try:
            if os.path.exists(self.films_file):
                with open(self.films_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                self.films = [Film.from_dict(film_data) for film_data in data.get('films', [])]

        except Exception as e:
            print(f"Erreur chargement films: {e}")
            self.films = []

    def _save_films(self) -> bool:
        """Sauvegarde les films dans le fichier JSON"""
        try:
            # If NO_AUTO_SAVE is set, skip saving to avoid accidental overwrites
            if os.environ.get('NO_AUTO_SAVE') == '1':
                try:
                    os.makedirs(os.path.dirname(self.films_file), exist_ok=True)
                    with open(os.path.join(os.path.dirname(self.films_file), 'save_log.txt'), 'a', encoding='utf-8') as logf:
                        logf.write(f"SKIP SAVE_FILMS {self.films_file} at {datetime.now().isoformat()}\n")
                except Exception:
                    pass
                return False
            # Créer le dossier si nécessaire
            os.makedirs(os.path.dirname(self.films_file), exist_ok=True)

            # Sauvegarde de sécurité
            if os.path.exists(self.films_file):
                backup_file = f"{self.films_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.rename(self.films_file, backup_file)

            data = {
                'films': [film.to_dict() for film in self.films],
                'last_updated': datetime.now().isoformat(),
                'total_films': len(self.films),
                'approved_films': len([f for f in self.films if f.approved])
            }

            with open(self.films_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Log successful save
            try:
                with open(os.path.join(os.path.dirname(self.films_file), 'save_log.txt'), 'a', encoding='utf-8') as logf:
                    logf.write(f"SAVE_FILMS {self.films_file} at {datetime.now().isoformat()}\n")
            except Exception:
                pass

            return True
        except Exception as e:
            print(f"Erreur sauvegarde films: {e}")
            return False

    def _get_next_film_id(self) -> int:
        """Génère le prochain ID film"""
        if not self.films:
            return 1
        return max(film.id for film in self.films) + 1

    def _film_exists(self, title: str, release_date: date) -> bool:
        """Vérifie si un film existe déjà"""
        for film in self.films:
            if (film.title.lower() == title.lower() and
                film.release_date == release_date):
                return True
        return False

    def add_film(self, film_data: Dict[str, Any], by_user: User) -> bool:
        """
        Ajoute un nouveau film proposé par un utilisateur
        """
        try:
            # Vérifier les doublons
            if self._film_exists(film_data['title'], film_data['release_date']):
                print("Ce film existe déjà")
                return False

            # Créer le film
            film_id = self._get_next_film_id()
            film = Film(
                id=film_id,
                title=film_data['title'],
                genre=film_data['genre'],
                release_date=film_data['release_date'],
                poster_path=film_data.get('poster_path', ''),
                trailer_url=film_data.get('trailer_url', ''),
                description=film_data.get('description', ''),
                approved=False,  # Doit être validé par un admin
                added_by_user_id=by_user.id
            )

            # Ajouter le log de création
            film.add_log("proposed", by_user.id)

            self.films.append(film)

            if self._save_films():
                print(f"Film '{film.title}' proposé avec succès (en attente de validation)")
                return True
            else:
                # Rollback en cas d'erreur
                self.films.remove(film)
                return False

        except Exception as e:
            print(f"Erreur ajout film: {e}")
            return False

    def delete_film(self, film_id: int, by_admin: Admin) -> bool:
        """
        Supprime un film (admin seulement)
        """
        try:
            film = self.get_film_by_id(film_id)
            if not film:
                print("Film non trouvé")
                return False

            # Ajouter un log avant suppression
            film.add_log("deleted", by_admin.id)

            self.films = [f for f in self.films if f.id != film_id]

            if self._save_films():
                print(f"Film '{film.title}' supprimé par {by_admin.username}")
                return True
            else:
                # Rollback en cas d'erreur
                self.films.append(film)
                return False

        except Exception as e:
            print(f"Erreur suppression film: {e}")
            return False

    def update_film(self, film_id: int, updates: Dict[str, Any], by_admin: Admin) -> bool:
        """
        Met à jour un film (admin seulement)
        """
        try:
            film = self.get_film_by_id(film_id)
            if not film:
                print("Film non trouvé")
                return False

            # Appliquer les mises à jour
            if film.update_info(user_id=by_admin.id, **updates):
                if self._save_films():
                    print(f"Film '{film.title}' mis à jour par {by_admin.username}")
                    return True
                else:
                    return False
            else:
                print("Aucune modification effectuée")
                return False

        except Exception as e:
            print(f"Erreur mise à jour film: {e}")
            return False

    def validate_film(self, film_id: int, by_admin: Admin) -> bool:
        """
        Valide un film proposé (admin seulement)
        """
        try:
            film = self.get_film_by_id(film_id)
            if not film:
                print("Film non trouvé")
                return False

            if film.approved:
                print("Film déjà validé")
                return True

            film.approve(by_admin.id)

            if self._save_films():
                print(f"Film '{film.title}' validé par {by_admin.username}")
                return True
            else:
                return False

        except Exception as e:
            print(f"Erreur validation film: {e}")
            return False

    def search_films(self, title: Optional[str] = None, genre: Optional[str] = None,
                    date_filter: Optional[date] = None, approved_only: bool = True) -> List[Film]:
        """
        Recherche des films selon les critères
        """
        results = []

        for film in self.films:
            # Filtrer par statut d'approbation
            if approved_only and not film.approved:
                continue

            # Appliquer les filtres
            if film.matches_filter(title, genre, date_filter):
                results.append(film)

        return results

    def get_film_by_id(self, film_id: int) -> Optional[Film]:
        """Retourne un film par son ID"""
        for film in self.films:
            if film.id == film_id:
                return film
        return None

    def get_pending_films(self) -> List[Film]:
        """Retourne les films en attente de validation"""
        return [film for film in self.films if not film.approved]

    def get_approved_films(self) -> List[Film]:
        """Retourne les films approuvés"""
        return [film for film in self.films if film.approved]

    def get_films_by_user(self, user_id: int) -> List[Film]:
        """Retourne les films proposés par un utilisateur"""
        return [film for film in self.films if film.added_by_user_id == user_id]

    def get_all_films(self) -> List[Film]:
        """Retourne tous les films"""
        return self.films.copy()

    def get_films_count(self) -> int:
        """Retourne le nombre total de films"""
        return len(self.films)
