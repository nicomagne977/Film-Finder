import sys
import os
from datetime import date
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QMessageBox, QTabWidget, QTextEdit, QDialog, QDialogButtonBox,
    QSizePolicy, QFormLayout, QComboBox, QDateEdit, QGridLayout, QScrollArea,
    QFrame
)
from PyQt5.QtCore import Qt, QDate, QSize, pyqtSignal, QUrl, QPropertyAnimation, QEasingCurve, pyqtProperty, QTimer
try:
    from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
    from PyQt5.QtMultimediaWidgets import QVideoWidget
    HAVE_VIDEO = True
except Exception:
    HAVE_VIDEO = False
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPainter, QPainterPath, QColor, QBrush

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.filmcontroller import FilmController
from core.admins import Admin

class NetflixPosterCard(QLabel):
    """Carte de poster style Netflix avec animations au hover"""

    clicked = pyqtSignal(object)

    def __init__(self, film, width=180, height=270, parent=None):
        super().__init__(parent)
        self.film = film
        self.width = width
        self.height = height
        self._scale = 1.0

        # Animations
        self.scale_animation = QPropertyAnimation(self, b"scale")
        self.scale_animation.setDuration(200)
        self.scale_animation.setEasingCurve(QEasingCurve.OutCubic)

        self.setFixedSize(width, height)
        self.setScaledContents(True)
        self.setStyleSheet("""
            NetflixPosterCard {
                border-radius: 8px;
                background-color: #2d2d2d;
            }
        """)

        self.load_poster()

    def load_poster(self):
        """Charge l'image du poster"""
        poster_path = getattr(self.film, 'poster_path', '')
        placeholder_text = self.film.title if hasattr(self.film, 'title') else 'No Poster'

        if poster_path and os.path.exists(poster_path):
            pixmap = QPixmap(poster_path)
        else:
            # Créer un placeholder
            pixmap = QPixmap(self.width, self.height)
            pixmap.fill(QColor('#2d2d2d'))

            painter = QPainter(pixmap)
            painter.setPen(QColor('#666666'))
            painter.setFont(QFont('Arial', 10, QFont.Weight.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, placeholder_text)
            painter.end()

        # Appliquer des coins arrondis
        rounded_pixmap = self._make_rounded_pixmap(pixmap, 8)
        self.setPixmap(rounded_pixmap)

    def _make_rounded_pixmap(self, pixmap, radius):
        """Crée un pixmap avec coins arrondis"""
        scaled_pixmap = pixmap.scaled(self.width, self.height, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        rounded_pixmap = QPixmap(self.width, self.height)
        rounded_pixmap.fill(Qt.transparent)

        painter = QPainter(rounded_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width, self.height, radius, radius)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, scaled_pixmap)
        painter.end()

        return rounded_pixmap

    @pyqtProperty(float)
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        self._scale = value
        self.setFixedSize(int(self.width * value), int(self.height * value))

    def enterEvent(self, event):
        """Animation d'entrée - zoom"""
        self.scale_animation.setStartValue(1.0)
        self.scale_animation.setEndValue(1.1)
        self.scale_animation.start()

        # Afficher info-bulle
        self.setToolTip(f"{self.film.title}\n{self.film.genre} • {self.film.release_date.year}")

        super().enterEvent(event)

    def leaveEvent(self, event):
        """Animation de sortie"""
        self.scale_animation.setStartValue(1.1)
        self.scale_animation.setEndValue(1.0)
        self.scale_animation.start()

        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Gère les clics"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.film)
        super().mousePressEvent(event)

class NetflixRow(QWidget):
    """Une rangée Netflix horizontale avec titre et défilement"""

    def __init__(self, title, films, on_film_click, parent=None):
        super().__init__(parent)
        self.films = films
        self.on_film_click = on_film_click
        self.setFixedHeight(320)

        self.init_ui(title)

    def init_ui(self, title):
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 10, 40, 10)
        layout.setSpacing(10)

        # Titre de la rangée
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: bold;
                padding: 5px 0px;
            }
        """)
        layout.addWidget(title_label)

        # Zone de défilement horizontale
        self.scroll_area = QScrollArea()
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:horizontal {
                background-color: #2d2d2d;
                height: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background-color: #555555;
                border-radius: 4px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #777777;
            }
        """)

        # Conteneur pour les posters
        self.posters_container = QWidget()
        self.posters_layout = QHBoxLayout()
        self.posters_layout.setSpacing(15)
        self.posters_layout.setContentsMargins(10, 5, 10, 15)

        self.create_posters()

        self.posters_container.setLayout(self.posters_layout)
        self.scroll_area.setWidget(self.posters_container)

        layout.addWidget(self.scroll_area)
        self.setLayout(layout)

    def create_posters(self):
        """Crée les posters pour cette rangée"""
        for film in self.films[:20]:  # Limite à 20 films par rangée
            poster = NetflixPosterCard(film, 160, 240)
            poster.clicked.connect(self.on_film_click)
            self.posters_layout.addWidget(poster)

