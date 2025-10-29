import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QMessageBox, QFrame, QCheckBox, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap

# Ajouter le chemin pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.authcontroller import AuthController

class LoginWindow(QMainWindow):
    """Fenêtre de connexion et d'inscription"""

    login_success = pyqtSignal(object)  # Signal émis lors d'une connexion réussie

    def __init__(self):
        super().__init__()
        self.auth_controller = AuthController()
        self.init_ui()

    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle("Film Finder - Connexion")
        # Rendre la fenêtre redimensionnable et responsive
        self.setMinimumSize(360, 480)
        self.resize(420, 520)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Logo/Titre
        title_label = QLabel("🎬 Film Finder")
        title_label.setObjectName('titleLabel')
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))

        # Frame du formulaire
        form_frame = QFrame()
        form_frame.setObjectName('formFrame')
        form_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)

        # Champs du formulaire
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.email_input.setMinimumHeight(40)
        self.email_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(40)
        self.password_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nom d'utilisateur (inscription)")
        self.username_input.setMinimumHeight(40)
        self.username_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("Prénom (inscription)")
        self.first_name_input.setMinimumHeight(40)
        self.first_name_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Nom (inscription)")
        self.last_name_input.setMinimumHeight(40)
        self.last_name_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Checkbox pour admin (cachée par défaut)
        self.admin_checkbox = QCheckBox("Créer un compte administrateur")
        self.admin_checkbox.setVisible(False)

        # Boutons
        self.login_button = QPushButton("Se connecter")
        self.login_button.setMinimumHeight(45)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)

        self.register_button = QPushButton("Créer un compte")
        self.register_button.setMinimumHeight(45)
        self.register_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1e7e34;
            }
        """)

        self.toggle_mode_button = QPushButton("Je n'ai pas de compte")
        self.toggle_mode_button.setFlat(True)
        self.toggle_mode_button.setStyleSheet("color: #007bff;")
        # expose properties for QSS
        self.register_button.setProperty('secondary', True)
        self.toggle_mode_button.setProperty('flat', True)
        # Taille et comportement responsive
        self.login_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.register_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Ajout des widgets au layout
        form_layout.addWidget(QLabel("Email:"))
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(QLabel("Mot de passe:"))
        form_layout.addWidget(self.password_input)

        # Champs d'inscription (cachés au début)
        self.register_widgets = [
            QLabel("Nom d'utilisateur:"), self.username_input,
            QLabel("Prénom:"), self.first_name_input,
            QLabel("Nom:"), self.last_name_input,
            self.admin_checkbox
        ]

        for widget in self.register_widgets:
            form_layout.addWidget(widget)
            widget.setVisible(False)

        form_layout.addWidget(self.login_button)
        form_layout.addWidget(self.register_button)
        form_layout.addWidget(self.toggle_mode_button)

        form_frame.setLayout(form_layout)

        # Assemblage final
        layout.addWidget(title_label)
        layout.addWidget(form_frame)

        central_widget.setLayout(layout)

        # Connexions des signaux
        self.login_button.clicked.connect(self.handle_login)
        self.register_button.clicked.connect(self.handle_register)
        self.toggle_mode_button.clicked.connect(self.toggle_mode)

        # Mode initial : connexion
        self.is_login_mode = True
        self.update_ui_mode()

        # Charger le style QSS si présent
        try:
            qss_path = os.path.join(os.path.dirname(__file__), 'style.qss')
            if os.path.exists(qss_path):
                with open(qss_path, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
        except Exception:
            pass

    def toggle_mode(self):
        """Bascule entre mode connexion et inscription"""
        self.is_login_mode = not self.is_login_mode
        self.update_ui_mode()

    def update_ui_mode(self):
        """Met à jour l'UI selon le mode"""
        if self.is_login_mode:
            # Mode connexion
            for widget in self.register_widgets:
                widget.setVisible(False)
            self.login_button.setVisible(True)
            self.register_button.setVisible(False)
            self.toggle_mode_button.setText("Je n'ai pas de compte")
            self.setWindowTitle("Film Finder - Connexion")
        else:
            # Mode inscription
            for widget in self.register_widgets:
                widget.setVisible(True)
            self.login_button.setVisible(False)
            self.register_button.setVisible(True)
            self.toggle_mode_button.setText("J'ai déjà un compte")
            self.setWindowTitle("Film Finder - Inscription")

    def handle_login(self):
        """Gère la tentative de connexion"""
        email = self.email_input.text().strip()
        password = self.password_input.text()

        if not email or not password:
            QMessageBox.warning(self, "Erreur", "Veuillez remplir tous les champs")
            return

        user = self.auth_controller.login_user(email, password)
        if user:
            self.login_success.emit(user)
        else:
            QMessageBox.critical(self, "Erreur", "Email ou mot de passe incorrect")

    def handle_register(self):
        """Gère l'inscription"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        username = self.username_input.text().strip()
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        is_admin = self.admin_checkbox.isChecked()

        # Validation
        if not all([email, password, username, first_name, last_name]):
            QMessageBox.warning(self, "Erreur", "Veuillez remplir tous les champs")
            return

        user = self.auth_controller.register_user(
            first_name, last_name, email, username, password, is_admin
        )

        if user:
            QMessageBox.information(self, "Succès", "Compte créé avec succès!")
            self.toggle_mode()  # Retour au mode connexion
            self.clear_form()
        else:
            QMessageBox.critical(self, "Erreur",
                               "Erreur lors de la création du compte. "
                               "Vérifiez que l'email et le nom d'utilisateur sont uniques "
                               "et que le mot de passe respecte les règles de sécurité.")

    def clear_form(self):
        """Vide tous les champs du formulaire"""
        self.email_input.clear()
        self.password_input.clear()
        self.username_input.clear()
        self.first_name_input.clear()
        self.last_name_input.clear()
        self.admin_checkbox.setChecked(False)

def main():
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
