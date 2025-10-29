import sys
import os
from datetime import date
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QMessageBox, QTabWidget, QTextEdit, QDialog, QDialogButtonBox,
    QSizePolicy, QFormLayout, QComboBox, QDateEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QPixmap

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.filmcontroller import FilmController
from core.admins import Admin


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
        self.genre_combo.addItems(["Action", "Comédie", "Drame", "Science-Fiction", "Horreur", "Romance", "Thriller", "Animation", "Documentaire", "Aventure"])
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
            # For now editing requires admin rights; do not allow general edit
            QMessageBox.information(self, 'Info', 'Modification via l\'interface admin')
            self.reject()
            return
        else:
            ok = self.film_controller.add_film(film_data, self.by_user)
            if ok:
                QMessageBox.information(self, 'Succès', 'Film proposé (en attente de validation)')
                self.accept()
            else:
                QMessageBox.critical(self, 'Erreur', 'Échec lors de la proposition du film')


class MainWindow(QMainWindow):
    """Main window with user and admin features"""

    def __init__(self, user):
        super().__init__()
        self.user = user
        self.film_controller = FilmController()
        self.setWindowTitle(f'Film Finder - {getattr(user, "username", "Invité")}')
        self.setMinimumSize(900, 640)
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.create_search_tab()
        self.create_my_films_tab()
        if isinstance(self.user, Admin):
            self.create_admin_tab()

        central.setLayout(layout)

        # load style
        try:
            qss = os.path.join(os.path.dirname(__file__), 'style.qss')
            if os.path.exists(qss):
                with open(qss, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
        except Exception:
            pass

    # --- Search tab ---
    def create_search_tab(self):
        tab = QWidget()
        v = QVBoxLayout()
        h = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Chercher par titre...')
        btn = QPushButton('🔎 Rechercher')
        btn.clicked.connect(self.search_films)
        h.addWidget(self.search_input)
        h.addWidget(btn)
        v.addLayout(h)

        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self.open_film_from_item)
        v.addWidget(self.results_list)

        tab.setLayout(v)
        self.tabs.addTab(tab, '🔍 Recherche')
        self.load_all_films()

    def load_all_films(self):
        self.results_list.clear()
        for f in self.film_controller.get_approved_films():
            item = QListWidgetItem(f'{f.id} - {f.title} ({f.release_date.year})')
            item.setData(Qt.UserRole, f)
            self.results_list.addItem(item)

    def search_films(self):
        q = self.search_input.text().strip()
        self.results_list.clear()
        for f in self.film_controller.search_films(title=q, approved_only=True):
            item = QListWidgetItem(f'{f.id} - {f.title} ({f.release_date.year})')
            item.setData(Qt.UserRole, f)
            self.results_list.addItem(item)

    def open_film_from_item(self, item: QListWidgetItem):
        film = item.data(Qt.UserRole)
        FilmViewDialog(film, parent=self).exec()

    # --- My films tab ---
    def create_my_films_tab(self):
        tab = QWidget()
        v = QVBoxLayout()

        h = QHBoxLayout()
        propose_btn = QPushButton('➕ Proposer un film')
        propose_btn.clicked.connect(self.propose_film)
        refresh_btn = QPushButton('🔄 Rafraîchir')
        refresh_btn.clicked.connect(self.refresh_my_films)
        h.addWidget(propose_btn)
        h.addWidget(refresh_btn)
        h.addStretch()
        v.addLayout(h)

        self.my_list = QListWidget()
        v.addWidget(self.my_list)

        btns = QHBoxLayout()
        view = QPushButton('🔍 Voir')
        withdraw = QPushButton('↩️ Retirer')
        view.clicked.connect(self.my_view)
        withdraw.clicked.connect(self.my_withdraw)
        btns.addWidget(view)
        btns.addWidget(withdraw)
        btns.addStretch()
        v.addLayout(btns)

        tab.setLayout(v)
        self.tabs.addTab(tab, '📝 Mes films')
        self.refresh_my_films()

    def refresh_my_films(self):
        self.my_list.clear()
        for f in self.film_controller.get_films_by_user(self.user.id):
            status = '✅' if f.approved else '⏳'
            item = QListWidgetItem(f'{f.id} - {f.title} {status}')
            item.setData(Qt.UserRole, f)
            self.my_list.addItem(item)

    def propose_film(self):
        dlg = FilmEditDialog(self.film_controller, self.user, parent=self)
        if dlg.exec() == QDialog.Accepted:
            self.refresh_my_films()
            self.load_all_films()

    def _selected_from_list(self, list_widget: QListWidget):
        items = list_widget.selectedItems()
        if not items:
            QMessageBox.information(self, 'Info', 'Veuillez sélectionner un film')
            return None
        return items[0].data(Qt.UserRole)

    def my_view(self):
        f = self._selected_from_list(self.my_list)
        if f:
            FilmViewDialog(f, parent=self).exec()

    def my_withdraw(self):
        f = self._selected_from_list(self.my_list)
        if not f:
            return
        if f.approved:
            QMessageBox.information(self, 'Info', 'Impossible de retirer un film déjà approuvé')
            return
        confirm = QMessageBox.question(self, 'Confirmer', f"Retirer la proposition '{f.title}' ?")
        if confirm != QMessageBox.StandardButton.Yes and confirm != QMessageBox.StandardButton.Ok:
            return
        ok = self.film_controller.withdraw_film(f.id, self.user)
        if ok:
            QMessageBox.information(self, 'Succès', 'Proposition retirée')
            self.refresh_my_films()

    # --- Admin tab ---
    def create_admin_tab(self):
        tab = QWidget()
        v = QVBoxLayout()
        h = QHBoxLayout()
        refresh = QPushButton('🔄 Rafraîchir')
        refresh.clicked.connect(self.refresh_admin_tab)
        h.addWidget(QLabel('Films en attente:'))
        h.addStretch()
        h.addWidget(refresh)
        v.addLayout(h)

        self.pending_list = QListWidget()
        v.addWidget(self.pending_list)

        btns = QHBoxLayout()
        view = QPushButton('🔍 Voir')
        approve = QPushButton('✅ Valider')
        delete = QPushButton('🗑️ Supprimer')
        view.clicked.connect(self.admin_view)
        approve.clicked.connect(self.admin_approve)
        delete.clicked.connect(self.admin_delete)
        btns.addWidget(view)
        btns.addWidget(approve)
        btns.addWidget(delete)
        btns.addStretch()
        v.addLayout(btns)

        tab.setLayout(v)
        self.tabs.addTab(tab, '⚙️ Administration')
        self.refresh_admin_tab()

    def refresh_admin_tab(self):
        self.pending_list.clear()
        for f in self.film_controller.get_pending_films():
            item = QListWidgetItem(f'{f.id} - {f.title} ({f.release_date.year})')
            item.setData(Qt.UserRole, f)
            self.pending_list.addItem(item)

    def _selected_pending(self):
        items = self.pending_list.selectedItems()
        if not items:
            QMessageBox.information(self, 'Info', 'Veuillez sélectionner un film')
            return None
        return items[0].data(Qt.UserRole)

    def admin_view(self):
        f = self._selected_pending()
        if f:
            FilmViewDialog(f, parent=self).exec()

    def admin_approve(self):
        f = self._selected_pending()
        if not f:
            return
        ok = self.film_controller.validate_film(f.id, self.user)
        if ok:
            QMessageBox.information(self, 'Succès', 'Film validé')
            self.refresh_admin_tab()
            self.load_all_films()

    def admin_delete(self):
        f = self._selected_pending()
        if not f:
            return
        ok = self.film_controller.delete_film(f.id, self.user)
        if ok:
            QMessageBox.information(self, 'Succès', 'Film supprimé')
            self.refresh_admin_tab()


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
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QMessageBox, QTabWidget, QTextEdit, QDialog, QDialogButtonBox,
    QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt, QDate, QUrl
