import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QComboBox, QScrollArea,
                             QGridLayout, QFrame, QCheckBox, QGroupBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

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

        # Barre de recherche
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
        self.search_input.returnPressed.connect(self.perform_search)
        layout.addWidget(self.search_input)

        # Bouton recherche
        search_btn = QPushButton("🔎")
        search_btn.setFixedSize(40, 40)
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #e50914;
                border: none;
                border-radius: 20px;
                color: white;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #f40612;
            }
        """)
        search_btn.clicked.connect(self.perform_search)
        layout.addWidget(search_btn)

        layout.addStretch()

        # Filtres avancés (bouton toggle)
        self.filters_btn = QPushButton("🎛️ Filtres")
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
        if hasattr(self, 'filters_panel') and self.filters_panel:
            return

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
        title = QLabel("Filtres avancés")
        title.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Genre
        layout.addWidget(QLabel("Genre:"))
        self.genre_combo = QComboBox()
        self.genre_combo.addItem("Tous les genres", "")
        for genre in self.genres:
            self.genre_combo.addItem(genre, genre)
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
        layout.addWidget(QLabel("Année:"))
        self.year_combo = QComboBox()
        self.year_combo.addItem("Toutes les années", "")
        for year in self.years:
            self.year_combo.addItem(str(year), year)
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
            del self.filters_panel

    def apply_filters(self):
        """Applique les filtres et lance la recherche"""
        criteria = {
            'title': self.search_input.text().strip() or None,
            'genre': self.genre_combo.currentData() or None,
            'year': self.year_combo.currentData() or None
        }

        self.search_requested.emit(criteria)
        self.hide_advanced_filters()
        self.filters_btn.setChecked(False)

    def clear_filters(self):
        """Réinitialise tous les filtres"""
        self.search_input.clear()
        self.genre_combo.setCurrentIndex(0)
        self.year_combo.setCurrentIndex(0)

        criteria = {'title': None, 'genre': None, 'year': None}
        self.search_requested.emit(criteria)

    def perform_search(self):
        """Lance la recherche avec les critères actuels"""
        criteria = {
            'title': self.search_input.text().strip() or None,
            'genre': getattr(self, 'genre_combo', None) and self.genre_combo.currentData() or None,
            'year': getattr(self, 'year_combo', None) and self.year_combo.currentData() or None
        }
        self.search_requested.emit(criteria)
