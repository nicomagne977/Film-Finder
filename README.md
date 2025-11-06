# Film Finder

Film Finder is a Python application built with **PyQt5** that allows users to search, propose, and manage movies.
Data is stored in **JSON**, and all actions (authentication, film management, admin validation) are logged.

The app supports user authentication, movie searching, admin moderation, poster display, and MP4 trailer playback.

---

## Features

### Authentication

- Secure password rules (uppercase, number, special char, username not allowed in password)
- User & Admin roles (inheritance-based models)
- Registration, login, logout
- Session management
- JSON-based user storage

### Movie Management

- Add, edit, delete movies
- Admin validation
- Duplicate movie prevention
- Search by **title**, **genre**, and **release year**
- Display poster images
- Trailer playback through MP4 video stream (`QMediaPlayer`)
- Detailed action logs per movie

### Data Storage (JSON)

- Safe read/write with backup
- Auto-saving after each modification
- Error handling on corrupted files

### Testing

- Unit tests for authentication and movie workflows
- Search feature testing
- Duplicate detection checks
- Logs integrity tests
- Test coverage target ≥ 80%
- Compatible with `unittest` or `pytest`

### Frontend (PyQt)

- Login screen
- Movie search interface
- Movie details window
- Admin dashboard
- Poster display widget
- Video trailer player
- Full error handling
- Accessible UI (keyboard navigation, screen-reader-friendly)
- Responsive layout for multiple resolutions

### Final Touches

- QSS visual styling
- Included asset library: 20 sample recent movies with posters
- Complete documentation (English & Portuguese)
- MIT license
- Ready for packaging/distribution

---

## Project Structure

film_finder/
├── core/
│ ├── models.py # User, Admin, Movie models
│ ├── controllers.py # AuthController, FilmController
│ └── database.py # JSON persistence handler
├── data/
│ ├── users.json
│ └── films.json
├── assets/ # Posters, trailers, icons
├── tests/ # Unit tests
├── main.py # Application entry point
├── requirements.txt
└── README.md

---

## Installation

### 1. Create & activate a virtual environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
python main.py
```

## Agile Methodology

Film Finder follows an Agile workflow with short sprints and iterative refinement.

🗂️ Sprint Overview
Sprint Objective Key Tasks
1 Design UML, JSON structure, business rules
2 Auth Backend User/Admin models, AuthController, secure passwords
3 Movie Backend Movie model, controller, logs, search
4 JSON Persistence Read/write, autosave, backups
5 Backend Testing Full workflow tests, duplicates, logs
6 Frontend PyQt UI screens, video, admin/user separation
7 Finalization Styling, assets, docs, end-to-end tests, packaging

## Contribution

This is currently a closed project, but suggestions and improvement ideas are welcome.

## License

This project is licensed under the MIT License.
Refer to the LICENSE file for full details.

## Author

Film Finder — 2025
Developed with passion using Python, PyQt, and JSON.
