import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QStackedWidget, QDialog, QListWidget)
from PyQt5.QtCore import Qt

from auth import create_default_admin, Session, logout
from login_window import LoginDialog
from admin_users import UserManagementWidget
from students_module import StudentsPanel
from events_module import AchievementsPanel
from clubs_module import ClubsPanel
from reports_module import ReportsPanel
from backup_module import BackupPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система обліку позакласних досягнень")
        self.setGeometry(100, 100, 1000, 600)
        self.setMinimumSize(900, 600)

        # Центральний віджет
        central_widget = QWidget()
        self.main_layout = QVBoxLayout(central_widget)
        self.setCentralWidget(central_widget)

        # Верхня панель (Інформація про користувача та кнопка Виходу)
        top_layout = QHBoxLayout()
        self.user_info_label = QLabel()
        top_layout.addWidget(self.user_info_label, alignment=Qt.AlignLeft)

        self.logout_btn = QPushButton("Вийти з системи")
        self.logout_btn.setFixedWidth(150)
        self.logout_btn.clicked.connect(self.handle_logout)
        top_layout.addWidget(self.logout_btn, alignment=Qt.AlignRight)

        self.main_layout.addLayout(top_layout)

        # Головна робоча область: Бокове меню (зліва) + Контент (справа)
        content_layout = QHBoxLayout()

        # Налаштування бокового меню
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(220)
        self.sidebar.currentRowChanged.connect(self.display_panel)
        content_layout.addWidget(self.sidebar)

        # QStackedWidget для перемикання між різними екранами
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        self.main_layout.addLayout(content_layout)

        self.setup_ui_for_role()

    def setup_ui_for_role(self):
        """Налаштовує інтерфейс залежно від ролі користувача."""
        role = Session.current_user['role']
        username = Session.current_user['username']
        self.user_info_label.setText(f"Користувач: {username} | Роль: {role}")

        # Динамічне заповнення меню залежно від прав доступу
        if role == "Адміністратор":
            self.add_panel("👥 Користувачі", UserManagementWidget())
            self.add_panel("🎓 Учні та Класи", StudentsPanel())
            self.add_panel("🏆 Заходи та Досягнення", AchievementsPanel())
            self.add_panel("⚽ Гуртки та Секції", ClubsPanel())
            self.add_panel("📊 Звіти та Характеристики", ReportsPanel())
            self.add_panel("💾 Резервне копіювання", BackupPanel()) 

        elif role in ["Вчитель / Куратор", "Класний керівник"]:
            self.add_panel("🎓 Учні та Класи", StudentsPanel())
            self.add_panel("🏆 Заходи та Досягнення", AchievementsPanel())
            self.add_panel("⚽ Гуртки та Секції", ClubsPanel())
            self.add_panel("📊 Звіти та Характеристики", ReportsPanel())

        elif role == "Учень / Батьки":
            welcome_label = QLabel("Режим перегляду портфоліо учня (в розробці).")
            welcome_label.setAlignment(Qt.AlignCenter)
            self.add_panel("📂 Моє Портфоліо", welcome_label)

        # Вибираємо перший пункт меню за замовчуванням
        if self.sidebar.count() > 0:
            self.sidebar.setCurrentRow(0)

    def add_panel(self, name, widget):
        """Допоміжний метод: додає кнопку в меню та віджет у стек."""
        self.sidebar.addItem(name)
        self.stack.addWidget(widget)

    def display_panel(self, index):
        """Перемикає видимий віджет у стеку при кліку на меню."""
        self.stack.setCurrentIndex(index)

    def handle_logout(self):
        """Механізм виходу та блокування сесії."""
        logout()
        self.close()  # Закриваємо головне вікно
        show_login_and_start()  # Знову викликаємо форму логіну


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

    # Перед запуском перевіряємо, чи є хоча б один адмін
    create_default_admin()

    show_login_and_start()
    sys.exit(app.exec_())