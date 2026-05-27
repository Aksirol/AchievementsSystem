import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QStackedWidget, QDialog
from PyQt5.QtCore import Qt

from auth import create_default_admin, Session, logout
from login_window import LoginDialog
from admin_users import UserManagementWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система обліку позакласних досягнень")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumSize(800, 600)

        # Центральний віджет
        central_widget = QWidget()
        self.main_layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # Інформація про користувача та кнопка виходу
        self.user_info_label = QLabel()
        self.main_layout.addWidget(self.user_info_label, alignment=Qt.AlignRight)

        self.logout_btn = QPushButton("Вийти з системи")
        self.logout_btn.setFixedWidth(150)
        self.logout_btn.clicked.connect(self.handle_logout)
        self.main_layout.addWidget(self.logout_btn, alignment=Qt.AlignRight)

        # QStackedWidget для перемикання між різними екранами
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        self.setup_ui_for_role()

    def setup_ui_for_role(self):
        """Налаштовує інтерфейс залежно від ролі користувача (Приховування/відображення)."""
        role = Session.current_user['role']
        username = Session.current_user['username']
        self.user_info_label.setText(f"Користувач: {username} | Роль: {role}")

        # Екран-заглушка для всіх
        welcome_label = QLabel(f"Вітаємо в системі! Ваш рівень доступу дозволяє працювати як {role}.")
        welcome_label.setAlignment(Qt.AlignCenter)
        self.stack.addWidget(welcome_label)

        # Логіка ролей: додаємо специфічні віджети
        if role == "Адміністратор":
            self.admin_panel = UserManagementWidget()
            self.stack.addWidget(self.admin_panel)
            self.stack.setCurrentWidget(self.admin_panel)
        elif role == "Вчитель / Куратор":
            # Тут буде панель вчителя (Фаза 3)
            pass
        elif role == "Класний керівник":
            # Тут буде панель класного керівника
            pass
        elif role == "Учень / Батьки":
            # Тут буде панель учня (тільки читання)
            pass

    def handle_logout(self):
        """Механізм виходу та блокування сесії."""
        logout()
        self.close()  # Закриваємо головне вікно
        show_login_and_start()  # Знову викликаємо логін


def show_login_and_start():
    """Контролер запуску програми."""
    login_dialog = LoginDialog()
    if login_dialog.exec_() == QDialog.Accepted:
        # Якщо вхід успішний, відкриваємо головне вікно
        global main_window
        main_window = MainWindow()
        main_window.show()
    else:
        # Якщо вікно закрили хрестиком
        sys.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    # Перед запуском перевіряємо, чи є хоча б один адмін, якщо ні - створюємо admin/admin123
    create_default_admin()

    show_login_and_start()
    sys.exit(app.exec_())