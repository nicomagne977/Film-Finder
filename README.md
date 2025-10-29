# Film Finder

Film Finder est une application de recherche et gestion de films, développée en Python avec PyQt et JSON comme base de données.
L’application permet aux utilisateurs de proposer des films et aux administrateurs de les valider. Chaque action est historisée dans des logs.

---

## 🎯 Objectifs du projet

- Authentification sécurisée (mot de passe avec majuscule, chiffre, caractère spécial et interdiction du nom dans le mot de passe)
- Gestion des utilisateurs (admin vs utilisateur normal)
- Recherche de films par titre, genre, date
- Gestion des films : ajout, modification, suppression et validation
- Affichage des films avec poster et lecture de bande-annonce (via flux vidéo MP4)
- Historique des actions (logs)
- Stockage des données en JSON

---

## 🏗️ Méthodologie Agile

Nous suivrons la méthodologie **Agile** avec **sprints courts**, itérations et revues fréquentes :

### Sprints proposés

| Sprint | Objecti          | Tâches principales                                                  |
| ------ | ---------------- | ------------------------------------------------------------------- |
| 1      | Conception       | UML (cas d’usage, classes), structure JSON, règles métier           |
| 2      | Backend Auth     | Modèles `User`/`Admin`, `AuthController`, tests login/inscription   |
| 3      | Backend Films    | Modèle `Film`, `FilmController`, ajout, validation, logs, recherche |
| 4      | Intégration JSON | Lecture/écriture des fichiers JSON, sauvegarde sécurisée            |
| 5      | Tests backend    | Test complet du workflow utilisateur/admin, logs et doublons        |
| 6      | Frontend         | Interface PyQt : login, recherche, détails film, lecture vidéo      |
| 7      | Finitions        | Ajout posters/trailers, stylisation, README final, tests finaux     |

---

## 🛠️ Organisation du projet

film_finder/
├── core/ # Backend : modèles et contrôleurs
│ ├── models.py
│ ├── controllers.py
│ └── database.py
├── data/ # JSON pour stocker utilisateurs et films
│ ├── users.json
│ └── films.json
├── assets/ # Images / vidéos
├── main.py # Point d'entrée de l'application
├── requirements.txt # Dépendances Python
└── .gitignore # Fichiers à ignorer par Git

---

## ⚙️ Tâches principales à faire

1. **Backend Auth**
   - [x] Implémenter `User` et `Admin` avec héritage
   - [x] Vérification mot de passe sécurisé
   - [x] `AuthController` avec `register`, `login`, `logout`
   - [ ] Tests unitaires pour l’authentification
   - [x] Gestion des sessions utilisateurs
2. **Backend Films**
   - [x] Implémenter `Film` avec `approved`, `added_by_user_id`, `logs`
   - [x] `FilmController` : ajout, validation, modification, suppression
   - [ ] Vérifier les doublons avant ajout
   - [x] Historique des actions (logs)
   - [x] Recherche par titre, genre, date
3. **Persistance JSON**
   - [ ] Lire/écrire `users.json` et `films.json` avec backup
   - [ ] Sauvegarde automatique après chaque modification
   - [ ] Gestion des erreurs de lecture/écriture
4. **Tests backend**
   - [ ] Tester login, ajout film, validation admin, recherche
   - [ ] Vérifier logs et gestion doublons
   - [ ] Couverture de code minimale de 80%
   - [ ] Utiliser `unittest` ou `pytest`
5. **Frontend**
   - [ ] PyQt : login, recherche, détails film
   - [ ] Lecture vidéo via `QMediaPlayer`
   - [ ] Affichage poster
   - [ ] Différencier vues admin/utilisateur
   - [ ] Gestion des erreurs et messages utilisateur
   - [ ] Tests d’intégration frontend-backend
   - [ ] Navigation fluide entre les écrans
   - [ ] Responsive design pour différentes résolutions
   - [ ] Accessibilité (support clavier, lecteurs d’écran)
6. **Finitions**
   - [ ] Stylisation PyQt (QSS)
   - [ ] Ajout 20 films récents et posters
   - [ ] Documentation finale en portugais et en anglais
   - [ ] Tests finaux de bout en bout
   - [ ] Préparation pour déploiement
   - [ ] Revue de code et nettoyage
   - [ ] Création du README final
   - [ ] Licence MIT

---

## 📝 Instructions pratiques

### Créer un environnement Python

```bash
python -m venv venv # Crée un environnement virtuel
source venv/bin/activate  # Windows : venv\Scripts\activate
pip install -r requirements.txt # Installe les dépendances
```

### Lancer l'application

```bash
python main.py
```

### Exécuter les tests

```bash
python -m unittest discover tests
```

---

## 🤝 Contribution

Aucune contribution externe n'est prévue pour ce projet, mais les suggestions sont les bienvenues !

---

## 📄 Licences

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.
