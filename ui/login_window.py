import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox, QFrame, QCheckBox,
    QSizePolicy, QScrollArea, QStackedWidget, QSpacerItem, QComboBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon, QColor, QPalette

# Ensure parent folder in path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.authcontroller import AuthController


class FloatingLineEdit(QWidget):
    """Custom widget: label that animates up when the QLineEdit is focused or has text."""

    def __init__(self, placeholder: str = '', parent=None, echo_mode=QLineEdit.EchoMode.Normal):
        super().__init__(parent)
        self.edit = QLineEdit(self)
        self.edit.setPlaceholderText('')
        self.label = QLabel(placeholder, self)
        self.label.setObjectName('floatingLabel')
        self.label.setStyleSheet('QLabel { color: rgba(230,230,230,0.8); }')
        self.edit.setEchoMode(echo_mode)

        self.anim = QPropertyAnimation(self.label, b'geometry')
        self.anim.setDuration(200)
        self.anim.setEasingCurve(QEasingCurve.InOutCubic)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        layout.addWidget(self.edit)
        self.setLayout(layout)

        self.edit.textChanged.connect(self._on_text_changed)
        self.edit.focused = False
        self.edit.installEventFilter(self)

    def eventFilter(self, obj, ev):
        if obj is self.edit:
            if ev.type() == ev.FocusIn:
                self._raise_label()
            elif ev.type() == ev.FocusOut:
                if not self.edit.text():
                    self._lower_label()
        return super().eventFilter(obj, ev)

    def _raise_label(self):
        r = QRect(0, 0, self.width(), 18)
        self.anim.stop()
        self.anim.setStartValue(self.label.geometry())
        self.anim.setEndValue(r)
        self.anim.start()

    def _lower_label(self):
        r = QRect(0, 18, self.width(), 18)
        self.anim.stop()
        self.anim.setStartValue(self.label.geometry())
        self.anim.setEndValue(r)
        self.anim.start()

    def _on_text_changed(self, t: str):
        if t:
            self._raise_label()
        else:
            if not self.edit.hasFocus():
                self._lower_label()

    def text(self):
        return self.edit.text()

    def setText(self, s: str):
        self.edit.setText(s)

    def setEchoMode(self, mode):
        self.edit.setEchoMode(mode)


class LoadingSpinner(QLabel):
    """Simple spinner using a small animated gif if available, otherwise text."""

    def __init__(self, parent=None):
        super().__init__(parent)
        gif_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'spinner.gif')
        if os.path.exists(gif_path):
            movie = QPixmap(gif_path)
            self.setPixmap(movie)
        else:
            self.setText('...')


class LoginWindow(QMainWindow):
    login_success = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.auth = AuthController()
        self.setWindowTitle('Film Finder - Connexion')
        self.setMinimumSize(900, 600)
        self.init_ui()

    def init_ui(self):
        # Central stacked widget to allow login <-> signup transition
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 20, 40, 20)

        # Header
        header = QHBoxLayout()
        logo = QLabel('FILM FINDER')
        logo.setStyleSheet('color: #E50914; font-weight: 800; font-size: 20px;')
        header.addWidget(logo, alignment=Qt.AlignLeft)
        header.addStretch()
        help_btn = QPushButton('Aide')
        help_btn.setProperty('flat', True)
        header.addWidget(help_btn, alignment=Qt.AlignRight)
        main_layout.addLayout(header)

        # Content area
        content = QHBoxLayout()
        content.addStretch()

        card = QFrame()
        card.setObjectName('formFrame')
        card.setFixedWidth(520)
        card_layout = QVBoxLayout()
        card_layout.setSpacing(12)

        title = QLabel("S'identifier")
        title.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        title.setStyleSheet('color: white;')
        card_layout.addWidget(title)

        self.email_field = FloatingLineEdit('Email')
        self.password_field = FloatingLineEdit('Mot de passe')
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        card_layout.addWidget(self.email_field)
        card_layout.addWidget(self.password_field)

        options = QHBoxLayout()
        self.remember = QCheckBox('Se souvenir de moi')
        options.addWidget(self.remember)
        options.addStretch()
        forgot = QPushButton('Besoin d\'aide ?')
        forgot.setProperty('flat', True)
        options.addWidget(forgot)
        card_layout.addLayout(options)

        self.error_label = QLabel('')
        self.error_label.setObjectName('errorLabel')
        self.error_label.setVisible(False)
        card_layout.addWidget(self.error_label)

        self.login_button = QPushButton('Se connecter')
        self.login_button.clicked.connect(self.on_login_clicked)
        card_layout.addWidget(self.login_button)

        # Signup section
        signup_h = QHBoxLayout()
        signup_h.addWidget(QLabel("Première visite sur Film Finder ?"))
        premiere_visite_label.setStyleSheet('color: white;')  # Ajouter cette ligne
        signup_btn = QPushButton('Inscrivez-vous maintenant')
        signup_btn.setStyleSheet('color: white;')  # Ajouter cette ligne
        signup_btn.setProperty('flat', True)
        signup_h.addWidget(signup_btn)
        card_layout.addLayout(signup_h)

        # Footer links
        footer = QHBoxLayout()
        conditions_label = QLabel('Conditions d\'utilisation')
        conditions_label.setStyleSheet('color: white;')  # Ajouter cette ligne
        footer.addWidget(conditions_label)
        footer.addStretch()
        centre_aide_label = QLabel('Centre d\'aide')
        centre_aide_label.setStyleSheet('color: white;')  # Ajouter cette ligne
        footer.addWidget(centre_aide_label)
        langue_label = QLabel('Langue:')
        langue_label.setStyleSheet('color: white;')  # Ajouter cette ligne
        footer.addWidget(langue_label)
        card_layout.addLayout(footer)

        card.setLayout(card_layout)
        content.addWidget(card)
        content.addStretch()

        main_layout.addLayout(content)
        central.setLayout(main_layout)

        # Load style
        try:
            qss_path = os.path.join(os.path.dirname(__file__), 'style.qss')
            if os.path.exists(qss_path):
                with open(qss_path, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
        except Exception:
            pass

        # Keyboard support
        self.email_field.edit.returnPressed.connect(self.password_field.edit.setFocus)
        self.password_field.edit.returnPressed.connect(self.on_login_clicked)

    def show_error(self, message: str):
        self.error_label.setText(message)
        self.error_label.setVisible(True)

    def on_login_clicked(self):
        email = self.email_field.text().strip()
        pwd = self.password_field.text()
        # simple validation
        if not email or not pwd:
            self.show_error('Veuillez remplir tous les champs')
            return

        # show loading spinner briefly and attempt login
        self.login_button.setEnabled(False)
        QTimer.singleShot(300, lambda: self._attempt_login(email, pwd))

    def _attempt_login(self, email, pwd):
        user = self.auth.login_user(email, pwd)
        if user:
            self.login_success.emit(user)
        else:
            self.show_error('Email ou mot de passe incorrect')
        self.login_button.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    w = LoginWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
