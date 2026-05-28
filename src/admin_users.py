import sqlite3
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLineEdit, QComboBox, QPushButton, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QSplitter)
from PyQt5.QtCore import Qt
from auth import hash_password, DB_PATH


class UserManagementWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        self.splitter = QSplitter(Qt.Horizontal)
        self.layout.addWidget(self.splitter)

        # --- ЛІВА ЧАСТИНА: Список користувачів ---
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_layout.setContentsMargins(0, 0, 0, 0)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(["ID", "Логін", "Роль", "Створено"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.users_table.itemSelectionChanged.connect(self.load_user_to_form)
        self.left_layout.addWidget(self.users_table)

        btn_layout = QHBoxLayout()
        self.del_btn = QPushButton("Видалити користувача")
        self.del_btn.clicked.connect(self.delete_user)
        btn_layout.addWidget(self.del_btn)
        self.left_layout.addLayout(btn_layout)

        # --- ПРАВА ЧАСТИНА: Форма ---
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)

        form_layout = QFormLayout()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Залиште порожнім, щоб не змінювати пароль")

        self.role_combo = QComboBox()
        self.role_combo.addItems(["Адміністратор", "Вчитель / Куратор", "Класний керівник", "Учень / Батьки"])

        form_layout.addRow("Логін:", self.username_input)
        form_layout.addRow("Новий Пароль:", self.password_input)
        form_layout.addRow("Роль:", self.role_combo)

        self.right_layout.addLayout(form_layout)

        action_layout = QHBoxLayout()
        self.clear_btn = QPushButton("Очистити форму")
        self.clear_btn.clicked.connect(self.clear_form)
        self.save_btn = QPushButton("Зберегти / Додати")
        self.save_btn.clicked.connect(self.save_user)

        action_layout.addWidget(self.clear_btn)
        action_layout.addWidget(self.save_btn)
        self.right_layout.addLayout(action_layout)
        self.right_layout.addStretch()

        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.right_widget)
        self.splitter.setSizes([500, 300])

        self.current_user_id = None
        self.load_users()

    def load_users(self):
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, username, role, date(created_at) FROM USERS ORDER BY id")
            rows = cur.fetchall()

        self.users_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j in range(4):
                self.users_table.setItem(i, j, QTableWidgetItem(str(row[j])))

    def load_user_to_form(self):
        row = self.users_table.currentRow()
        if row < 0: return

        self.current_user_id = self.users_table.item(row, 0).text()
        self.username_input.setText(self.users_table.item(row, 1).text())
        self.role_combo.setCurrentText(self.users_table.item(row, 2).text())
        self.password_input.clear()

    def clear_form(self):
        self.current_user_id = None
        self.username_input.clear()
        self.password_input.clear()
        self.users_table.clearSelection()

    def save_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        role = self.role_combo.currentText()

        if not username:
            QMessageBox.warning(self, "Помилка", "Логін є обов'язковим!")
            return

        try:
            with sqlite3.connect(DB_PATH) as conn:
                if self.current_user_id:
                    # Оновлення існуючого
                    if password:
                        hashed = hash_password(password)
                        conn.execute("UPDATE USERS SET username=?, password_hash=?, role=? WHERE id=?",
                                     (username, hashed, role, self.current_user_id))
                    else:
                        conn.execute("UPDATE USERS SET username=?, role=? WHERE id=?",
                                     (username, role, self.current_user_id))
                    QMessageBox.information(self, "Успіх", "Дані користувача оновлено.")
                else:
                    # Додавання нового
                    if not password:
                        QMessageBox.warning(self, "Помилка", "Для нового користувача обов'язково введіть пароль!")
                        return
                    hashed = hash_password(password)
                    conn.execute("INSERT INTO USERS (username, password_hash, role) VALUES (?, ?, ?)",
                                 (username, hashed, role))
                    QMessageBox.information(self, "Успіх", "Користувача додано!")
                conn.commit()
            self.load_users()
            self.clear_form()
        except sqlite3.IntegrityError:
            QMessageBox.critical(self, "Помилка", "Користувач з таким логіном вже існує!")

    def delete_user(self):
        row = self.users_table.currentRow()
        if row < 0: return

        user_id = self.users_table.item(row, 0).text()
        username = self.users_table.item(row, 1).text()

        if username == "admin":
            QMessageBox.warning(self, "Увага", "Неможливо видалити головного адміністратора!")
            return

        reply = QMessageBox.question(self, 'Підтвердження', f"Видалити користувача {username}?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("DELETE FROM USERS WHERE id=?", (user_id,))
                conn.commit()
            self.load_users()
            self.clear_form()