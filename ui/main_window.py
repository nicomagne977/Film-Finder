import sys
import os
import shutil
from datetime import date
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QMessageBox, QTabWidget, QTextEdit, QDialog, QDialogButtonBox,
    QSizePolicy, QFormLayout, QComboBox, QDateEdit, QGridLayout, QScrollArea,
    QFrame, QGroupBox
)
from PyQt5.QtCore import Qt, QDate, QSize, pyqtSignal, QUrl, QPropertyAnimation, QEasingCurve, pyqtProperty, QTimer
from PyQt5.QtCore import Qt, QCoreApplication
try:
    from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
    from PyQt5.QtMultimediaWidgets import QVideoWidget
    HAVE_VIDEO = True
except Exception:
    HAVE_VIDEO = False
# Ajoutez ces imports pour WebEngine
QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
    HAVE_WEBENGINE = True
    print("Import successful")
except ImportError:
    HAVE_WEBENGINE = False
    print("WebEngine import failed!")
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPainter, QPainterPath, QColor, QBrush

import subprocess
import tempfile
import os
import threading
from PyQt5.QtCore import QThread, pyqtSignal

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.filmcontroller import FilmController
from core.admins import Admin


class NetflixPosterCard(QLabel):
    """Netflix-style poster card with hover animations"""

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
        """Load poster image"""
        poster_path = getattr(self.film, 'poster_path', '')
        placeholder_text = self.film.title if hasattr(self.film, 'title') else 'No Poster'

        if poster_path and os.path.exists(poster_path):
            pixmap = QPixmap(poster_path)
        else:
            # Create placeholder
            pixmap = QPixmap(self.width, self.height)
            pixmap.fill(QColor('#2d2d2d'))

            painter = QPainter(pixmap)
            painter.setPen(QColor('#666666'))
            painter.setFont(QFont('Arial', 10, QFont.Weight.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, placeholder_text)
            painter.end()

        # Apply rounded corners
        rounded_pixmap = self._make_rounded_pixmap(pixmap, 8)
        self.setPixmap(rounded_pixmap)

    def _make_rounded_pixmap(self, pixmap, radius):
        """Create pixmap with rounded corners"""
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
        """Enter animation - zoom"""
        self.scale_animation.setStartValue(1.0)
        self.scale_animation.setEndValue(1.1)
        self.scale_animation.start()

        # Show tooltip
        self.setToolTip(f"{self.film.title}\n{self.film.genre} • {self.film.release_date.year}")

        super().enterEvent(event)

    def leaveEvent(self, event):
        """Leave animation"""
        self.scale_animation.setStartValue(1.1)
        self.scale_animation.setEndValue(1.0)
        self.scale_animation.start()

        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Handle clicks"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.film)
        super().mousePressEvent(event)

class NetflixRow(QWidget):
    """Horizontal Netflix row with title and scrolling"""

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

        # Row title
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

        # Horizontal scroll area
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

        # Container for posters
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
        """Create posters for this row"""
        for film in self.films[:20]:  # Limit to 20 films per row
            poster = NetflixPosterCard(film, 160, 240)
            poster.clicked.connect(self.on_film_click)
            self.posters_layout.addWidget(poster)

class NetflixSearchHeader(QWidget):
    """Netflix-style header with search bar"""

    search_requested = pyqtSignal(dict)  # Emits search criteria

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

        # Variables to store current filters
        self.current_genre = None
        self.current_year = None
        self.filters_panel = None

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

        # Search bar with real-time search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search movies...")
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

        # Timer for real-time search (avoids too frequent searches)
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)

        # Search button
        search_btn = QPushButton("Search")
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

        # Advanced filters (toggle button)
        self.filters_btn = QPushButton("Filters")
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
        """Triggers search after delay"""
        self.search_timer.stop()
        if text.strip():  # Only search if text is entered
            self.search_timer.start(300)  # 300ms delay

    def load_filter_data(self):
        """Load data for filters"""
        try:
            films = self.film_controller.get_all_films()

            # Unique genres
            self.genres = sorted(set(film.genre for film in films if hasattr(film, 'genre') and film.genre))

            # Unique years
            self.years = sorted(set(film.release_date.year for film in films if hasattr(film, 'release_date')), reverse=True)

        except Exception as e:
            print(f"Error loading filter data: {e}")
            self.genres = []
            self.years = []

    def toggle_filters(self, checked):
        """Show/hide advanced filters"""
        if checked:
            self.show_advanced_filters()
        else:
            self.hide_advanced_filters()

    def show_advanced_filters(self):
        """Show advanced filters panel"""
        # Remove old panel if exists
        if self.filters_panel:
            self.filters_panel.deleteLater()

        self.filters_panel = QFrame(self.window())
        self.filters_panel.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.filters_panel.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border: 2px solid #2d2d2d;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        self.filters_panel.setFixedSize(350, 250)

        layout = QVBoxLayout()

        # Title
        title = QLabel("Advanced Filters")
        title.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Genre
        layout.addWidget(QLabel("Genre:"))
        self.genre_combo = QComboBox()
        self.genre_combo.addItem("All genres", "")
        for genre in self.genres:
            self.genre_combo.addItem(genre, genre)
        # Restore previous selection
        if self.current_genre:
            index = self.genre_combo.findData(self.current_genre)
            if index >= 0:
                self.genre_combo.setCurrentIndex(index)
        self.genre_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #424242;
                border-radius: 4px;
                padding: 8px;
                color: #ffffff;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.genre_combo)

        # Year
        layout.addWidget(QLabel("Year:"))
        self.year_combo = QComboBox()
        self.year_combo.addItem("All years", "")
        for year in self.years:
            self.year_combo.addItem(str(year), year)
        # Restore previous selection
        if self.current_year:
            index = self.year_combo.findData(self.current_year)
            if index >= 0:
                self.year_combo.setCurrentIndex(index)
        self.year_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #424242;
                border-radius: 4px;
                padding: 8px;
                color: #ffffff;
                font-size: 14px;
            }
        """)
        layout.addWidget(self.year_combo)

        # Buttons
        btn_layout = QHBoxLayout()
        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.apply_filters)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear_filters)

        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #e50914;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                color: white;
                font-weight: bold;
                font-size: 14px;
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
                padding: 8px 16px;
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
        """)

        btn_layout.addWidget(apply_btn)
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)

        self.filters_panel.setLayout(layout)

        # Center window on screen
        window_rect = self.window().geometry()
        panel_width = self.filters_panel.width()
        panel_height = self.filters_panel.height()

        x = window_rect.x() + (window_rect.width() - panel_width) // 2
        y = window_rect.y() + (window_rect.height() - panel_height) // 3  # Slightly higher than center

        self.filters_panel.move(x, y)
        self.filters_panel.show()

    def hide_advanced_filters(self):
        """Hide filters panel"""
        if self.filters_panel:
            self.filters_panel.hide()
            self.filters_panel.deleteLater()
            self.filters_panel = None
        self.filters_btn.setChecked(False)

    def apply_filters(self):
        """Apply filters and launch search"""
        # Save current filters
        self.current_genre = self.genre_combo.currentData()
        self.current_year = self.year_combo.currentData()

        criteria = {
            'title': self.search_input.text().strip() or None,
            'genre': self.current_genre,
            'year': self.current_year
        }

        self.search_requested.emit(criteria)
        self.hide_advanced_filters()

    def clear_filters(self):
        """Reset all filters"""
        self.search_input.clear()
        self.current_genre = None
        self.current_year = None

        criteria = {'title': None, 'genre': None, 'year': None}
        self.search_requested.emit(criteria)
        self.hide_advanced_filters()

    def perform_search(self):
        """Perform search with current criteria"""
        try:
            # Use saved filters instead of accessing comboboxes directly
            criteria = {
                'title': self.search_input.text().strip() or None,
                'genre': self.current_genre,
                'year': self.current_year
            }
            self.search_requested.emit(criteria)
        except Exception as e:
            print(f"Search error: {e}")