class NetflixSearchHeader(QWidget):
    """Header style Netflix avec barre de recherche"""

    search_requested = pyqtSignal(dict)  # Émet les critères de recherche

    def __init__(self, film_controller, parent=None):
        super().__init__(parent)
        self.film_controller = film_controller
        self.setFixedHeight(80)
        self.setStyleSheet("""
            NetflixSearchHeader {
                background-color: rgba(20, 20, 20, 0.95);
                border-bottom: 1px solid #2a2a2a;
            }
        """)

        # Variables pour stocker les filtres actuels
        self.current_genre = None
        self.current_year = None

        self.init_ui()
        self.load_filter_data()

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(15)

        # Logo
        logo = QLabel("FILM FINDER")
        logo.setStyleSheet("""
            QLabel {
                color: #e50914;
                font-size: 24px;
                font-weight: bold;
                font-family: 'Arial Black';
                padding: 5px 0px;
            }
        """)
        layout.addWidget(logo)

        # Barre de recherche avec recherche en temps réel
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Rechercher des films...")
        self.search_input.setFixedWidth(300)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d2d;
                border: 2px solid #424242;
                border-radius: 20px;
                padding: 8px 16px;
                color: #ffffff;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #e50914;
                background-color: #363636;
            }
            QLineEdit::placeholder {
                color: #888888;
            }
        """)
        self.search_input.textChanged.connect(self.on_text_changed)
        self.search_input.returnPressed.connect(self.perform_search)
        layout.addWidget(self.search_input)

        # Timer pour la recherche en temps réel (évite les recherches trop fréquentes)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

        # Bouton recherche
        search_btn = QPushButton("Rechercher")
        search_btn.setFixedSize(100, 40)
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #e50914;
                border: none;
                border-radius: 20px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f40612;
            }
        """)
        search_btn.clicked.connect(self.perform_search)
        layout.addWidget(search_btn)

        layout.addStretch()

        # Filtres avancés (bouton toggle)
        self.filters_btn = QPushButton("Filtres")
        self.filters_btn.setCheckable(True)
        self.filters_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px 16px;
                color: #ffffff;
            }
            QPushButton:checked {
                background-color: #e50914;
                border-color: #e50914;
            }
            QPushButton:hover {
                border-color: #e50914;
            }
        """)
        self.filters_btn.toggled.connect(self.toggle_filters)
        layout.addWidget(self.filters_btn)

        self.setLayout(layout)

    def on_text_changed(self, text):
        """Déclenche la recherche après un délai"""
        self.search_timer.stop()
        if text.strip():  # Ne recherche que si du texte est saisi
            self.search_timer.start(300)  # 300ms de délai

    def load_filter_data(self):
        """Charge les données pour les filtres"""
        try:
            films = self.film_controller.get_all_films()

            # Genres uniques
            self.genres = sorted(set(film.genre for film in films if hasattr(film, 'genre') and film.genre))

            # Années uniques
            self.years = sorted(set(film.release_date.year for film in films if hasattr(film, 'release_date')), reverse=True)

        except Exception as e:
            print(f"Erreur chargement données filtres: {e}")
            self.genres = []
            self.years = []

    def toggle_filters(self, checked):
        """Affiche/masque les filtres avancés"""
        if checked:
            self.show_advanced_filters()
        else:
            self.hide_advanced_filters()

    def show_advanced_filters(self):
        """Affiche le panneau de filtres avancés"""
        # Supprimer l'ancien panneau s'il existe
        if hasattr(self, 'filters_panel'):
            self.filters_panel.deleteLater()

        self.filters_panel = QFrame(self.parent())
        self.filters_panel.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 1px solid #2d2d2d;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        self.filters_panel.setFixedWidth(300)

        layout = QVBoxLayout()

        # Titre
        title = QLabel("Filtres avances")
        title.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Genre
        layout.addWidget(QLabel("Genre:"))
        self.genre_combo = QComboBox()
        self.genre_combo.addItem("Tous les genres", "")
        for genre in self.genres:
            self.genre_combo.addItem(genre, genre)
        # Restaurer la sélection précédente
        if self.current_genre:
            index = self.genre_combo.findData(self.current_genre)
            if index >= 0:
                self.genre_combo.setCurrentIndex(index)
        self.genre_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #424242;
                border-radius: 4px;
                padding: 6px;
                color: #ffffff;
            }
        """)
        layout.addWidget(self.genre_combo)

        # Année
        layout.addWidget(QLabel("Annee:"))
        self.year_combo = QComboBox()
        self.year_combo.addItem("Toutes les annees", "")
        for year in self.years:
            self.year_combo.addItem(str(year), year)
        # Restaurer la sélection précédente
        if self.current_year:
            index = self.year_combo.findData(self.current_year)
            if index >= 0:
                self.year_combo.setCurrentIndex(index)
        self.year_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #424242;
                border-radius: 4px;
                padding: 6px;
                color: #ffffff;
            }
        """)
        layout.addWidget(self.year_combo)

        # Boutons
        btn_layout = QHBoxLayout()
        apply_btn = QPushButton("Appliquer")
        apply_btn.clicked.connect(self.apply_filters)
        clear_btn = QPushButton("Effacer")
        clear_btn.clicked.connect(self.clear_filters)

        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #e50914;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f40612;
            }
        """)

        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #555555;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #666666;
            }
        """)

        btn_layout.addWidget(apply_btn)
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)

        self.filters_panel.setLayout(layout)

        # Positionner sous le bouton filtres
        pos = self.filters_btn.mapToGlobal(self.filters_btn.rect().bottomLeft())
        parent_pos = self.parent().mapFromGlobal(pos)
        self.filters_panel.move(parent_pos.x(), parent_pos.y() + 5)
        self.filters_panel.show()

    def hide_advanced_filters(self):
        """Masque le panneau de filtres"""
        if hasattr(self, 'filters_panel'):
            self.filters_panel.hide()
            self.filters_panel.deleteLater()
            delattr(self, 'filters_panel')

    def apply_filters(self):
        """Applique les filtres et lance la recherche"""
        # Sauvegarder les filtres actuels
        self.current_genre = self.genre_combo.currentData()
        self.current_year = self.year_combo.currentData()

        criteria = {
            'title': self.search_input.text().strip() or None,
            'genre': self.current_genre,
            'year': self.current_year
        }

        self.search_requested.emit(criteria)
        self.hide_advanced_filters()
        self.filters_btn.setChecked(False)

    def clear_filters(self):
        """Réinitialise tous les filtres"""
        self.search_input.clear()
        self.genre_combo.setCurrentIndex(0)
        self.year_combo.setCurrentIndex(0)
        self.current_genre = None
        self.current_year = None

        criteria = {'title': None, 'genre': None, 'year': None}
        self.search_requested.emit(criteria)

    def perform_search(self):
        """Lance la recherche avec les critères actuels"""
        try:
            # Utiliser les filtres sauvegardés au lieu d'accéder directement aux combobox
            criteria = {
                'title': self.search_input.text().strip() or None,
                'genre': self.current_genre,
                'year': self.current_year
            }
            self.search_requested.emit(criteria)
        except Exception as e:
            print(f"Erreur lors de la recherche: {e}")

class NetflixGridView(QWidget):
    """Vue principale style Netflix avec plusieurs rangées"""

    def __init__(self, film_controller, on_film_click, parent=None):
        super().__init__(parent)
        self.film_controller = film_controller
        self.on_film_click = on_film_click

        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Zone de défilement principale
        self.main_scroll = QScrollArea()
        self.main_scroll.setWidgetResizable(True)
        self.main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.main_scroll.setStyleSheet("""
            QScrollArea {
                background-color: #141414;
                border: none;
            }
        """)

        # Conteneur pour les rangées
        self.rows_container = QWidget()
        self.rows_layout = QVBoxLayout()
        self.rows_layout.setSpacing(0)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)

        self.rows_container.setLayout(self.rows_layout)
        self.main_scroll.setWidget(self.rows_container)

        layout.addWidget(self.main_scroll)
        self.setLayout(layout)

    def load_data(self):
        """Charge les données et crée les rangées"""
        # Nettoyer les anciennes rangées
        for i in reversed(range(self.rows_layout.count())):
            item = self.rows_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

        try:
            # Récupérer tous les films approuvés
            all_films = self.film_controller.get_approved_films()

            if not all_films:
                # Aucun film trouvé
                no_films_label = QLabel("Aucun film disponible\nCommencez par proposer des films !")
                no_films_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_films_label.setStyleSheet("""
                    QLabel {
                        color: #888888;
                        font-size: 18px;
                        padding: 50px;
                        background-color: #1a1a1a;
                        border-radius: 8px;
                        margin: 20px;
                    }
                """)
                self.rows_layout.addWidget(no_films_label)
                return

            # Créer différentes catégories (sans emojis)
            categories = {
                "Tendances actuelles": all_films[:10],
                "Populaire sur Film Finder": all_films[5:15],
                "Nouveaux films": sorted(all_films, key=lambda x: x.release_date, reverse=True)[:10],
                "Recommandé pour vous": all_films[8:18],
            }

            # Ajouter des rangées par genre
            genres = sorted(set(film.genre for film in all_films if hasattr(film, 'genre')))
            for genre in genres[:4]:  # Maximum 4 genres
                genre_films = [f for f in all_films if getattr(f, 'genre', '') == genre]
                if genre_films:
                    categories[f"{genre}"] = genre_films[:12]

            # Créer les rangées
            for title, films in categories.items():
                if films:  # Ne créer que si il y a des films
                    row = NetflixRow(title, films, self.on_film_click)
                    self.rows_layout.addWidget(row)

            self.rows_layout.addStretch()

        except Exception as e:
            error_label = QLabel(f"Erreur lors du chargement des films:\n{str(e)}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("""
                QLabel {
                    color: #ff6b6b;
                    font-size: 14px;
                    padding: 30px;
                    background-color: #2d1a1a;
                    border-radius: 8px;
                    margin: 20px;
                }
            """)
            self.rows_layout.addWidget(error_label)

class FilmViewDialog(QDialog):
    """Read-only film viewer"""

    def __init__(self, film, parent=None):
        super().__init__(parent)
        self.film = film
        self.setWindowTitle(film.title)
        self.setMinimumSize(480, 360)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        title = QLabel(self.film.title)
        title.setFont(QFont('Arial', 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # Poster + description
        hl = QHBoxLayout()
        poster = QLabel()
        poster.setFixedSize(160, 240)
        poster.setScaledContents(True)
        try:
            if self.film.poster_path and os.path.exists(self.film.poster_path):
                poster.setPixmap(QPixmap(self.film.poster_path))
        except Exception:
            pass
        hl.addWidget(poster)

        desc = QTextEdit()
        desc.setReadOnly(True)
        desc.setText(self.film.description or '(Pas de description)')
        desc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        hl.addWidget(desc)

        layout.addLayout(hl)

        btns = QHBoxLayout()
        btns.addStretch()
        close = QPushButton('Fermer')
        close.clicked.connect(self.accept)
        btns.addWidget(close)
        layout.addLayout(btns)

        self.setLayout(layout)

class FilmEditDialog(QDialog):
    """Dialog to propose a new film (or edit if needed)."""

    def __init__(self, film_controller: FilmController, by_user, film=None, parent=None):
        super().__init__(parent)
        self.film_controller = film_controller
        self.by_user = by_user
        self.film = film
        self.is_edit = film is not None
        self.setWindowTitle('Modifier le film' if self.is_edit else 'Proposer un film')
        self.setMinimumSize(480, 520)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.title_input = QLineEdit()
        self.genre_combo = QComboBox()
        self.genre_combo.addItems(["Action", "Comedie", "Drame", "Science-Fiction", "Horreur", "Romance", "Thriller", "Animation", "Documentaire", "Aventure"])
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.desc_input = QTextEdit()
        self.poster_input = QLineEdit()
        self.trailer_input = QLineEdit()

        if self.is_edit:
            self.title_input.setText(self.film.title)
            idx = self.genre_combo.findText(self.film.genre)
            if idx >= 0:
                self.genre_combo.setCurrentIndex(idx)
            self.date_input.setDate(QDate(self.film.release_date.year, self.film.release_date.month, self.film.release_date.day))
            self.desc_input.setText(self.film.description)
            self.poster_input.setText(self.film.poster_path)
            self.trailer_input.setText(self.film.trailer_url)

        form.addRow('Titre*:', self.title_input)
        form.addRow('Genre*:', self.genre_combo)
        form.addRow('Date de sortie*:', self.date_input)
        form.addRow('Description:', self.desc_input)
        form.addRow('Poster (chemin):', self.poster_input)
        form.addRow('Trailer (URL):', self.trailer_input)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def on_accept(self):
        title = self.title_input.text().strip()
        genre = self.genre_combo.currentText()
        qdate = self.date_input.date()
        release_date = date(qdate.year(), qdate.month(), qdate.day())
        description = self.desc_input.toPlainText().strip()
        poster = self.poster_input.text().strip()
        trailer = self.trailer_input.text().strip()

        if not title or not genre:
            QMessageBox.warning(self, 'Erreur', 'Titre et genre requis')
            return

        film_data = {
            'title': title,
            'genre': genre,
            'release_date': release_date,
            'description': description,
            'poster_path': poster,
            'trailer_url': trailer
        }

        if self.is_edit:
            QMessageBox.information(self, 'Info', 'Modification via l interface admin')
            self.reject()
            return
        else:
            ok = self.film_controller.add_film(film_data, self.by_user)
            if ok:
                QMessageBox.information(self, 'Succès', 'Film proposé (en attente de validation)')
                self.accept()
            else:
                QMessageBox.critical(self, 'Erreur', 'Echec lors de la proposition du film')

class MainWindow(QMainWindow):
    """Main window with Netflix-like interface"""

    logout_signal = pyqtSignal()

    def __init__(self, user):
        super().__init__()
        self.user = user
        self.film_controller = FilmController()

        self.setWindowTitle(f'Film Finder - {getattr(user, "username", "Invité")}')
        self.setMinimumSize(1200, 800)
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Header Netflix avec recherche
        self.header = NetflixSearchHeader(self.film_controller)
        self.header.search_requested.connect(self.on_search_requested)
        self.main_layout.addWidget(self.header)

        # Vue principale Netflix
        self.netflix_view = NetflixGridView(self.film_controller, self.on_film_clicked)
        self.main_layout.addWidget(self.netflix_view)

        # Footer avec déconnexion
        footer = QWidget()
        footer.setFixedHeight(50)
        footer.setStyleSheet("background-color: #141414; border-top: 1px solid #2a2a2a;")
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(20, 5, 20, 5)

        user_info = QLabel(f'Connecté en tant que: {getattr(self.user, "username", "Invité")}')
        user_info.setStyleSheet("color: #888888;")
        footer_layout.addWidget(user_info)

        footer_layout.addStretch()

        logout_btn = QPushButton('Se deconnecter')
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #e50914;
                border-radius: 4px;
                padding: 6px 12px;
                color: #e50914;
            }
            QPushButton:hover {
                background-color: #e50914;
                color: white;
            }
        """)
        logout_btn.clicked.connect(self.on_logout_clicked)
        footer_layout.addWidget(logout_btn)

        footer.setLayout(footer_layout)
        self.main_layout.addWidget(footer)

        central.setLayout(self.main_layout)

        # Charger le style
        self.load_styles()

    def load_styles(self):
        """Charge le style QSS Netflix"""
        try:
            qss_path = os.path.join(os.path.dirname(__file__), 'style.qss')
            if os.path.exists(qss_path):
                with open(qss_path, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Erreur chargement style: {e}")

    def on_search_requested(self, criteria):
        """Gère les requêtes de recherche"""
        try:
            # Adapter les critères pour FilmController
            title = criteria.get('title')
            genre = criteria.get('genre')
            year = criteria.get('year')

            # Utiliser la méthode search_films existante
            films = self.film_controller.search_films(
                title=title,
                genre=genre,
                approved_only=True
            )

            # Filtrer par année si spécifiée
            if year:
                films = [f for f in films if hasattr(f, 'release_date') and f.release_date.year == year]

            # Afficher les résultats
            self.show_search_results(films, criteria)

        except Exception as e:
            print(f"Erreur recherche: {e}")
            self.show_error_message(f"Erreur lors de la recherche: {e}")

    def show_error_message(self, message):
        """Affiche un message d'erreur stylisé"""
        error_msg = QMessageBox(self)
        error_msg.setWindowTitle("Erreur")
        error_msg.setText(message)
        error_msg.setStyleSheet("""
            QMessageBox {
                background-color: #141414;
                color: #ffffff;
            }
            QMessageBox QLabel {
                color: #ffffff;
                background-color: #141414;
            }
            QMessageBox QPushButton {
                background-color: #e50914;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #f40612;
            }
        """)
        error_msg.exec_()

    def show_search_results(self, films, criteria):
        """Affiche les résultats de recherche"""
        # Cache la vue Netflix normale
        self.netflix_view.hide()

        # Supprimer l'ancienne vue de résultats si elle existe
        if hasattr(self, 'search_results_view'):
            self.search_results_view.hide()
            self.main_layout.removeWidget(self.search_results_view)
            self.search_results_view.deleteLater()

        # Crée une nouvelle vue de résultats
        self.search_results_view = QWidget()
        search_results_layout = QVBoxLayout()
        search_results_layout.setContentsMargins(0, 0, 0, 0)
        search_results_layout.setSpacing(0)
        self.search_results_view.setLayout(search_results_layout)

        # Titre des résultats
        results_title = QLabel(f"Resultats de recherche ({len(films)} films trouves)")
        results_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
                padding: 20px;
                background-color: #1a1a1a;
            }
        """)
        search_results_layout.addWidget(results_title)

        # Bouton retour
        back_btn = QPushButton("Retour a l'accueil")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #e50914;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: white;
                font-weight: bold;
                margin: 0px 20px 20px 20px;
            }
            QPushButton:hover {
                background-color: #f40612;
            }
        """)
        back_btn.clicked.connect(self.show_main_view)
        search_results_layout.addWidget(back_btn)

        # Grille de résultats
        if films:
            results_container = QWidget()
            results_layout = QVBoxLayout()
            results_container.setLayout(results_layout)

            results_grid = QWidget()
            grid_layout = QGridLayout()
            grid_layout.setSpacing(20)
            grid_layout.setContentsMargins(20, 20, 20, 20)
            results_grid.setLayout(grid_layout)

            thumb_w = 180
            thumb_h = 270
            cols = 6
            row = 0
            col = 0

            for film in films:
                poster = NetflixPosterCard(film, thumb_w, thumb_h)
                poster.clicked.connect(self.on_film_clicked)
                grid_layout.addWidget(poster, row, col)

                col += 1
                if col >= cols:
                    col = 0
                    row += 1

            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setWidget(results_grid)
            results_layout.addWidget(scroll_area)

            search_results_layout.addWidget(results_container)
        else:
            no_results = QLabel("Aucun film ne correspond a votre recherche")
            no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_results.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 18px;
                    padding: 50px;
                }
            """)
            search_results_layout.addWidget(no_results)

        # Ajouter la vue de résultats au layout principal
        self.main_layout.insertWidget(1, self.search_results_view)
        self.search_results_view.show()

    def show_main_view(self):
        """Retourne à la vue principale"""
        if hasattr(self, 'search_results_view'):
            self.search_results_view.hide()
            self.main_layout.removeWidget(self.search_results_view)
            self.search_results_view.deleteLater()
            delattr(self, 'search_results_view')
        self.netflix_view.show()

    def on_film_clicked(self, film):
        """Gère le clic sur un film"""
        FilmViewDialog(film, parent=self).exec()

    def on_logout_clicked(self):
        """Gère la déconnexion"""
        try:
            self.logout_signal.emit()
        except Exception:
            pass
        self.close()

def main():
    app = QApplication(sys.argv)
    try:
        from ui.login_window import LoginWindow
        login = LoginWindow()

        def _on_login(user):
            mw = MainWindow(user)
            mw.show()
            login.hide()

        login.login_success.connect(_on_login)
        login.show()
    except Exception:
        # fallback
        from core.users import User
        user = User.create_user(0, 'Dev', 'User', 'dev@local', 'dev', 'DevPass1!')
        window = MainWindow(user)
        window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
