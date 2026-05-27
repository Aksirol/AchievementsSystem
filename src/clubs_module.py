import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QFormLayout, QComboBox,
                             QMessageBox, QDialog, QLineEdit, QHeaderView, QLabel, QSplitter)
from PyQt5.QtCore import Qt, QDate
import auth


# --- Діалог Додавання Гуртка ---
class ClubDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новий гурток / секція")
        self.setMinimumWidth(350)
        self.layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Назва (напр. Волейбол, Авіамоделювання)")

        self.category_combo = QComboBox()
        self.category_combo.addItems(
            ["Спортивний", "Науково-технічний", "Художньо-естетичний", "Туристсько-краєзнавчий", "Інше"])

        self.supervisor_combo = QComboBox()
        self.schedule_input = QLineEdit()
        self.schedule_input.setPlaceholderText("Напр. Пн, Ср 15:00-16:30")

        self.load_teachers()

        self.layout.addRow("Назва гуртка:", self.name_input)
        self.layout.addRow("Напрямок:", self.category_combo)
        self.layout.addRow("Керівник:", self.supervisor_combo)
        self.layout.addRow("Розклад:", self.schedule_input)

        self.save_btn = QPushButton("Зберегти")
        self.save_btn.clicked.connect(self.save_data)
        self.layout.addRow(self.save_btn)

    def load_teachers(self):
        with sqlite3.connect(auth.DB_PATH) as conn:
            self.supervisor_combo.addItem("Не призначено", None)
            for row in conn.execute("SELECT id, last_name || ' ' || first_name FROM TEACHERS"):
                self.supervisor_combo.addItem(row[1], row[0])

    def save_data(self):
        name = self.name_input.text().strip()
        category = self.category_combo.currentText()
        supervisor_id = self.supervisor_combo.currentData()
        schedule = self.schedule_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Помилка", "Введіть назву гуртка.")
            return

        with sqlite3.connect(auth.DB_PATH) as conn:
            conn.execute("INSERT INTO CLUBS (name, category, supervisor_id, schedule) VALUES (?, ?, ?, ?)",
                         (name, category, supervisor_id, schedule))
            conn.commit()
        self.accept()


# --- Діалог Запису Учня в Гурток ---
class EnrollDialog(QDialog):
    def __init__(self, club_id, parent=None):
        super().__init__(parent)
        self.club_id = club_id
        self.setWindowTitle("Запис учня до гуртка")
        self.setMinimumWidth(300)
        self.layout = QFormLayout(self)

        self.student_combo = QComboBox()
        self.load_students()

        self.date_input = QLineEdit()
        self.date_input.setText(QDate.currentDate().toString("yyyy-MM-dd"))
        self.date_input.setPlaceholderText("РРРР-ММ-ДД")

        self.layout.addRow("Учень:", self.student_combo)
        self.layout.addRow("Дата вступу:", self.date_input)

        self.save_btn = QPushButton("Записати")
        self.save_btn.clicked.connect(self.save_data)
        self.layout.addRow(self.save_btn)

    def load_students(self):
        # Завантажуємо тільки тих активних учнів, які ще НЕ є активними учасниками цього гуртка
        query = """
            SELECT id, last_name || ' ' || first_name 
            FROM STUDENTS 
            WHERE is_active = 1 
            AND id NOT IN (
                SELECT student_id FROM CLUB_MEMBERS WHERE club_id = ? AND is_active = 1
            )
            ORDER BY last_name
        """
        with sqlite3.connect(auth.DB_PATH) as conn:
            for row in conn.execute(query, (self.club_id,)):
                self.student_combo.addItem(row[1], row[0])

    def save_data(self):
        student_id = self.student_combo.currentData()
        join_date = self.date_input.text().strip()

        if not student_id:
            QMessageBox.warning(self, "Помилка", "Немає доступних учнів для запису.")
            return

        with sqlite3.connect(auth.DB_PATH) as conn:
            conn.execute("INSERT INTO CLUB_MEMBERS (club_id, student_id, joined_at, is_active) VALUES (?, ?, ?, 1)",
                         (self.club_id, student_id, join_date))
            conn.commit()
        self.accept()