class NetflixGridView(QWidget):
    """Main Netflix-style view with multiple rows"""

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

        # Main scroll area
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

        # Container for rows
        self.rows_container = QWidget()
        self.rows_layout = QVBoxLayout()
        self.rows_layout.setSpacing(0)
        self.rows_layout.setContentsMargins(0, 0, 0, 0)

        self.rows_container.setLayout(self.rows_layout)
        self.main_scroll.setWidget(self.rows_container)

        layout.addWidget(self.main_scroll)
        self.setLayout(layout)

    def load_data(self):
        """Load data and create rows"""
        # Clear old rows
        for i in reversed(range(self.rows_layout.count())):
            item = self.rows_layout.itemAt(i)
            if item.widget():
                item.widget().setParent(None)

        try:
            # Get all approved films
            all_films = self.film_controller.get_approved_films()

            if not all_films:
                # No films found
                no_films_label = QLabel("No movies available\nStart by suggesting movies!")
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

            # Create different categories (without emojis)
            categories = {
                "Current Trends": all_films[:10],
                "Popular on Film Finder": all_films[5:15],
                "New Movies": sorted(all_films, key=lambda x: x.release_date, reverse=True)[:10],
                "Recommended for You": all_films[8:18],
            }

            # Add rows by genre
            genres = sorted(set(film.genre for film in all_films if hasattr(film, 'genre')))
            for genre in genres[:4]:  # Maximum 4 genres
                genre_films = [f for f in all_films if getattr(f, 'genre', '') == genre]
                if genre_films:
                    categories[f"{genre}"] = genre_films[:12]

            # Create rows
            for title, films in categories.items():
                if films:  # Only create if there are films
                    row = NetflixRow(title, films, self.on_film_click)
                    self.rows_layout.addWidget(row)

            self.rows_layout.addStretch()

        except Exception as e:
            error_label = QLabel(f"Error loading movies:\n{str(e)}")
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

class VideoDownloadThread(QThread):
    """Thread to download video in background"""

    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, youtube_url):
        super().__init__()
        self.youtube_url = youtube_url
        self.temp_dir = "/mnt/c/Users/utilisateur/Desktop/UFSC/POO/Film_finder/data/"
        self.video_path = None

    def run(self):
        try:
            self.progress_signal.emit("📥 Downloading video...")

            # Unique temporary filename
            import uuid
            filename = f"film_finder_trailer.mp4"
            self.video_path = os.path.join(self.temp_dir, filename)

            # yt-dlp options
            ydl_opts = {
                'format': 'best[height<=720]',  # Max 720p quality
                'outtmpl': self.video_path,
                'quiet': True,
            }

            # Download
            import yt_dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.youtube_url])

            if os.path.exists(self.video_path):
                self.progress_signal.emit("✅ Video downloaded! Launching VLC...")
                self.finished_signal.emit(self.video_path)
            else:
                self.error_signal.emit("❌ Download failed")

        except Exception as e:
            self.error_signal.emit(f"❌ Error: {str(e)}")