from PyQt5.QtGui import QFont, QPixmap

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.filmcontroller import FilmController
from core.admins import Admin


class FilmDialog(QDialog):
    """Simple dialog to view a film's details (read-only) and optionally play trailer."""

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

        # Horizontal area: poster + description
        hl = QHBoxLayout()

        poster = QLabel()
        poster.setFixedSize(160, 240)
        poster.setScaledContents(True)
        try:
            if self.film.poster_path and os.path.exists(self.film.poster_path):
                pix = QPixmap(self.film.poster_path)
                poster.setPixmap(pix)
        except Exception:
            pass
        hl.addWidget(poster)

        desc = QTextEdit()
        desc.setReadOnly(True)
        desc.setText(self.film.description or "(Pas de description)")
        desc.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        hl.addWidget(desc)

        layout.addLayout(hl)

        # Buttons
        btns = QHBoxLayout()
        btns.addStretch()
        close = QPushButton("Fermer")
        close.clicked.connect(self.accept)
        btns.addWidget(close)
        layout.addLayout(btns)

        self.setLayout(layout)


class MainWindow(QMainWindow):
    """Main application window with simple search and admin tabs."""

    def __init__(self, user):
        super().__init__()
        self.user = user
        self.film_controller = FilmController()
        self.setWindowTitle(f"Film Finder - {getattr(user, 'username', 'Invité')}")
        self.setMinimumSize(800, 600)
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout()

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(False)
        main_layout.addWidget(self.tabs)

        self.create_search_tab()
        # Only add admin tab for Admins
        if isinstance(self.user, Admin):
            self.create_admin_tab()

        central.setLayout(main_layout)

        # Load QSS if available for nicer colors
        try:
            qss_path = os.path.join(os.path.dirname(__file__), 'style.qss')
            if os.path.exists(qss_path):
                with open(qss_path, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
        except Exception:
            pass

    def create_search_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Search bar
        hl = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Chercher un film par titre...')
        search_btn = QPushButton('🔎 Rechercher')
        search_btn.clicked.connect(self.search_films)
        hl.addWidget(self.search_input)
        hl.addWidget(search_btn)
        layout.addLayout(hl)

        # Results
        self.results_list = QListWidget()
        self.results_list.itemDoubleClicked.connect(self.open_selected_film)
        layout.addWidget(self.results_list)

        tab.setLayout(layout)
        self.tabs.addTab(tab, '🔍 Recherche')

        # initial load
        self.load_all_films()

    def load_all_films(self):
        try:
            films = self.film_controller.get_all_films()
            self.results_list.clear()
            for f in films:
                item = QListWidgetItem(f"{f.id} - {f.title} ({f.release_date.year})")
                item.setData(Qt.UserRole, f)
                self.results_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible de charger les films: {e}")

    def search_films(self):
        q = self.search_input.text().strip()
        try:
            results = self.film_controller.search_films({'title': q}) if q else self.film_controller.get_all_films()
            self.results_list.clear()
            for f in results:
                item = QListWidgetItem(f"{f.id} - {f.title} ({f.release_date.year})")
                item.setData(Qt.UserRole, f)
                self.results_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Recherche échouée: {e}")

    def open_selected_film(self, item: QListWidgetItem):
        film = item.data(Qt.UserRole)
        dlg = FilmDialog(film, parent=self)
        dlg.exec()

    def create_admin_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        hl = QHBoxLayout()
        refresh = QPushButton('🔄 Rafraîchir')
        refresh.clicked.connect(self.refresh_admin_tab)
        hl.addWidget(QLabel('Films en attente:'))
        hl.addStretch()
        hl.addWidget(refresh)
        layout.addLayout(hl)

        self.pending_list = QListWidget()
        layout.addWidget(self.pending_list)

        btns = QHBoxLayout()
        view = QPushButton('🔍 Voir')
        approve = QPushButton('✅ Valider')
        delete = QPushButton('🗑️ Supprimer')
        view.clicked.connect(self.admin_view)
        approve.clicked.connect(self.admin_approve)
        delete.clicked.connect(self.admin_delete)
        btns.addWidget(view)
        btns.addWidget(approve)
        btns.addWidget(delete)
        btns.addStretch()
        layout.addLayout(btns)

        tab.setLayout(layout)
        self.tabs.addTab(tab, '⚙️ Administration')
        self.refresh_admin_tab()

    def refresh_admin_tab(self):
        try:
            pending = self.film_controller.get_pending_films()
            self.pending_list.clear()
            for f in pending:
                item = QListWidgetItem(f"{f.id} - {f.title} ({f.release_date.year})")
                item.setData(Qt.UserRole, f)
                self.pending_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Impossible de charger en attente: {e}")

    def _selected_pending(self):
        items = self.pending_list.selectedItems()
        if not items:
            QMessageBox.information(self, 'Info', 'Sélectionnez un film')
            return None
        return items[0].data(Qt.UserRole)

    def admin_view(self):
        f = self._selected_pending()
        if f:
            FilmDialog(f, parent=self).exec()

    def admin_approve(self):
        f = self._selected_pending()
        if not f:
            return
        try:
            ok = self.film_controller.validate_film(f.id, self.user)
            if ok:
                QMessageBox.information(self, 'Succès', 'Film validé')
                self.refresh_admin_tab()
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Échec validation: {e}")

    def admin_delete(self):
        f = self._selected_pending()
        if not f:
            return
        try:
            ok = self.film_controller.delete_film(f.id, self.user)
            if ok:
                QMessageBox.information(self, 'Succès', 'Film supprimé')
                self.refresh_admin_tab()
        except Exception as e:
            QMessageBox.critical(self, 'Erreur', f"Échec suppression: {e}")


def main():
    app = QApplication(sys.argv)
    # Prefer opening the login window so we don't auto-create data on import
    try:
        from ui.login_window import LoginWindow

        login = LoginWindow()

        def _on_login(user):
            mw = MainWindow(user)
            mw.show()
            # hide login window to avoid confusion
            login.hide()

        login.login_success.connect(_on_login)
        login.show()
    except Exception:
        # If something fails, open a simple main window for development
        from core.users import User
        user = User.create_user(0, 'Dev', 'User', 'dev@local', 'dev', 'DevPass1!')
        window = MainWindow(user)
        window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QListWidget, QListWidgetItem, QMessageBox,
                             QTabWidget, QFrame, QComboBox, QDateEdit,
                             QTextEdit, QDialog, QDialogButtonBox, QSizePolicy, QScrollArea)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QUrl
