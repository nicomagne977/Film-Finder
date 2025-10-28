import json
import os


class Users:
    """Using this class to manage user information in the application with file json
    respecting class diagramm in docs/diagramme_de_classe.txt.
    Class Diagram:class User {
    attributes:
    - id : int
    - first_name : str
    - last_name : str
    - email : str
    - username : str
    - password_hash : str
    - created_at : datetime
    --
    methods:
    + get_full_name() : str
    + check_password_rules(password: str) : bool
    + verify_password(password: str) : bool
    + propose_film(f: Film) : bool
}"""

    def __init__(self, json_file='users.json'):
        self.json_file = json_file
        self.users = self.load_users()

    def load_users(self):
        """Load users from a JSON file."""
        if not os.path.exists(self.json_file):
            return []
        with open(self.json_file, 'r') as file:
            return json.load(file)

    def save_users(self):
        """Save users to a JSON file."""
        with open(self.json_file, 'w') as file:
            json.dump(self.users, file, indent=4)