class FilmViewDialog(QDialog):
    """Detailed film view with integrated VLC playback"""

    def __init__(self, film, parent=None):
        super().__init__(parent)
        self.film = film
        self.video_path = None
        self.download_thread = None
        self.vlc_process = None

        self.setWindowTitle(f"Film Finder - {film.title}")
        self.setMinimumSize(900, 700)
        self.setStyleSheet("""
            FilmViewDialog {
                background-color: #1a1a1a;
                color: #ffffff;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Main title
        title_label = QLabel(self.film.title)
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 28px;
                font-weight: bold;
                padding: 10px 0px;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Main container (poster + info + trailer)
        main_container = QHBoxLayout()
        main_container.setSpacing(30)

        # Left column - Poster and info
        left_column = QVBoxLayout()
        left_column.setSpacing(15)

        poster_label = QLabel()
        poster_label.setFixedSize(300, 450)
        poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        poster_label.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                border-radius: 8px;
                padding: 10px;
            }
        """)

        self.load_poster(poster_label)
        left_column.addWidget(poster_label)

        # Information under poster
        info_widget = QWidget()
        info_widget.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        info_layout = QVBoxLayout()

        # Genre
        genre_label = QLabel(f"<b>Genre:</b> {self.film.genre}")
        genre_label.setStyleSheet("color: #cccccc; font-size: 14px;")
        info_layout.addWidget(genre_label)

        # Release date
        release_date = self.film.release_date
        if hasattr(release_date, 'strftime'):
            date_str = release_date.strftime("%d/%m/%Y")
        else:
            date_str = str(release_date)
        date_label = QLabel(f"<b>Release Date:</b> {date_str}")
        date_label.setStyleSheet("color: #cccccc; font-size: 14px;")
        info_layout.addWidget(date_label)

        # Approval status
        status_label = QLabel(f"<b>Status:</b> {'Approved' if getattr(self.film, 'approved', False) else 'Pending'}")
        status_label.setStyleSheet("color: #cccccc; font-size: 14px;")
        info_layout.addWidget(status_label)

        info_widget.setLayout(info_layout)
        left_column.addWidget(info_widget)

        main_container.addLayout(left_column)

        # Right column - Description and Trailer
        right_column = QVBoxLayout()
        right_column.setSpacing(20)

        # Description
        desc_group = QWidget()
        desc_group.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-radius: 8px;
                padding: 0px;
            }
        """)
        desc_layout = QVBoxLayout()

        desc_title = QLabel("Description")
        desc_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 18px;
                font-weight: bold;
                padding: 15px 15px 5px 15px;
            }
        """)
        desc_layout.addWidget(desc_title)

        desc_text = QTextEdit()
        desc_text.setReadOnly(True)
        desc_text.setPlainText(self.film.description or "No description available.")
        desc_text.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                color: #cccccc;
                font-size: 14px;
                padding: 0px 15px 15px 15px;
                line-height: 1.4;
            }
        """)
        desc_text.setFixedHeight(150)
        desc_layout.addWidget(desc_text)

        desc_group.setLayout(desc_layout)
        right_column.addWidget(desc_group)

        # Trailer - Integrated VLC playback
        trailer_group = QWidget()
        trailer_group.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-radius: 8px;
                padding: 25px;
            }
        """)
        trailer_layout = QVBoxLayout()

        trailer_title = QLabel("Trailer")
        trailer_title.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 22px;
                font-weight: bold;
                margin-bottom: 20px;
                text-align: center;
            }
        """)
        trailer_layout.addWidget(trailer_title)

        if self.film.trailer_url:
            # Download and play button
            self.download_btn = QPushButton("🎬 Watch Trailer (VLC)")
            self.download_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e50914;
                    border: none;
                    border-radius: 8px;
                    padding: 15px 25px;
                    color: white;
                    font-weight: bold;
                    font-size: 16px;
                    margin: 10px;
                }
                QPushButton:hover:!disabled {
                    background-color: #f40612;
                }
                QPushButton:disabled {
                    background-color: #666666;
                    color: #aaaaaa;
                }
            """)
            self.download_btn.clicked.connect(self.download_and_play)
            trailer_layout.addWidget(self.download_btn)

            # Status label
            self.status_label = QLabel("Ready to download and play trailer")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #88ff88;
                    font-size: 12px;
                    padding: 10px;
                    background-color: #1a2a1a;
                    border-radius: 4px;
                    margin: 5px;
                }
            """)
            self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.status_label.setWordWrap(True)
            trailer_layout.addWidget(self.status_label)

            # Fallback button (browser)
            browser_btn = QPushButton("🌐 Open in Browser (fallback)")
            browser_btn.setStyleSheet("""
                QPushButton {
                    background-color: #555555;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 15px;
                    color: white;
                    font-weight: bold;
                    font-size: 12px;
                    margin-top: 10px;
                }
                QPushButton:hover {
                    background-color: #666666;
                }
            """)
            browser_btn.clicked.connect(self.open_in_browser)
            trailer_layout.addWidget(browser_btn)

        else:
            no_trailer_label = QLabel("No trailer available")
            no_trailer_label.setStyleSheet("color: #888888; padding: 40px;")
            no_trailer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            trailer_layout.addWidget(no_trailer_label)

        trailer_group.setLayout(trailer_layout)
        right_column.addWidget(trailer_group)

        main_container.addLayout(right_column)
        layout.addLayout(main_container)

        # Close buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton('Close')
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #e50914;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                color: white;
                font-weight: bold;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #f40612;
            }
        """)
        close_btn.clicked.connect(self.close_dialog)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def download_and_play(self):
        """Download and play video with VLC"""
        if not self.film.trailer_url:
            return

        # Disable button during download
        self.download_btn.setEnabled(False)
        self.status_label.setText("📥 Preparing download...")

        # Launch download in separate thread
        self.download_thread = VideoDownloadThread(self.film.trailer_url)
        self.download_thread.progress_signal.connect(self.update_status)
        self.download_thread.finished_signal.connect(self.launch_vlc)
        self.download_thread.error_signal.connect(self.download_error)
        self.download_thread.start()

    def update_status(self, message):
        """Update download status"""
        self.status_label.setText(message)

    def launch_vlc(self, video_path):
        """Launch VLC with downloaded video"""
        try:
            self.video_path = video_path
            self.status_label.setText("🚀 Launching VLC...")

            # Convert path for Windows if under WSL
            if os.name == 'posix' and '/mnt/c/' in video_path:
                vlc_path = video_path.replace("/mnt/c/", "C:\\").replace("/", "\\")
            else:
                vlc_path = video_path

            # Look for VLC in common locations
            vlc_executable = "/mnt/c/Program Files/VideoLAN/VLC/vlc.exe"

            if vlc_executable:
                # Launch VLC
                self.vlc_process = subprocess.Popen([vlc_executable, vlc_path])
                self.status_label.setText("✅ VLC launched! Video will be deleted on close.")

                # Re-enable button
                self.download_btn.setEnabled(True)
                self.download_btn.setText("🎬 Play Trailer Again")
            else:
                self.download_error("VLC not found. Install VLC or use browser button.")

        except Exception as e:
            self.download_error(f"VLC launch error: {str(e)}")

    def find_vlc(self):
        """Find VLC executable"""
        possible_paths = [
            # Windows
            "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
            "C:\\Program Files (x86)\\VideoLAN\\VLC\\vlc.exe",
            # Linux
            "/usr/bin/vlc",
            "/usr/local/bin/vlc",
            # WSL
            "/mnt/c/Program Files/VideoLAN/VLC/vlc.exe",
            "/mnt/c/Program Files (x86)/VideoLAN/VLC/vlc.exe",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def download_error(self, error_message):
        """Handle download errors"""
        self.status_label.setText(error_message)
        self.status_label.setStyleSheet("color: #ff8888; background-color: #2a1a1a; padding: 10px; border-radius: 4px;")
        self.download_btn.setEnabled(True)

    def open_in_browser(self):
        """Open trailer in browser (fallback)"""
        try:
            import webbrowser
            webbrowser.open(self.film.trailer_url)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Cannot open browser:\n{str(e)}")

    def load_poster(self, poster_label):
        """Load poster image"""
        poster_path = getattr(self.film, 'poster_path', '')

        if poster_path and os.path.exists(poster_path):
            pixmap = QPixmap(poster_path)
            scaled_pixmap = pixmap.scaled(280, 420, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            poster_label.setPixmap(scaled_pixmap)
        else:
            placeholder = QPixmap(280, 420)
            placeholder.fill(QColor('#2d2d2d'))

            painter = QPainter(placeholder)
            painter.setPen(QColor('#666666'))
            painter.setFont(QFont('Arial', 12, QFont.Weight.Bold))
            painter.drawText(placeholder.rect(), Qt.AlignmentFlag.AlignCenter, "Image not available")
            painter.end()

            poster_label.setPixmap(placeholder)

    def close_dialog(self):
        """Close dialog and clean temporary files"""
        # Stop download thread if running
        if self.download_thread and self.download_thread.isRunning():
            self.download_thread.terminate()
            self.download_thread.wait()

        # Delete temporary video file
        if self.video_path and os.path.exists(self.video_path):
            try:
                os.remove(self.video_path)
                print(f"✅ Temporary file deleted: {self.video_path}")
            except Exception as e:
                print(f"⚠️ Cannot delete file: {e}")

        # Close VLC if still open
        if self.vlc_process:
            try:
                self.vlc_process.terminate()
            except:
                pass

        self.accept()

class FilmEditDialog(QDialog):
    """Dialog to propose a new film (or edit if needed)."""

    def __init__(self, film_controller: FilmController, by_user, film=None, parent=None):
        super().__init__(parent)
        self.film_controller = film_controller
        self.by_user = by_user
        self.film = film
        self.is_edit = film is not None
        self.setWindowTitle('Edit Film' if self.is_edit else 'Suggest a Film')
        self.setMinimumSize(480, 520)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        # CSS style for white text
        white_style = "color: white;"

        self.title_input = QLineEdit()

        self.genre_combo = QComboBox()
        self.genre_combo.setStyleSheet(white_style)
        self.genre_combo.addItems(["Action", "Comedy", "Drama", "Science-Fiction", "Horror", "Romance", "Thriller", "Animation", "Documentary", "Adventure"])

        self.date_input = QDateEdit()
        self.date_input.setStyleSheet(white_style)
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

        # Apply white style to form labels
        form.addRow(self.create_white_label('Title*:'), self.title_input)
        form.addRow(self.create_white_label('Genre*:'), self.genre_combo)
        form.addRow(self.create_white_label('Release Date*:'), self.date_input)
        form.addRow(self.create_white_label('Description:'), self.desc_input)
        form.addRow(self.create_white_label('Poster (path):'), self.poster_input)
        form.addRow(self.create_white_label('Trailer (URL):'), self.trailer_input)

        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.setStyleSheet("""QDialogButtonBox {
            background-color: #1a1a1a;
            color: white;
        }""")
        buttons.accepted.connect(self.on_accept)
        buttons.rejected.connect(self.reject)

        # Optional: style buttons too
        buttons.setStyleSheet("QPushButton { color: white; }")

        layout.addWidget(buttons)

        self.setLayout(layout)

    def create_white_label(self, text):
        """Create QLabel with white text"""
        label = QLabel(text)
        label.setStyleSheet("color: white;")
        return label

    def on_accept(self):
        # Get form data
        title = self.title_input.text().strip()
        genre = self.genre_combo.currentText().strip()
        year_text = self.date_input.date().toPyDate()
        description = self.desc_input.toPlainText().strip()
        poster = self.poster_input.text().strip()
        trailer = self.trailer_input.text().strip()

        # Minimal validation
        if not title or not genre or not year_text or not description or not poster:
            self.show_error_message("All fields except trailer are required.")
            return

        # Prepare film data
        film_data = {
            "title": title,
            "genre": genre,
            "release_date": self.date_input.date().toPyDate(),
            "description": description,
            "trailer_url": trailer,
            "poster_path": None  # Will be updated after copy
        }

        # Handle poster
        if poster:
            poster_dest_dir = os.path.join(os.getcwd(), "data", "posters")
            os.makedirs(poster_dest_dir, exist_ok=True)
            filename = os.path.basename(poster)
            dest_path = os.path.join(poster_dest_dir, filename)
            try:
                shutil.copyfile(poster, dest_path)
                film_data['poster_path'] = dest_path
            except Exception as e:
                QMessageBox.warning(self, 'Warning', f"Cannot copy poster: {e}")
                QMessageBox.setStyleSheet("QMessageBox { background-color: #1a1a1a; color: white; }")

        # Add film via controller
        ok = self.film_controller.add_film(film_data, self.by_user)
        if not ok:
            self.show_error_message("Failed to add film.")
            return

        # Auto-approval if admin
        if hasattr(self.by_user, "is_admin") and self.by_user.is_admin:
            last_film = self.film_controller.get_last_added_film()
            self.film_controller.approve_film(last_film)
            QMessageBox.information(self, 'Success', 'Film added and automatically approved.')
            QMessageBox.setStyleSheet("QMessageBox { background-color: #1a1a1a; color: white; }")
            self.accept()
            return

        # Confirmation for standard user
        QMessageBox.information(self, 'Success', 'Film suggested (pending validation)')
        QMessageBox.setStyleSheet("QMessageBox { background-color: #1a1a1a; color: white; }")
        self.accept()

    def show_error_message(self, message):
        """Show error message"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle("Error")
        msg.exec_()

class AdminApprovalDialog(QDialog):
    film_approved = pyqtSignal()

    def __init__(self, film_controller, user, parent=None):
        super().__init__(parent)
        self.film_controller = film_controller
        self.by_user = user
        self.setWindowTitle("Approval Management")
        self.setMinimumSize(800, 500)
        self.setStyleSheet(self.get_netflix_style())
        self.init_ui()

    def get_netflix_style(self):
        return """
        QDialog {
            background-color: #141414;
            color: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
        }

        QListWidget {
            background-color: #2d2d2d;
            border: 2px solid #404040;
            border-radius: 8px;
            padding: 10px;
            color: #ffffff;
            font-size: 14px;
            outline: none;
        }

        QListWidget::item {
            background-color: #404040;
            border-radius: 6px;
            padding: 12px 15px;
            margin: 5px;
            border: 1px solid #555555;
        }

        QListWidget::item:hover {
            background-color: #525252;
            border: 1px solid #e50914;
        }

        QListWidget::item:selected {
            background-color: #e50914;
            border: 1px solid #e50914;
        }

        QPushButton {
            background-color: #e50914;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: bold;
            min-width: 120px;
        }

        QPushButton:hover {
            background-color: #f40612;
            transform: scale(1.05);
        }

        QPushButton:pressed {
            background-color: #b8070f;
        }

        QPushButton:focus {
            outline: none;
            border: 2px solid #ffffff;
        }

        QLabel {
            color: #ffffff;
            font-size: 14px;
            padding: 5px;
        }
        """

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title_label = QLabel("Pending Film Approvals")
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
                padding: 10px 0px;
                border-bottom: 2px solid #e50914;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # List of pending films
        self.pending_list = QListWidget()
        self.pending_list.setSelectionMode(QListWidget.SingleSelection)

        pending_films = self.film_controller.get_pending_films()
        if pending_films:
            for film in pending_films:
                item_text = f"🎬 {film.title}\n   📅 {film.release_date} | 🎭 {film.genre}"
                if hasattr(film, 'description') and film.description:
                    # Limit description to 100 characters
                    desc = film.description[:100] + "..." if len(film.description) > 100 else film.description
                    item_text += f"\n   📝 {desc}"

                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, film)

                # Custom style for item
                item.setSizeHint(QSize(0, 80))  # Fixed height for each item
                self.pending_list.addItem(item)
        else:
            # Message when no pending films
            no_films_item = QListWidgetItem("No films pending approval")
            no_films_item.setFlags(Qt.NoItemFlags)  # Make non-selectable
            no_films_item.setTextAlignment(Qt.AlignCenter)
            no_films_item.setSizeHint(QSize(0, 60))
            self.pending_list.addItem(no_films_item)

        layout.addWidget(self.pending_list)

        # Container for buttons
        button_layout = QHBoxLayout()

        approve_btn = QPushButton("✅ Approve Film")
        approve_btn.clicked.connect(self.approve_selected)
        approve_btn.setIcon(QIcon.fromTheme("dialog-ok-apply"))

        close_btn = QPushButton("🚪 Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)

        button_layout.addWidget(approve_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        # Status at bottom
        status_label = QLabel(f"{len(pending_films)} film(s) pending approval")
        status_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 12px;
                padding: 5px;
                border-top: 1px solid #404040;
            }
        """)
        status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(status_label)

        self.setLayout(layout)

    def approve_selected(self):
        current_item = self.pending_list.currentItem()
        if current_item and current_item.data(Qt.UserRole):
            film = current_item.data(Qt.UserRole)
            try:
                self.film_controller.approve_film(film.id)
                self.film_approved.emit()

                # Remove item from list
                self.pending_list.takeItem(self.pending_list.row(current_item))

                # Success message
                QMessageBox.information(self, "Success", f"Film '{film.title}' approved successfully!")

                # Update status
                if self.pending_list.count() == 0:
                    no_films_item = QListWidgetItem("No films pending approval")
                    no_films_item.setFlags(Qt.NoItemFlags)
                    no_films_item.setTextAlignment(Qt.AlignCenter)
                    no_films_item.setSizeHint(QSize(0, 60))
                    self.pending_list.addItem(no_films_item)

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Approval error: {str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "Please select a film to approve.")

class ManageFilmsDialog(QDialog):
    film_updated = pyqtSignal()
    film_deleted = pyqtSignal()

    def __init__(self, film_controller, user, parent=None):
        super().__init__(parent)
        self.film_controller = film_controller
        self.by_user = user
        self.setWindowTitle("Film Management")
        self.setMinimumSize(900, 600)
        self.setStyleSheet(self.get_netflix_style())
        self.init_ui()

    def get_netflix_style(self):
        return """
        QDialog {
            background-color: #141414;
            color: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
        }

        QListWidget {
            background-color: #2d2d2d;
            border: 2px solid #404040;
            border-radius: 8px;
            padding: 10px;
            color: #ffffff;
            font-size: 14px;
            outline: none;
        }

        QListWidget::item {
            background-color: #404040;
            border-radius: 6px;
            padding: 15px;
            margin: 5px;
            border: 1px solid #555555;
        }

        QListWidget::item:hover {
            background-color: #525252;
            border: 1px solid #e50914;
        }

        QListWidget::item:selected {
            background-color: #e50914;
            border: 1px solid #e50914;
        }

        QPushButton {
            border: none;
            border-radius: 6px;
            padding: 12px 20px;
            font-size: 14px;
            font-weight: bold;
            min-width: 120px;
            margin: 5px;
        }

        QPushButton:hover {
            transform: scale(1.05);
        }

        QPushButton:pressed {
            transform: scale(0.95);
        }

        QLineEdit, QTextEdit, QComboBox, QDateEdit {
            background-color: #2d2d2d;
            border: 2px solid #404040;
            border-radius: 6px;
            padding: 8px 12px;
            color: white;
            font-size: 14px;
            selection-background-color: #e50914;
        }

        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {
            border-color: #e50914;
        }

        QLabel {
            color: #ffffff;
            font-size: 14px;
            padding: 5px;
        }
        """

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title_label = QLabel("Film Management")
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
                padding: 10px 0px;
                border-bottom: 2px solid #e50914;
            }
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # List of all films
        self.films_list = QListWidget()
        self.films_list.setSelectionMode(QListWidget.SingleSelection)
        self.films_list.itemSelectionChanged.connect(self.on_film_selected)

        self.load_films()
        layout.addWidget(self.films_list)

        # Selected film details area
        self.details_group = QGroupBox("Film Details")
        self.details_group.setStyleSheet("""
            QGroupBox {
                color: #e50914;
                font-weight: bold;
                font-size: 16px;
                border: 2px solid #404040;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        details_layout = QFormLayout()
        details_layout.setLabelAlignment(Qt.AlignRight)

        self.title_input = QLineEdit()
        self.genre_combo = QComboBox()
        self.genre_combo.addItems(["Action", "Comedy", "Drama", "Science-Fiction", "Horror", "Romance", "Thriller", "Animation", "Documentary", "Adventure"])
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(100)
        self.poster_input = QLineEdit()
        self.trailer_input = QLineEdit()

        # Apply style to fields
        for widget in [self.title_input, self.genre_combo, self.date_input,
                      self.desc_input, self.poster_input, self.trailer_input]:
            widget.setStyleSheet("color: white;")

        details_layout.addRow('Title*:', self.title_input)
        details_layout.addRow('Genre*:', self.genre_combo)
        details_layout.addRow('Release Date*:', self.date_input)
        details_layout.addRow('Description:', self.desc_input)
        details_layout.addRow('Poster:', self.poster_input)
        details_layout.addRow('Trailer:', self.trailer_input)

        self.details_group.setLayout(details_layout)
        layout.addWidget(self.details_group)

        # Action buttons
        button_layout = QHBoxLayout()

        self.update_btn = QPushButton("💾 Update")
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #cccccc;
            }
        """)
        self.update_btn.clicked.connect(self.update_film)
        self.update_btn.setEnabled(False)

        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #cccccc;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_film)
        self.delete_btn.setEnabled(False)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        refresh_btn.clicked.connect(self.load_films)

        close_btn = QPushButton("🚪 Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        close_btn.clicked.connect(self.accept)

        button_layout.addWidget(self.update_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_films(self):
        self.films_list.clear()
        films = self.film_controller.get_all_films()

        if films:
            for film in films:
                status = "✅" if getattr(film, 'approved', True) else "⏳"
                item_text = f"{status} {film.title}\n   📅 {film.release_date} | 🎭 {film.genre}"
                if hasattr(film, 'description') and film.description:
                    desc = film.description[:80] + "..." if len(film.description) > 80 else film.description
                    item_text += f"\n   📝 {desc}"

                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, film)
                item.setSizeHint(QSize(0, 80))
                self.films_list.addItem(item)
        else:
            no_films_item = QListWidgetItem("No films in database")
            no_films_item.setFlags(Qt.NoItemFlags)
            no_films_item.setTextAlignment(Qt.AlignCenter)
            no_films_item.setSizeHint(QSize(0, 60))
            self.films_list.addItem(no_films_item)

    def on_film_selected(self):
        current_item = self.films_list.currentItem()
        if current_item and current_item.data(Qt.UserRole):
            film = current_item.data(Qt.UserRole)
            self.current_film = film

            # Fill fields with film data
            self.title_input.setText(film.title)

            idx = self.genre_combo.findText(film.genre)
            if idx >= 0:
                self.genre_combo.setCurrentIndex(idx)

            release_date = QDate(film.release_date.year, film.release_date.month, film.release_date.day)
            self.date_input.setDate(release_date)

            self.desc_input.setText(getattr(film, 'description', ''))
            self.poster_input.setText(getattr(film, 'poster_path', ''))
            self.trailer_input.setText(getattr(film, 'trailer_url', ''))

            # Enable buttons
            self.update_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
        else:
            self.current_film = None
            self.update_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)

    def update_film(self):
        if not self.current_film:
            return

        # Validate required fields
        if not self.title_input.text().strip():
            QMessageBox.warning(self, "Error", "Title is required")
            return

        try:
            # Prepare update data
            updated_data = {
                'title': self.title_input.text().strip(),
                'genre': self.genre_combo.currentText(),
                'release_date': self.date_input.date().toPyDate(),
                'description': self.desc_input.toPlainText().strip(),
                'poster_path': self.poster_input.text().strip(),
                'trailer_url': self.trailer_input.text().strip()
            }

            # Update film
            self.film_controller.update_film(self.current_film.id, updated_data, self.by_user)

            QMessageBox.information(self, "Success", "Film updated successfully!")
            self.film_updated.emit()
            self.load_films()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Update error: {str(e)}")

    def delete_film(self):
        if not self.current_film:
            return

        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Are you sure you want to delete the film '{self.current_film.title}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.film_controller.delete_film(self.current_film.id, self.by_user)
                QMessageBox.information(self, "Success", "Film deleted successfully!")
                self.film_deleted.emit()
                self.load_films()
                self.current_film = None

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Deletion error: {str(e)}")

