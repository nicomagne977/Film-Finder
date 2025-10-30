import sys
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QScrollArea, QGridLayout, QSizePolicy)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath, QColor, QFont, QMouseEvent

class NetflixPosterCard(QLabel):
    """Carte de poster style Netflix avec animations au hover"""

    def __init__(self, film, width=180, height=270, parent=None):
        super().__init__(parent)
        self.film = film
        self.width = width
        self.height = height
        self._scale = 1.0
        self._y_offset = 0

        # Animations
        self.scale_animation = QPropertyAnimation(self, b"scale")
        self.scale_animation.setDuration(200)
        self.scale_animation.setEasingCurve(QEasingCurve.OutCubic)

        self.y_animation = QPropertyAnimation(self, b"y_offset")
        self.y_animation.setDuration(200)
        self.y_animation.setEasingCurve(QEasingCurve.OutCubic)

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

    @pyqtProperty(float)
    def y_offset(self):
        return self._y_offset

    @y_offset.setter
    def y_offset(self, value):
        self._y_offset = value
        current_pos = self.pos()
        self.move(current_pos.x(), int(current_pos.y() - value))

    def enterEvent(self, event):
        """Animation d'entrée - zoom et élévation"""
        self.scale_animation.setStartValue(1.0)
        self.scale_animation.setEndValue(1.1)
        self.scale_animation.start()

        self.y_animation.setStartValue(0)
        self.y_animation.setEndValue(20)  # Légère élévation
        self.y_animation.start()

        # Afficher info-bulle
        self.setToolTip(f"{self.film.title}\n{self.film.genre} • {self.film.release_date.year}")

        super().enterEvent(event)

    def leaveEvent(self, event):
        """Animation de sortie"""
        self.scale_animation.setStartValue(1.1)
        self.scale_animation.setEndValue(1.0)
        self.scale_animation.start()

        self.y_animation.setStartValue(20)
        self.y_animation.setEndValue(0)
        self.y_animation.start()

        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """Gère les clics"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
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
        layout.setContentsMargins(20, 10, 20, 10)
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
            poster.clicked.connect(lambda checked=False, f=film: self.on_film_click(f))
            self.posters_layout.addWidget(poster)

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
                no_films_label = QLabel("🎬 Aucun film disponible\nCommencez par proposer des films !")
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

            # Créer différentes catégories
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
            error_label = QLabel(f"❌ Erreur lors du chargement des films:\n{str(e)}")
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
