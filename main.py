import sys
import os

# Ensure project root is importable
ROOT = os.path.dirname(__file__)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

def main():
    """Application entry point: show LoginWindow and open MainWindow on success."""
    try:
        from PyQt5.QtWidgets import QApplication
    except Exception as e:
        print("PyQt5 is required to run the GUI. Error:", e)
        sys.exit(1)

    app = QApplication(sys.argv)

    try:
        # Import UI components (these import controllers/models)
        from ui.login_window import LoginWindow
        from ui.main_window import MainWindow

        login = LoginWindow()

        def _on_login(user):
            # Open main window when login succeeds
            mw = MainWindow(user)
            # Keep a reference on the login window to avoid GC closing the window
            try:
                login._main_window = mw
            except Exception:
                pass
            mw.show()
            # hide login window to avoid duplicate windows
            try:
                login.hide()
            except Exception:
                pass

        login.login_success.connect(_on_login)
        login.show()

    except Exception as e:
        # If for some reason the UI cannot be imported (headless/dev),
        # fallback to opening a simple MainWindow with a dev user.
        print("Warning: failed to import UI components:", e)
        try:
            from core.users import User
            from ui.main_window import MainWindow
            user = User.create_user(0, 'Dev', 'User', 'dev@local', 'dev', 'DevPass1!')
            window = MainWindow(user)
            window.show()
        except Exception as e2:
            print("Fatal: cannot start GUI. Error:", e2)
            sys.exit(1)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