class MainWindow(QMainWindow):
    """Main window with Netflix-like interface"""

    logout_signal = pyqtSignal()

    def __init__(self, user):
        super().__init__()
        self.user = user
        self.film_controller = FilmController()
        self.is_admin = isinstance(user, Admin)  # Check if user is admin

        self.setWindowTitle(f'Film Finder - {getattr(user, "username", "Guest")}')
        self.setMinimumSize(1200, 800)
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Netflix header with search
        self.header = NetflixSearchHeader(self.film_controller)
        self.header.search_requested.connect(self.on_search_requested)
        self.main_layout.addWidget(self.header)

        # Approval button for admins
        if self.is_admin:
            self.admin_panel_btn = QPushButton("📋 Approval Management")
            self.admin_panel_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e50914;
                    border: none;
                    border-radius: 4px;
                    padding: 10px 15px;
                    color: white;
                    font-weight: bold;
                    margin: 10px 40px;
                    max-width: 200px;
                }
                QPushButton:hover {
                    background-color: #f40612;
                }
            """)
            self.admin_panel_btn.clicked.connect(self.show_admin_approval_panel)
            self.main_layout.addWidget(self.admin_panel_btn)

            # New Edit/Delete button
            self.manage_films_btn = QPushButton("Manage Films")
            self.manage_films_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2d2d2d;
                    border: 2px solid #404040;
                    border-radius: 4px;
                    padding: 10px 15px;
                    color: white;
                    font-weight: bold;
                    margin: 10px 5px;
                }
                QPushButton:hover {
                    background-color: #404040;
                    border-color: #e50914;
                    transform: scale(1.02);
                }
            """)
            self.manage_films_btn.clicked.connect(self.show_manage_films_dialog)
            self.main_layout.addWidget(self.manage_films_btn)

        # Main Netflix view
        self.netflix_view = NetflixGridView(self.film_controller, self.on_film_clicked)
        self.main_layout.addWidget(self.netflix_view)

        # Footer with logout
        footer = QWidget()
        footer.setFixedHeight(50)
        footer.setStyleSheet("background-color: #141414; border-top: 1px solid #2a2a2a;")
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(20, 5, 20, 5)

        user_info = QLabel(f'Logged in as: {getattr(self.user, "username", "Guest")}')
        user_info.setStyleSheet("color: #888888;")
        footer_layout.addWidget(user_info)

        footer_layout.addStretch()

        # Button to suggest a film (for all users)
        propose_btn = QPushButton('🎬 Suggest a Film')
        propose_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #e50914;
                border-radius: 4px;
                padding: 6px 12px;
                color: #e50914;
                margin-right: 10px;
            }
            QPushButton:hover {
                background-color: #e50914;
                color: white;
            }
        """)
        propose_btn.clicked.connect(self.propose_film)
        footer_layout.addWidget(propose_btn)

        logout_btn = QPushButton('Logout')
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

        # Load style
        self.load_styles()

    def load_styles(self):
        """Load Netflix QSS style"""
        try:
            qss_path = os.path.join(os.path.dirname(__file__), 'style.qss')
            if os.path.exists(qss_path):
                with open(qss_path, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Style loading error: {e}")

    def on_search_requested(self, criteria):
        """Handle search requests"""
        try:
            # Adapt criteria for FilmController
            title = criteria.get('title')
            genre = criteria.get('genre')
            year = criteria.get('year')

            # Use existing search_films method
            films = self.film_controller.search_films(
                title=title,
                genre=genre,
                approved_only=True
            )

            # Filter by year if specified
            if year:
                films = [f for f in films if hasattr(f, 'release_date') and f.release_date.year == year]

            # Display results
            self.show_search_results(films, criteria)

        except Exception as e:
            print(f"Search error: {e}")
            self.show_error_message(f"Search error: {e}")

    def show_error_message(self, message):
        """Show styled error message"""
        error_msg = QMessageBox(self)
        error_msg.setWindowTitle("Error")
        error_msg.setText(message)
        error_msg.setStyleSheet("""
            QMessageBox {
                background-color: #141414;
                color: #ffffff;
            }
            QMessageBox QLabel {
                color: #ffffff;

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
        """Display search results"""
        # Hide normal Netflix view
        self.netflix_view.hide()

        # Remove old results view if exists
        if hasattr(self, 'search_results_view'):
            self.search_results_view.hide()
            self.main_layout.removeWidget(self.search_results_view)
            self.search_results_view.deleteLater()

        # Create new results view
        self.search_results_view = QWidget()
        search_results_layout = QVBoxLayout()
        search_results_layout.setContentsMargins(0, 0, 0, 0)
        search_results_layout.setSpacing(0)
        self.search_results_view.setLayout(search_results_layout)

        # Results title
        results_title = QLabel(f"Search Results ({len(films)} movies found)")
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

        # Back button
        back_btn = QPushButton("Back to Home")
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

        # Results grid
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
            no_results = QLabel("No movies match your search")
            no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_results.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 18px;
                    padding: 50px;
                }
            """)
            search_results_layout.addWidget(no_results)

        # Add results view to main layout
        self.main_layout.insertWidget(1, self.search_results_view)
        self.search_results_view.show()

    def show_main_view(self):
        """Return to main view"""
        if hasattr(self, 'search_results_view'):
            self.search_results_view.hide()
            self.main_layout.removeWidget(self.search_results_view)
            self.search_results_view.deleteLater()
            delattr(self, 'search_results_view')
        self.netflix_view.show()

    def on_film_clicked(self, film):
        """Handle film click"""
        FilmViewDialog(film, parent=self).exec()

    def on_logout_clicked(self):
        """Handle logout"""
        try:
            self.logout_signal.emit()
        except Exception:
            pass
        self.close()

    def propose_film(self):
        """Open dialog to suggest new film"""
        dialog = FilmEditDialog(self.film_controller, self.user, parent=self)
        dialog.exec()

    def show_admin_approval_panel(self):
        """Show approval panel for admins"""
        if not self.is_admin:
            return

        dialog = AdminApprovalDialog(self.film_controller, self.user, parent=self)
        dialog.film_approved.connect(self.on_film_approved)
        dialog.exec()

    def on_film_approved(self):
        """Refresh interface when film is approved"""
        # Reload data
        self.netflix_view.load_data()

    def show_manage_films_dialog(self):
        dialog = ManageFilmsDialog(self.film_controller, self.user)
        dialog.film_updated.connect(self.refresh_films)
        dialog.film_deleted.connect(self.refresh_films)
        dialog.exec_()

    def refresh_films(self):
        """Refresh film display after modification/deletion"""
        try:
            # If you have a film grid or list
            if hasattr(self, 'films_grid'):
                self.update_films_grid()

            # If you have a QListWidget or QTableView for films
            if hasattr(self, 'films_list_widget'):
                self.load_films_to_list()

            # If you have a home page with films
            if hasattr(self, 'display_films'):
                self.display_films()

            print("Films refreshed successfully")

        except Exception as e:
            print(f"Refresh error: {e}")

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
