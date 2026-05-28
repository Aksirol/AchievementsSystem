import sqlite3
import os
import platform
import subprocess
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QComboBox,
                             QLabel, QHeaderView, QTabWidget, QMessageBox)
from PyQt5.QtCore import Qt
import auth


class PortfolioPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # --- Блок вибору учня ---
        selection_layout = QHBoxLayout()
        self.class_combo = QComboBox()
        self.class_combo.currentIndexChanged.connect(self.load_students)

        self.student_combo = QComboBox()
        self.student_combo.currentIndexChanged.connect(self.load_portfolio)

        selection_layout.addWidget(QLabel("Клас:"))
        selection_layout.addWidget(self.class_combo)
        selection_layout.addWidget(QLabel("Учень:"))
        selection_layout.addWidget(self.student_combo)
        selection_layout.addStretch()

        self.layout.addLayout(selection_layout)

        # --- Вкладки з даними ---
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.init_achievements_tab()
        self.init_clubs_tab()

        self.load_classes()

    def init_achievements_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.ach_table = QTableWidget()
        self.ach_table.setColumnCount(5)
        self.ach_table.setHorizontalHeaderLabels(["Захід", "Рівень", "Місце", "Диплом", "Документ"])
        self.ach_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ach_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.ach_table)

        btn_layout = QHBoxLayout()
        self.open_doc_btn = QPushButton("Відкрити скан-копію")
        self.open_doc_btn.clicked.connect(self.open_document)
        btn_layout.addWidget(self.open_doc_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.tabs.addTab(tab, "🏆 Досягнення у заходах")

    def init_clubs_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.clubs_table = QTableWidget()
        self.clubs_table.setColumnCount(5)
        self.clubs_table.setHorizontalHeaderLabels(["Гурток", "Напрямок", "Дата вступу", "Дата виходу", "Статус"])
        self.clubs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.clubs_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.clubs_table)

        self.tabs.addTab(tab, "⚽ Гуртки та Секції")

    def load_classes(self):
        self.class_combo.clear()

        # Безпека для ролі «Учень / Батьки»
        if auth.Session.current_user['role'] == "Учень / Батьки":
            username = auth.Session.current_user['username']
            with sqlite3.connect(auth.DB_PATH) as conn:
                cur = conn.cursor()
                # Припускаємо, що логін учня дорівнює його прізвищу
                cur.execute("SELECT class_id, id, last_name || ' ' || first_name FROM STUDENTS WHERE last_name = ?",
                            (username,))
                row = cur.fetchone()
                if row:
                    class_id, st_id, st_name = row
                    self.class_combo.addItem("Ваш клас", class_id)
                    self.student_combo.clear()
                    self.student_combo.addItem(st_name, st_id)
                    self.class_combo.setEnabled(False)
                    self.student_combo.setEnabled(False)
                    self.load_portfolio()
                else:
                    self.class_combo.addItem("Доступ закрито", None)
                    self.class_combo.setEnabled(False)
                    self.student_combo.setEnabled(False)
                    QMessageBox.warning(self, "Увага",
                                        f"Ваш логін '{username}' не співпадає з прізвищем жодного учня. Зверніться до адміністратора для налаштування доступу.")
            return

        self.class_combo.addItem("Оберіть клас...", None)
        with sqlite3.connect(auth.DB_PATH) as conn:
            for row in conn.execute("SELECT id, name FROM CLASSES ORDER BY grade_number, name"):
                self.class_combo.addItem(row[1], row[0])

    def load_students(self):
        self.student_combo.clear()
        class_id = self.class_combo.currentData()
        if not class_id:
            self.ach_table.setRowCount(0)
            self.clubs_table.setRowCount(0)
            return

        self.student_combo.addItem("Оберіть учня...", None)
        with sqlite3.connect(auth.DB_PATH) as conn:
            for row in conn.execute(
                    "SELECT id, last_name || ' ' || first_name FROM STUDENTS WHERE class_id = ? ORDER BY last_name",
                    (class_id,)):
                self.student_combo.addItem(row[1], row[0])

    def load_portfolio(self):
        student_id = self.student_combo.currentData()
        if not student_id:
            self.ach_table.setRowCount(0)
            self.clubs_table.setRowCount(0)
            return

        with sqlite3.connect(auth.DB_PATH) as conn:
            cur = conn.cursor()

            # Завантаження досягнень
            query_ach = """
                SELECT e.name, e.level, a.place, a.diploma_type, a.document_path 
                FROM ACHIEVEMENTS a
                JOIN EVENTS e ON a.event_id = e.id
                WHERE a.student_id = ?
                ORDER BY e.event_date DESC, a.created_at DESC
            """
            cur.execute(query_ach, (student_id,))
            ach_rows = cur.fetchall()

            self.ach_table.setRowCount(len(ach_rows))
            for i, row in enumerate(ach_rows):
                self.ach_table.setItem(i, 0, QTableWidgetItem(row[0]))
                self.ach_table.setItem(i, 1, QTableWidgetItem(row[1]))
                self.ach_table.setItem(i, 2, QTableWidgetItem(str(row[2]) if row[2] else "Без місця"))
                self.ach_table.setItem(i, 3, QTableWidgetItem(row[3]))

                doc_item = QTableWidgetItem("✅ Прикріплено" if row[4] else "❌ Відсутній")
                doc_item.setData(Qt.UserRole, row[4])  # Приховано зберігаємо шлях до файлу
                self.ach_table.setItem(i, 4, doc_item)

            # Завантаження гуртків
            query_clubs = """
                SELECT c.name, c.category, cm.joined_at, cm.left_at, cm.is_active 
                FROM CLUB_MEMBERS cm
                JOIN CLUBS c ON cm.club_id = c.id
                WHERE cm.student_id = ?
                ORDER BY cm.is_active DESC, cm.joined_at DESC
            """
            cur.execute(query_clubs, (student_id,))
            club_rows = cur.fetchall()

            self.clubs_table.setRowCount(len(club_rows))
            for i, row in enumerate(club_rows):
                self.clubs_table.setItem(i, 0, QTableWidgetItem(row[0]))
                self.clubs_table.setItem(i, 1, QTableWidgetItem(row[1]))
                self.clubs_table.setItem(i, 2, QTableWidgetItem(row[2] if row[2] else "—"))
                self.clubs_table.setItem(i, 3, QTableWidgetItem(row[3] if row[3] else "—"))
                status = "Активний" if row[4] else "Відрахований"
                self.clubs_table.setItem(i, 4, QTableWidgetItem(status))

    def open_document(self):
        row = self.ach_table.currentRow()
        if row < 0: return

        doc_path = self.ach_table.item(row, 4).data(Qt.UserRole)
        if doc_path:
            full_path = os.path.abspath(os.path.join(auth.BASE_DIR, 'data', 'documents', doc_path))
            if os.path.exists(full_path):
                if platform.system() == 'Windows':
                    os.startfile(full_path)
                elif platform.system() == 'Darwin':
                    subprocess.call(['open', full_path])
                else:
                    subprocess.call(['xdg-open', full_path])
            else:
                QMessageBox.warning(self, "Помилка", "Файл не знайдено на диску.")
        else:
            QMessageBox.information(self, "Інфо", "До цього досягнення документ не прикріплено.")