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
        self.setWindowTitle('Film Finder - Login')
        self.setMinimumSize(900, 600)
        self.stacked_widget = QStackedWidget()
        # Create login and signup forms
        self.signup_form = self.create_signup_form()

        # Add forms to stacked widget
        #self.stacked_widget.addWidget(self.login_form)
        self.stacked_widget.addWidget(self.signup_form)
        #self.stacked_widget.setCurrentWidget(self.login_form)
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
        help_btn = QPushButton('Help')
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

        title = QLabel("Sign In")
        title.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        title.setStyleSheet('color: white;')
        card_layout.addWidget(title)

        self.email_field = FloatingLineEdit('Email')
        self.password_field = FloatingLineEdit('Password')
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        card_layout.addWidget(self.email_field)
        card_layout.addWidget(self.password_field)

        options = QHBoxLayout()
        self.remember = QCheckBox('Remember me')
        options.addWidget(self.remember)
        options.addStretch()
        forgot = QPushButton('Need help?')
        forgot.setProperty('flat', True)
        options.addWidget(forgot)
        card_layout.addLayout(options)

        self.error_label = QLabel('')
        self.error_label.setObjectName('errorLabel')
        self.error_label.setVisible(False)
        card_layout.addWidget(self.error_label)

        self.login_button = QPushButton('Sign In')
        self.login_button.clicked.connect(self.on_login_clicked)
        card_layout.addWidget(self.login_button)

        # Signup section
        signup_h = QHBoxLayout()
        firstvisit = QLabel("First time on Film Finder?")
        firstvisit.setStyleSheet('color: white;')  # Add this line
        signup_btn = QPushButton('Sign up now')
        signup_btn.setStyleSheet('''
            QPushButton {
                color: white;
                background: transparent;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #E50914;
            }
        ''')  # Add this line
        signup_btn.setProperty('flat', True)
        signup_btn.clicked.connect(self.show_signup_form)
        signup_h.addWidget(firstvisit)
        signup_h.addWidget(signup_btn)
        card_layout.addLayout(signup_h)

        # Footer links
        footer = QHBoxLayout()
        conditions_label = QLabel('Terms of Use')
        conditions_label.setStyleSheet('color: white;')  # Add this line
        footer.addWidget(conditions_label)
        footer.addStretch()
        centre_aide_label = QLabel('Help Center')
        centre_aide_label.setStyleSheet('color: white;')  # Add this line
        footer.addWidget(centre_aide_label)
        langue_label = QLabel('Language:')
        langue_label.setStyleSheet('color: white;')  # Add this line
        footer.addWidget(langue_label)
        card_layout.addLayout(footer)

        card.setLayout(card_layout)
        content.addWidget(card)
        content.addStretch()

        main_layout.addLayout(content)

        # ⚡ NEW PART — transform this layout into login page
        login_page = QWidget()
        login_page.setLayout(main_layout)

        # Add login + signup pages to stacked widget
        self.stacked_widget.addWidget(login_page)
        self.stacked_widget.setCurrentWidget(login_page)
        self.stacked_widget.addWidget(self.signup_form)

        # Put stacked widget in main window
        central_layout = QVBoxLayout()
        central_layout.addWidget(self.stacked_widget)
        central.setLayout(central_layout)
        self.setCentralWidget(central)

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


    def create_signup_form(self):
        # Main widget for the form
        signup_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 20, 40, 20)
        main_layout.setSpacing(15)

        # Header
        header = QHBoxLayout()
        logo = QLabel('FILM FINDER')
        logo.setStyleSheet('color: #E50914; font-weight: 800; font-size: 20px;')
        header.addWidget(logo, alignment=Qt.AlignLeft)
        header.addStretch()
        help_btn = QPushButton('Help')
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

        title = QLabel("Create Account")
        title.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        title.setStyleSheet('color: white;')
        card_layout.addWidget(title)

        # Signup fields
        self.signup_first_name_field = FloatingLineEdit('First Name')
        self.signup_last_name_field = FloatingLineEdit('Last Name')
        self.signup_email_field = FloatingLineEdit('Email')
        self.signup_username_field = FloatingLineEdit('Username')
        self.signup_password_field = FloatingLineEdit('Password')
        self.signup_password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.signup_confirm_field = FloatingLineEdit('Confirm Password')
        self.signup_confirm_field.setEchoMode(QLineEdit.EchoMode.Password)

        for field in [
            self.signup_first_name_field,
            self.signup_last_name_field,
            self.signup_email_field,
            self.signup_username_field,
            self.signup_password_field,
            self.signup_confirm_field
        ]:
            card_layout.addWidget(field)

        # Admin checkbox
        self.signup_admin_checkbox = QCheckBox("Administrator?")
        self.signup_admin_checkbox.setStyleSheet('color: white;')
        card_layout.addWidget(self.signup_admin_checkbox)

        # Error label
        self.signup_error_label = QLabel('')
        self.signup_error_label.setObjectName('errorLabel')
        self.signup_error_label.setVisible(False)
        card_layout.addWidget(self.signup_error_label)

        # Create account button
        self.signup_button = QPushButton('Create Account')
        self.signup_button.clicked.connect(self.on_signup_clicked)
        card_layout.addWidget(self.signup_button)

        # Back to login link
        login_h = QHBoxLayout()
        deja_compte_label = QLabel("Already have an account?")
        deja_compte_label.setStyleSheet('color: white;')
        login_h.addWidget(deja_compte_label)
        login_btn = QPushButton('Sign In')
        login_btn.setStyleSheet('''
            QPushButton {
                color: white;
                background: transparent;
                border: none;
                text-decoration: underline;
            }
            QPushButton:hover {
                color: #E50914;
            }
        ''')
        login_btn.setProperty('flat', True)
        login_btn.clicked.connect(self.show_login_form)
        login_h.addWidget(login_btn)
        card_layout.addLayout(login_h)

        card.setLayout(card_layout)
        content.addWidget(card)
        content.addStretch()
        main_layout.addLayout(content)
        signup_widget.setLayout(main_layout)

        # ⚡ Add scroll for small windows
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(signup_widget)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("border: none;")

        return scroll_area

    def show_signup_form(self):
        self.stacked_widget.setCurrentWidget(self.signup_form)  # Index 1 = signup

    def show_login_form(self):
        self.stacked_widget.setCurrentIndex(0)  # Index 0 = login

    def on_signup_clicked(self):
        first_name = self.signup_first_name_field.text().strip()
        last_name = self.signup_last_name_field.text().strip()
        email = self.signup_email_field.text().strip()
        username = self.signup_username_field.text().strip()
        password = self.signup_password_field.text()
        confirm = self.signup_confirm_field.text()
        is_admin = self.signup_admin_checkbox.isChecked()

        # Simple validation
        if not all([first_name, last_name, email, username, password, confirm]):
            self.signup_error_label.setText('Please fill in all fields')
            self.signup_error_label.setVisible(True)
            return

        if password != confirm:
            self.signup_error_label.setText('Passwords do not match')
            self.signup_error_label.setVisible(True)
            return

        # Here call user creation function, for example:
        self.auth.register_user(first_name, last_name, email, username, password, is_admin)
        self.signup_error_label.setText('Registration successful! You can now sign in.')
        self.signup_error_label.setVisible(True)

        # Return to login form after registration
        QTimer.singleShot(1500, self.show_login_form)

    def on_login_clicked(self):
        email = self.email_field.text().strip()
        pwd = self.password_field.text()
        # simple validation
        if not email or not pwd:
            self.show_error('Please fill in all fields')
            return

        # show loading spinner briefly and attempt login
        self.login_button.setEnabled(False)
        QTimer.singleShot(300, lambda: self._attempt_login(email, pwd))

    def _attempt_login(self, email, pwd):
        user = self.auth.login_user(email, pwd)
        if user:
            self.login_success.emit(user)
        else:
            self.show_error('Incorrect email or password')
        self.login_button.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    w = LoginWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