from PyQt5.QtGui import QFont, QPixmap, QIcon
try:
    # Modules multimedia optionnels — peuvent ne pas être disponibles sur toutes les plateformes
    from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
    from PyQt5.QtMultimediaWidgets import QVideoWidget
    MULTIMEDIA_AVAILABLE = True
except Exception:
    MULTIMEDIA_AVAILABLE = False

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.filmcontroller import FilmController
from core.films import Film
from core.admins import Admin
from datetime import date

class FilmDialog(QDialog):
    """Dialogue pour ajouter/modifier un film"""
    def __init__(self, film_controller, user, film=None, parent=None):
        super().__init__(parent)
        self.film_controller = film_controller
        self.user = user
        self.film = film
        self.is_edit = film is not None

        self.init_ui()

    def init_ui(self):
        """Initialise l'interface du dialogue"""
        self.setWindowTitle("Modifier le film" if self.is_edit else "Proposer un film")
        # Dialog resizable for responsiveness
        self.setMinimumSize(480, 520)
        self.resize(520, 640)

        # Layout principal du dialogue
        layout = QVBoxLayout()

        # Titre
        title_label = QLabel("Modifier le film" if self.is_edit else "Nouveau film")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))

        # Formulaire
        form_layout = QVBoxLayout()

        # Titre du film
        form_layout.addWidget(QLabel("Titre*:"))
        self.title_input = QLineEdit()
        if self.is_edit:
            self.title_input.setText(self.film.title)
        form_layout.addWidget(self.title_input)

        # Genre
        form_layout.addWidget(QLabel("Genre*:"))
        self.genre_combo = QComboBox()
        genres = ["Action", "Comédie", "Drame", "Science-Fiction", "Horreur",
                 "Romance", "Thriller", "Animation", "Documentaire", "Aventure"]
        self.genre_combo.addItems(genres)
        if self.is_edit:
            index = self.genre_combo.findText(self.film.genre)
            if index >= 0:
                self.genre_combo.setCurrentIndex(index)
        form_layout.addWidget(self.genre_combo)

        # Date de sortie
        form_layout.addWidget(QLabel("Date de sortie*:"))
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        if self.is_edit:
            qdate = QDate(self.film.release_date.year,
                         self.film.release_date.month,
                         self.film.release_date.day)
            self.date_input.setDate(qdate)
        form_layout.addWidget(self.date_input)

        # Description
        form_layout.addWidget(QLabel("Description:"))
        self.description_input = QTextEdit()
        # Let description expand vertically when dialog resized
        self.description_input.setMinimumHeight(80)
        self.description_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        if self.is_edit:
            self.description_input.setText(self.film.description)
        form_layout.addWidget(self.description_input)

        # Poster URL
        form_layout.addWidget(QLabel("URL du poster:"))
        self.poster_input = QLineEdit()
        if self.is_edit:
            self.poster_input.setText(self.film.poster_path)
        self.poster_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        form_layout.addWidget(self.poster_input)

        # Trailer URL
        form_layout.addWidget(QLabel("URL de la bande-annonce:"))
        self.trailer_input = QLineEdit()
        if self.is_edit:
            self.trailer_input.setText(self.film.trailer_url)
        self.trailer_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        form_layout.addWidget(self.trailer_input)

        # Boutons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        # Assemblage
        layout.addWidget(title_label)
        layout.addLayout(form_layout)
        layout.addWidget(button_box)

        # Wrap content in a scroll area for small screens
        container = QWidget()
        container.setLayout(layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        outer = QVBoxLayout()
        outer.addWidget(scroll)
        self.setLayout(outer)
        container = QWidget()
        container.setLayout(layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        outer = QVBoxLayout()
        outer.addWidget(scroll)
        self.setLayout(outer)

    def accept(self):
        """Valide et sauvegarde le film"""
        title = self.title_input.text().strip()
        genre = self.genre_combo.currentText()
        release_date = self.date_input.date().toPyDate()
        description = self.description_input.toPlainText().strip()
        poster_path = self.poster_input.text().strip()
        trailer_url = self.trailer_input.text().strip()

        if not title or not genre:
            QMessageBox.warning(self, "Erreur", "Les champs titre et genre sont obligatoires")
            return

        film_data = {
            'title': title,
            'genre': genre,
            'release_date': release_date,
            'description': description,
            'poster_path': poster_path,
            'trailer_url': trailer_url
        }

        if self.is_edit:
            # Modification
            success = self.film_controller.update_film(
                self.film.id, film_data, self.user
            )
            if success:
                QMessageBox.information(self, "Succès", "Film modifié avec succès!")
                super().accept()
            else:
                QMessageBox.critical(self, "Erreur", "Erreur lors de la modification du film")
        else:
            # Nouveau film
            class FilmDialog(QDialog):
                """Dialogue pour ajouter/modifier un film"""

                def __init__(self, film_controller, user, film=None, parent=None):
                    super().__init__(parent)
                    self.film_controller = film_controller
                    self.user = user
                    self.film = film
                    self.is_edit = film is not None

                    self.init_ui()

                def init_ui(self):
                    """Initialise l'interface du dialogue"""
                    self.setWindowTitle("Modifier le film" if self.is_edit else "Proposer un film")
                    # Dialog resizable for responsiveness
                    self.setMinimumSize(480, 520)
                    self.resize(520, 640)

                    # Layout principal du dialogue
                    layout = QVBoxLayout()

                    # Titre
                    title_label = QLabel("Modifier le film" if self.is_edit else "Nouveau film")
                    title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))

                    # Formulaire
                    form_layout = QVBoxLayout()

                    # Titre du film
                    form_layout.addWidget(QLabel("Titre*:"))
                    self.title_input = QLineEdit()
                    if self.is_edit:
                        self.title_input.setText(self.film.title)
                    form_layout.addWidget(self.title_input)

                    # Genre
                    form_layout.addWidget(QLabel("Genre*:"))
                    self.genre_combo = QComboBox()
                    genres = ["Action", "Comédie", "Drame", "Science-Fiction", "Horreur",
                             "Romance", "Thriller", "Animation", "Documentaire", "Aventure"]
                    self.genre_combo.addItems(genres)
                    if self.is_edit:
                        index = self.genre_combo.findText(self.film.genre)
                        if index >= 0:
                            self.genre_combo.setCurrentIndex(index)
                    form_layout.addWidget(self.genre_combo)

                    # Date de sortie
                    form_layout.addWidget(QLabel("Date de sortie*:"))
                    self.date_input = QDateEdit()
                    self.date_input.setCalendarPopup(True)
                    self.date_input.setDate(QDate.currentDate())
                    if self.is_edit:
                        qdate = QDate(self.film.release_date.year,
                                     self.film.release_date.month,
                                     self.film.release_date.day)
                        self.date_input.setDate(qdate)
                    form_layout.addWidget(self.date_input)

                    # Description
                    form_layout.addWidget(QLabel("Description:"))
                    self.description_input = QTextEdit()
                    # Let description expand vertically when dialog resized
                    self.description_input.setMinimumHeight(80)
                    self.description_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                    if self.is_edit:
                        self.description_input.setText(self.film.description)
                    form_layout.addWidget(self.description_input)

                    # Poster URL
                    form_layout.addWidget(QLabel("URL du poster:"))
                    self.poster_input = QLineEdit()
                    if self.is_edit:
                        self.poster_input.setText(self.film.poster_path)
                    self.poster_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                    form_layout.addWidget(self.poster_input)

                    # Trailer URL
                    form_layout.addWidget(QLabel("URL de la bande-annonce:"))
                    self.trailer_input = QLineEdit()
                    if self.is_edit:
                        self.trailer_input.setText(self.film.trailer_url)
                    self.trailer_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                    form_layout.addWidget(self.trailer_input)

                    # Boutons
                    button_box = QDialogButtonBox(
                        QDialogButtonBox.StandardButton.Ok |
                        QDialogButtonBox.StandardButton.Cancel
                    )
                    button_box.accepted.connect(self.accept)
                    button_box.rejected.connect(self.reject)

                    # Assemblage
                    layout.addWidget(title_label)
                    layout.addLayout(form_layout)
                    layout.addWidget(button_box)

                    # Wrap content in a scroll area for small screens
                    container = QWidget()
                    container.setLayout(layout)
                    scroll = QScrollArea()
                    scroll.setWidgetResizable(True)
                    scroll.setWidget(container)
                    outer = QVBoxLayout()
                    outer.addWidget(scroll)
                    self.setLayout(outer)

                def accept(self):
                    """Valide et sauvegarde le film"""
                    title = self.title_input.text().strip()
                    genre = self.genre_combo.currentText()
                    release_date = self.date_input.date().toPyDate()
                    description = self.description_input.toPlainText().strip()
                    poster_path = self.poster_input.text().strip()
                    trailer_url = self.trailer_input.text().strip()

                    if not title or not genre:
                        QMessageBox.warning(self, "Erreur", "Les champs titre et genre sont obligatoires")
                        return

                    film_data = {
                        'title': title,
                        'genre': genre,
                        'release_date': release_date,
                        'description': description,
                        'poster_path': poster_path,
                        'trailer_url': trailer_url
                    }

                    if self.is_edit:
                        # Modification
                        success = self.film_controller.update_film(
                            self.film.id, film_data, self.user
                        )
                        if success:
                            QMessageBox.information(self, "Succès", "Film modifié avec succès!")
                            super().accept()
                        else:
                            QMessageBox.critical(self, "Erreur", "Erreur lors de la modification du film")
                    else:
                        # Nouveau film
                        success = self.film_controller.add_film(film_data, self.user)
                        if success:
                            QMessageBox.information(self, "Succès", "Film proposé avec succès! En attente de validation.")
                            super().accept()
                        else:
                            QMessageBox.critical(self, "Erreur", "Erreur lors de l'ajout du film")

        # Boutons action: jouer bande-annonce si dispo
        hl = QHBoxLayout()
        hl.addStretch()
        if film.trailer_url:
            play_btn = QPushButton("▶️ Lire la bande-annonce")
            def _play_trailer():
                # Si les modules multimedia sont disponibles, ouvrir un lecteur simple
                if MULTIMEDIA_AVAILABLE:
                    trailer_dialog = QDialog(self)
                    trailer_dialog.setWindowTitle(f"Bande-annonce - {film.title}")
                    trailer_dialog.setMinimumSize(640, 480)

                    v = QVBoxLayout()
                    video_widget = QVideoWidget()
                    v.addWidget(video_widget)

                    player = QMediaPlayer()
                    player.setVideoOutput(video_widget)
                    try:
                        url = QUrl.fromUserInput(film.trailer_url)
                        player.setMedia(QMediaContent(url))
                    except Exception as e:
                        QMessageBox.critical(self, "Erreur", f"Impossible de charger la bande-annonce: {e}")
                        return

                    # Contrôles simples
                    ctrl_layout = QHBoxLayout()
                    pause_btn = QPushButton("Pause")
                    stop_btn = QPushButton("Stop")
                    ctrl_layout.addWidget(pause_btn)
                    ctrl_layout.addWidget(stop_btn)
                    v.addLayout(ctrl_layout)

                    pause_btn.clicked.connect(lambda: player.pause())
                    stop_btn.clicked.connect(lambda: player.stop())

                    trailer_dialog.setLayout(v)
                    player.play()
                    trailer_dialog.exec()
                else:
                    # Ouvrir avec le navigateur/lecteur externe si multimedia indisponible
                    try:
                        from PyQt5.QtGui import QDesktopServices
                        QDesktopServices.openUrl(QUrl(film.trailer_url))
                    except Exception:
                        QMessageBox.information(self, "Info", "Impossible de lancer la bande-annonce depuis l'application."
                                                    " Ouvrez le lien manuellement.")

            play_btn.clicked.connect(_play_trailer)
            hl.addWidget(play_btn)

        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(dialog.accept)
        hl.addWidget(close_btn)
        hl.addStretch()

        vlayout.addLayout(hl)

        dialog.setLayout(vlayout)
        dialog.exec()

    def create_my_films_tab(self):
        """Crée l'onglet 'Mes films'"""
        tab = QWidget()
        layout = QVBoxLayout()

        # À implémenter
        layout.addWidget(QLabel("Mes films proposés (à implémenter)"))

        tab.setLayout(layout)
        self.tabs.addTab(tab, "📝 Mes films")

    def create_admin_tab(self):
        """Crée l'onglet administrateur"""
        tab = QWidget()
        layout = QVBoxLayout()

        # Liste des films en attente
        hl_top = QHBoxLayout()
        hl_top.addWidget(QLabel("Films en attente:"))
        refresh_btn = QPushButton("🔄 Rafraîchir")
        refresh_btn.clicked.connect(self.refresh_admin_tab)
        hl_top.addWidget(refresh_btn)
        hl_top.addStretch()

        self.admin_pending_list = QListWidget()
        self.admin_pending_list.itemSelectionChanged.connect(lambda: None)

        # Boutons d'action
        hl = QHBoxLayout()
        approve_btn = QPushButton("✅ Valider")
        approve_btn.clicked.connect(self.approve_selected_film)
        delete_btn = QPushButton("🗑️ Supprimer")
        delete_btn.clicked.connect(self.delete_selected_film)
        view_btn = QPushButton("🔍 Voir détails")
        view_btn.clicked.connect(self.view_pending_film_details)

        hl.addWidget(view_btn)
        hl.addWidget(approve_btn)
        hl.addWidget(delete_btn)
        hl.addStretch()

        # Logs récents pour le film sélectionné
        self.admin_logs_label = QLabel("Sélectionnez un film pour voir les logs")
        self.admin_logs_label.setWordWrap(True)

        layout.addLayout(hl_top)
        layout.addWidget(self.admin_pending_list)
        layout.addLayout(hl)
        layout.addWidget(self.admin_logs_label)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "⚙️ Administration")

        # Chargement initial
        self.refresh_admin_tab()

    def refresh_admin_tab(self):
        """Recharge la liste des films en attente"""
        try:
            pending = self.film_controller.get_pending_films()
            self.admin_pending_list.clear()
            for film in pending:
                item = QListWidgetItem(f"{film.id} - {film.title} ({film.release_date.year}) - {film.genre}")
                item.setData(Qt.ItemDataRole.UserRole, film)
                self.admin_pending_list.addItem(item)

            self.admin_logs_label.setText(f"{len(pending)} film(s) en attente")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger les films en attente: {e}")

    def _get_selected_pending_film(self):
        items = self.admin_pending_list.selectedItems()
        if not items:
            QMessageBox.information(self, "Info", "Veuillez sélectionner un film")
            return None
        return items[0].data(Qt.ItemDataRole.UserRole)

    def approve_selected_film(self):
        """Valide le film sélectionné via FilmController"""
        # Autorisation: seul un Admin peut valider
        if not isinstance(self.user, Admin):
            QMessageBox.critical(self, "Accès refusé", "Vous n'avez pas les droits pour valider des films.")
            return
        film = self._get_selected_pending_film()
        if not film:
            return
        # Confirmer
        ret = QMessageBox.question(self, "Confirmer", f"Valider le film '{film.title}' ?")
        if ret != QMessageBox.StandardButton.Yes and ret != QMessageBox.StandardButton.Ok:
            return

        # Trouver un admin user correct — self.user devrait être un Admin
        try:
            success = self.film_controller.validate_film(film.id, self.user)
            if success:
                QMessageBox.information(self, "Succès", "Film validé avec succès")
                self.refresh_admin_tab()
            else:
                QMessageBox.critical(self, "Erreur", "Erreur lors de la validation du film")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la validation: {e}")

    def delete_selected_film(self):
        """Supprime le film sélectionné via FilmController"""
        # Autorisation: seul un Admin peut supprimer
        if not isinstance(self.user, Admin):
            QMessageBox.critical(self, "Accès refusé", "Vous n'avez pas les droits pour supprimer des films.")
            return
        film = self._get_selected_pending_film()
        if not film:
            return
        ret = QMessageBox.question(self, "Confirmer", f"Supprimer le film '{film.title}' ? Cette action est irréversible.")
        if ret != QMessageBox.StandardButton.Yes and ret != QMessageBox.StandardButton.Ok:
            return

        try:
            success = self.film_controller.delete_film(film.id, self.user)
            if success:
                QMessageBox.information(self, "Succès", "Film supprimé")
                self.refresh_admin_tab()
            else:
                QMessageBox.critical(self, "Erreur", "Erreur lors de la suppression du film")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la suppression: {e}")

    def view_pending_film_details(self):
        """Affiche les détails (dialog) du film sélectionné"""
        film = self._get_selected_pending_film()
        if not film:
            return

        # Réutiliser FilmDialog en mode édition pour visualiser/éditer
        dialog = FilmDialog(self.film_controller, self.user, film, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Après modification, rafraîchir
            self.refresh_admin_tab()

def main():
    app = QApplication(sys.argv)
    # Pour lancer l'interface depuis ce module, ouvrir d'abord la fenêtre de connexion
    # afin de ne pas créer d'utilisateurs ou modifier les JSON par inadvertance.
    try:
        from ui.login_window import LoginWindow
        login = LoginWindow()
        # Lors d'une connexion réussie, ouvrir la fenêtre principale
        def _on_login(user):
            mw = MainWindow(user)
            mw.show()
        login.login_success.connect(_on_login)
        login.show()
    except Exception:
        # Fallback : si LoginWindow ne peut pas être importé, afficher une instance
        # vide pour développement local sans modifier les fichiers de données.
        from core.users import User
        user = User.create_user(0, "Dev", "User", "dev@local", "dev", "DevPass1!")
        window = MainWindow(user)
        window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
