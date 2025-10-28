import json
import os

class Films:
    """Using this class to manage film information in the application with file json
    respecting class diagramm in docs/diagramme_de_classe.txt.
    Class Diagram:class Film {
    attributes:
    - id : int
    - title : str
    - director : str
    - release_year : int
    - genre : str
    - duration_minutes : int
    - rating : float
    --
    methods:
    + get_summary() : str
    + is_classic() : bool
}"""

    def __init__(self, json_file='films.json'):
        self.json_file = json_file
        self.films = self.load_films()

    def load_films(self):
        """Load films from a JSON file."""
        if not os.path.exists(self.json_file):
            return []
        with open(self.json_file, 'r') as file:
            return json.load(file)

    def save_films(self):
        """Save films to a JSON file."""
        with open(self.json_file, 'w') as file:
            json.dump(self.films, file, indent=4)
    def add_film(self, film):
        """Add a new film to the collection."""
        self.films.append(film)
        self.save_films()
    def get_film_by_id(self, film_id):
        """Retrieve a film by its ID."""
        for film in self.films:
            if film['id'] == film_id:
                return film
        return None
    def remove_film(self, film_id):
        """Remove a film by its ID."""
        self.films = [film for film in self.films if film['id'] != film_id]
        self.save_films()
    def update_film(self, film_id, updated_info):
        """Update film information by its ID."""
        for film in self.films:
            if film['id'] == film_id:
                film.update(updated_info)
                self.save_films()
                return True
        return False
    def list_films(self):
        """List all films in the collection."""
        return self.films
    def find_films_by_genre(self, genre):
        """Find films by genre."""
        return [film for film in self.films if film['genre'].lower() == genre.lower()]
    def find_films_by_director(self, director):
        """Find films by director."""
        return [film for film in self.films if film['director'].lower() == director.lower()]
    def find_films_by_release_year(self, year):
        """Find films by release year."""
        return [film for film in self.films if film['release_year'] == year]
    def get_top_rated_films(self, top_n=10):
        """Get top N rated films."""
        sorted_films = sorted(self.films, key=lambda x: x['rating'], reverse=True)
        return sorted_films[:top_n]
    def get_classic_films(self, year_threshold=25):
        """Get films older than a certain number of years."""
        current_year = 2024  # Update this as needed
        return [film for film in self.films if current_year - film['release_year'] >= year_threshold]

    def get_film_summary(self, film_id):
        """Get a summary of a film by its ID."""
        film = self.get_film_by_id(film_id)
        if film:
            return f"{film['title']} ({film['release_year']}), directed by {film['director']}. Genre: {film['genre']}, Duration: {film['duration_minutes']} minutes, Rating: {film['rating']}/10"
        return "Film not found."

    def is_classic(self, film_id, year_threshold=25):
        """Check if a film is considered a classic based on its release year."""
        film = self.get_film_by_id(film_id)
        if film:
            current_year = 2024  # Update this as needed
            return current_year - film['release_year'] >= year_threshold
        return False
    def clear_films(self):
        """Clear all films from the collection."""
        self.films = []
        self.save_films()

# Example usage:
# films_manager = Films()
# films_manager.add_film({
