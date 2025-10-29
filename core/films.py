from datetime import datetime, date
from typing import Optional, List, Dict, Any
import json

class Film:
    def __init__(self, id: int, title: str, genre: str, release_date: date,
                 poster_path: str = "", trailer_url: str = "", description: str = "",
                 approved: bool = False, added_by_user_id: int = 0,
                 logs: Optional[List[Dict]] = None):
        self.id = id
        self.title = title
        self.genre = genre
        self.release_date = release_date
        self.poster_path = poster_path
        self.trailer_url = trailer_url
        self.description = description
        self.approved = approved
        self.added_by_user_id = added_by_user_id
        self.logs = logs or []

    def matches_filter(self, title: Optional[str] = None, genre: Optional[str] = None,
                      date_filter: Optional[date] = None) -> bool:
        """
        Vérifie si le film correspond aux critères de recherche
        """
        # Filtre par titre (recherche partielle, insensible à la casse)
        if title and title.lower() not in self.title.lower():
            return False

        # Filtre par genre (exact match, insensible à la casse)
        if genre and genre.lower() != self.genre.lower():
            return False

        # Filtre par date (année seulement ou date complète)
        if date_filter:
            if isinstance(date_filter, date):
                # Si une date complète est fournie, comparaison exacte
                if self.release_date != date_filter:
                    return False
            else:
                # Si seulement l'année est fournie
                if self.release_date.year != date_filter:
                    return False

        return True

    def add_log(self, action: str, user_id: int) -> None:
        """
        Ajoute une entrée de log pour le film
        """
        log_entry = {
            'action': action,
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'film_id': self.id
        }
        self.logs.append(log_entry)

        # Garder seulement les 100 derniers logs pour éviter la surcharge
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]

    def approve(self, admin_id: int) -> None:
        """Approuve le film et ajoute un log"""
        self.approved = True
        self.add_log("approved", admin_id)

    def reject(self, admin_id: int) -> None:
        """Rejette le film et ajoute un log"""
        self.approved = False
        self.add_log("rejected", admin_id)

    def update_info(self, title: Optional[str] = None, genre: Optional[str] = None,
                   release_date: Optional[date] = None, poster_path: Optional[str] = None,
                   trailer_url: Optional[str] = None, description: Optional[str] = None,
                   user_id: int = 0) -> bool:
        """
        Met à jour les informations du film et ajoute un log
        Retourne True si des modifications ont été faites
        """
        modifications = []

        if title and title != self.title:
            modifications.append(f"title: {self.title} -> {title}")
            self.title = title

        if genre and genre != self.genre:
            modifications.append(f"genre: {self.genre} -> {genre}")
            self.genre = genre

        if release_date and release_date != self.release_date:
            modifications.append(f"release_date: {self.release_date} -> {release_date}")
            self.release_date = release_date

        if poster_path is not None and poster_path != self.poster_path:
            modifications.append(f"poster_path updated")
            self.poster_path = poster_path

        if trailer_url is not None and trailer_url != self.trailer_url:
            modifications.append(f"trailer_url updated")
            self.trailer_url = trailer_url

        if description is not None and description != self.description:
            modifications.append(f"description updated")
            self.description = description

        if modifications:
            modification_text = ", ".join(modifications)
            self.add_log(f"updated: {modification_text}", user_id)
            return True

        return False

    def get_recent_logs(self, limit: int = 10) -> List[Dict]:
        """Retourne les logs les plus récents"""
        return sorted(self.logs, key=lambda x: x['timestamp'], reverse=True)[:limit]

    def to_dict(self) -> Dict[str, Any]:
        """Convertit le film en dictionnaire pour stockage JSON"""
        return {
            'id': self.id,
            'title': self.title,
            'genre': self.genre,
            'release_date': self.release_date.isoformat(),
            'poster_path': self.poster_path,
            'trailer_url': self.trailer_url,
            'description': self.description,
            'approved': self.approved,
            'added_by_user_id': self.added_by_user_id,
            'logs': self.logs
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Film':
        """Crée un film à partir d'un dictionnaire"""
        # Conversion de la date de sortie
        release_date = date.fromisoformat(data['release_date']) if isinstance(data['release_date'], str) else data['release_date']

        return cls(
            id=data['id'],
            title=data['title'],
            genre=data['genre'],
            release_date=release_date,
            poster_path=data.get('poster_path', ''),
            trailer_url=data.get('trailer_url', ''),
            description=data.get('description', ''),
            approved=data.get('approved', False),
            added_by_user_id=data.get('added_by_user_id', 0),
            logs=data.get('logs', [])
        )

    def __str__(self) -> str:
        status = "✓" if self.approved else "⏳"
        return f"Film({self.id}) {status} '{self.title}' ({self.release_date.year}) - {self.genre}"

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other) -> bool:
        """Deux films sont égaux s'ils ont le même ID"""
        if not isinstance(other, Film):
            return False
        return self.id == other.id

    def get_age(self) -> int:
        """Retourne l'âge du film en années"""
        today = date.today()
        return today.year - self.release_date.year - (
            (today.month, today.day) < (self.release_date.month, self.release_date.day)
        )

    def is_recent(self, years: int = 2) -> bool:
        """Vérifie si le film est récent (par défaut moins de 2 ans)"""
        return self.get_age() <= years