# --- Головна панель Гуртків ---
class ClubsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # Використовуємо QSplitter для розділення екрану на дві частини
        self.splitter = QSplitter(Qt.Horizontal)
        self.layout.addWidget(self.splitter)

        # --- ЛІВА ЧАСТИНА: Гуртки ---
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_layout.setContentsMargins(0, 0, 0, 0)

        self.add_club_btn = QPushButton("Додати гурток")
        self.add_club_btn.clicked.connect(self.add_club)
        self.left_layout.addWidget(self.add_club_btn)

        self.clubs_table = QTableWidget()
        self.clubs_table.setColumnCount(4)
        self.clubs_table.setHorizontalHeaderLabels(["ID", "Назва", "Категорія", "Керівник"])
        self.clubs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.clubs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.clubs_table.itemSelectionChanged.connect(self.load_members)
        self.left_layout.addWidget(self.clubs_table)

        # --- ПРАВА ЧАСТИНА: Учасники ---
        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)
        self.right_layout.setContentsMargins(0, 0, 0, 0)

        btn_layout = QHBoxLayout()
        self.enroll_btn = QPushButton("Записати учня")
        self.enroll_btn.clicked.connect(self.enroll_student)
        self.remove_btn = QPushButton("Відрахувати учня")
        self.remove_btn.clicked.connect(self.remove_student)

        btn_layout.addWidget(self.enroll_btn)
        btn_layout.addWidget(self.remove_btn)
        self.right_layout.addLayout(btn_layout)

        self.members_table = QTableWidget()
        self.members_table.setColumnCount(5)
        self.members_table.setHorizontalHeaderLabels(["ID Запису", "Учень", "Дата вступу", "Дата виходу", "Статус"])
        self.members_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.members_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.right_layout.addWidget(self.members_table)

        # Додаємо віджети до сплітера
        self.splitter.addWidget(self.left_widget)
        self.splitter.addWidget(self.right_widget)
        # Встановлюємо пропорції 40% на 60%
        self.splitter.setSizes([400, 600])

        self.load_clubs()

    def add_club(self):
        if ClubDialog(self).exec_():
            self.load_clubs()

    def load_clubs(self):
        query = """
            SELECT c.id, c.name, c.category, t.last_name || ' ' || t.first_name 
            FROM CLUBS c
            LEFT JOIN TEACHERS t ON c.supervisor_id = t.id
        """
        with sqlite3.connect(auth.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute(query)
            rows = cur.fetchall()

        self.clubs_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.clubs_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.clubs_table.setItem(i, 1, QTableWidgetItem(row[1]))
            self.clubs_table.setItem(i, 2, QTableWidgetItem(row[2]))
            self.clubs_table.setItem(i, 3, QTableWidgetItem(row[3] if row[3] else "—"))

    def load_members(self):
        row = self.clubs_table.currentRow()
        if row < 0:
            self.members_table.setRowCount(0)
            return

        club_id = self.clubs_table.item(row, 0).text()

        query = """
            SELECT cm.id, s.last_name || ' ' || s.first_name, cm.joined_at, cm.left_at, cm.is_active
            FROM CLUB_MEMBERS cm
            JOIN STUDENTS s ON cm.student_id = s.id
            WHERE cm.club_id = ?
            ORDER BY cm.is_active DESC, s.last_name
        """
        with sqlite3.connect(auth.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute(query, (club_id,))
            rows = cur.fetchall()

        self.members_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.members_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.members_table.setItem(i, 1, QTableWidgetItem(row[1]))
            self.members_table.setItem(i, 2, QTableWidgetItem(row[2]))
            self.members_table.setItem(i, 3, QTableWidgetItem(row[3] if row[3] else "—"))
            status = "Активний" if row[4] else "Відрахований"
            self.members_table.setItem(i, 4, QTableWidgetItem(status))

    def enroll_student(self):
        row = self.clubs_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Увага", "Оберіть гурток зі списку зліва.")
            return

        club_id = self.clubs_table.item(row, 0).text()
        if EnrollDialog(club_id, self).exec_():
            self.load_members()

    def remove_student(self):
        row = self.members_table.currentRow()
        if row < 0: return

        record_id = self.members_table.item(row, 0).text()
        status = self.members_table.item(row, 4).text()

        if status == "Відрахований":
            QMessageBox.information(self, "Інфо", "Цей учень вже відрахований з гуртка.")
            return

        reply = QMessageBox.question(self, 'Підтвердження',
                                     "Відрахувати учня? Його історія участі збережеться.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            leave_date = QDate.currentDate().toString("yyyy-MM-dd")
            with sqlite3.connect(auth.DB_PATH) as conn:
                conn.execute("UPDATE CLUB_MEMBERS SET is_active = 0, left_at = ? WHERE id = ?", (leave_date, record_id))
                conn.commit()
            self.load_members()