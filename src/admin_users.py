import sqlite3
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QPushButton, QMessageBox
from auth import hash_password, DB_PATH


class UserManagementWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()

        form_layout = QFormLayout()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        self.role_combo = QComboBox()
        self.role_combo.addItems(["Адміністратор", "Вчитель / Куратор", "Класний керівник", "Учень / Батьки"])

        form_layout.addRow("Логін:", self.username_input)
        form_layout.addRow("Пароль:", self.password_input)
        form_layout.addRow("Роль:", self.role_combo)

        self.add_btn = QPushButton("Додати користувача")
        self.add_btn.clicked.connect(self.add_user)

        self.layout.addLayout(form_layout)
        self.layout.addWidget(self.add_btn)
        self.setLayout(self.layout)

    def add_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_combo.currentText()

        if not username or not password:
            QMessageBox.warning(self, "Помилка", "Заповніть всі поля!")
            return

        hashed = hash_password(password)
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO USERS (username, password_hash, role) VALUES (?, ?, ?)",
                           (username, hashed, role))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Успіх", f"Користувача {username} додано!")
            self.username_input.clear()
            self.password_input.clear()
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Помилка", "Користувач з таким логіном вже існує!")