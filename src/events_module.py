import sqlite3
import os
import shutil
import platform
import subprocess
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QFormLayout, QComboBox,
                             QMessageBox, QDialog, QLineEdit, QFileDialog, QHeaderView, QLabel, QInputDialog)
from PyQt5.QtCore import Qt
import auth


# --- Діалог Додавання Заходу ---
class EventDialog(QDialog):
    # ... (Код залишається без змін)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Новий захід")
        self.layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.type_combo = QComboBox()
        self.level_combo = QComboBox()
        self.level_combo.addItems(["Шкільний", "Районний", "Міський", "Обласний", "Всеукраїнський", "Міжнародний"])

        self.load_types()

        self.layout.addRow("Назва заходу:", self.name_input)
        self.layout.addRow("Тип заходу:", self.type_combo)
        self.layout.addRow("Рівень:", self.level_combo)

        self.save_btn = QPushButton("Зберегти")
        self.save_btn.clicked.connect(self.save_data)
        self.layout.addRow(self.save_btn)

    def load_types(self):
        with sqlite3.connect(auth.DB_PATH) as conn:
            for row in conn.execute("SELECT id, name FROM EVENT_TYPES"):
                self.type_combo.addItem(row[1], row[0])

    def save_data(self):
        name = self.name_input.text().strip()
        type_id = self.type_combo.currentData()
        level = self.level_combo.currentText()

        if not name or not type_id:
            QMessageBox.warning(self, "Помилка", "Заповніть назву та оберіть тип заходу.")
            return

        with sqlite3.connect(auth.DB_PATH) as conn:
            conn.execute("INSERT INTO EVENTS (name, event_type_id, level) VALUES (?, ?, ?)",
                         (name, type_id, level))
            conn.commit()
        self.accept()


# --- Діалог Досягнення Учня ---
class AchievementDialog(QDialog):
    # ... (Код залишається без змін)
    def __init__(self, parent=None, achievement_id=None):
        super().__init__(parent)
        self.achievement_id = achievement_id
        self.setWindowTitle("Внесення досягнення")
        self.setMinimumWidth(400)
        self.layout = QFormLayout(self)

        self.student_combo = QComboBox()
        self.event_combo = QComboBox()
        self.place_combo = QComboBox()
        self.place_combo.addItems(["Без місця", "1", "2", "3"])
        self.diploma_combo = QComboBox()
        self.diploma_combo.addItems(["Учасник", "Лауреат", "Переможець"])

        self.file_path = None
        self.file_btn = QPushButton("Обрати скан-копію...")
        self.file_btn.clicked.connect(self.select_file)
        self.file_label = QLabel("Файл не обрано")

        self.load_relations()

        self.layout.addRow("Учень:", self.student_combo)
        self.layout.addRow("Захід:", self.event_combo)
        self.layout.addRow("Місце:", self.place_combo)
        self.layout.addRow("Тип диплому:", self.diploma_combo)
        self.layout.addRow(self.file_btn, self.file_label)

        self.save_btn = QPushButton("Зберегти досягнення")
        self.save_btn.clicked.connect(self.save_data)
        self.layout.addRow(self.save_btn)

    def load_relations(self):
        with sqlite3.connect(auth.DB_PATH) as conn:
            for row in conn.execute("SELECT id, last_name || ' ' || first_name FROM STUDENTS WHERE is_active=1"):
                self.student_combo.addItem(row[1], row[0])
            for row in conn.execute("SELECT id, name || ' (' || level || ')' FROM EVENTS"):
                self.event_combo.addItem(row[1], row[0])

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Обрати документ", "", "Images/PDF (*.png *.jpg *.jpeg *.pdf)")
        if path:
            self.file_path = path
            self.file_label.setText(os.path.basename(path))

    def save_data(self):
        student_id = self.student_combo.currentData()
        event_id = self.event_combo.currentData()
        place = self.place_combo.currentText()
        place_val = int(place) if place.isdigit() else None
        diploma = self.diploma_combo.currentText()
        user_id = auth.Session.current_user['id']

        with sqlite3.connect(auth.DB_PATH) as conn:
            cur = conn.cursor()

            # TC-4.5: Перевірка на дублікати
            if not self.achievement_id:
                cur.execute("SELECT COUNT(*) FROM ACHIEVEMENTS WHERE student_id=? AND event_id=?",
                            (student_id, event_id))
                if cur.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Увага", "Цей учень вже має зареєстроване досягнення на даному заході!")
                    return

            # TC-4.3: Копіювання файлу
            saved_file_name = None
            if self.file_path:
                ext = os.path.splitext(self.file_path)[1]
                saved_file_name = f"doc_{student_id}_{event_id}_{int(datetime.now().timestamp())}{ext}"
                dest_path = os.path.join('data', 'documents', saved_file_name)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                shutil.copy(self.file_path, dest_path)

            cur.execute("""INSERT INTO ACHIEVEMENTS 
                           (student_id, event_id, confirmed_by, place, diploma_type, document_path) 
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (student_id, event_id, user_id, place_val, diploma, saved_file_name))
            conn.commit()
        self.accept()


# --- Головна панель Досягнень ---
class AchievementsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # Кнопки довідників
        top_layout = QHBoxLayout()
        self.add_type_btn = QPushButton("Додати тип заходу")
        self.add_type_btn.clicked.connect(self.add_event_type)
        self.add_event_btn = QPushButton("Додати захід")
        self.add_event_btn.clicked.connect(self.add_event)
        top_layout.addWidget(self.add_type_btn)
        top_layout.addWidget(self.add_event_btn)
        top_layout.addStretch()
        self.layout.addLayout(top_layout)

        # Фільтри (TC-4.7, TC-4.8)
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Пошук заходу...")
        self.search_input.textChanged.connect(self.load_data)

        self.level_filter = QComboBox()
        self.level_filter.addItems(
            ["Всі рівні", "Шкільний", "Районний", "Міський", "Обласний", "Всеукраїнський", "Міжнародний"])
        self.level_filter.currentIndexChanged.connect(self.load_data)

        filter_layout.addWidget(QLabel("Пошук:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(QLabel("Рівень:"))
        filter_layout.addWidget(self.level_filter)
        self.layout.addLayout(filter_layout)

        # Таблиця
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Учень", "Захід", "Рівень", "Місце", "Диплом", "Документ"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.layout.addWidget(self.table)

        # Кнопки управління
        btn_layout = QHBoxLayout()
        self.add_ach_btn = QPushButton("Внести досягнення")
        self.add_ach_btn.clicked.connect(self.add_achievement)
        self.open_doc_btn = QPushButton("Відкрити документ")  # TC-4.4
        self.open_doc_btn.clicked.connect(self.open_document)
        self.del_ach_btn = QPushButton("Видалити запис")
        self.del_ach_btn.clicked.connect(self.delete_achievement)

        btn_layout.addWidget(self.add_ach_btn)
        btn_layout.addWidget(self.open_doc_btn)
        btn_layout.addWidget(self.del_ach_btn)
        self.layout.addLayout(btn_layout)

        self.load_data()

    def add_event_type(self):
        name, ok = QInputDialog.getText(self, "Тип заходу", "Введіть назву (напр. Олімпіада, Конкурс):")
        if ok and name:
            with sqlite3.connect(auth.DB_PATH) as conn:
                conn.execute("INSERT INTO EVENT_TYPES (name) VALUES (?)", (name,))
                conn.commit()
            QMessageBox.information(self, "Успіх", "Тип заходу додано!")

    def add_event(self):
        if EventDialog(self).exec_():
            self.load_data()

    def add_achievement(self):
        if AchievementDialog(self).exec_():
            self.load_data()

    def open_document(self):
        row = self.table.currentRow()
        if row < 0: return

        doc_path = self.table.item(row, 6).data(Qt.UserRole)
        if doc_path:
            full_path = os.path.abspath(os.path.join('data', 'documents', doc_path))
            if os.path.exists(full_path):
                # Відкриття файлу стандартною програмою ОС (TC-4.4)
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

    def delete_achievement(self):
        row = self.table.currentRow()
        if row < 0: return

        ach_id = self.table.item(row, 0).text()
        doc_path = self.table.item(row, 6).data(Qt.UserRole)  # Отримуємо ім'я файлу

        reply = QMessageBox.question(self, 'Підтвердження',
                                     "Видалити запис? Прикріплений файл також буде видалено назавжди.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # TC-4.6: Видалення з БД та з диска
            with sqlite3.connect(auth.DB_PATH) as conn:
                conn.execute("DELETE FROM ACHIEVEMENTS WHERE id=?", (ach_id,))
                conn.commit()

            if doc_path:
                full_path = os.path.join('data', 'documents', doc_path)
                if os.path.exists(full_path):
                    os.remove(full_path)

            self.load_data()

    def load_data(self):
        search = f"%{self.search_input.text()}%"
        level_filter = self.level_filter.currentText()

        query = """
            SELECT a.id, s.last_name || ' ' || s.first_name, e.name, e.level, a.place, a.diploma_type, a.document_path 
            FROM ACHIEVEMENTS a
            JOIN STUDENTS s ON a.student_id = s.id
            JOIN EVENTS e ON a.event_id = e.id
            WHERE e.name LIKE ?
        """
        params = [search]

        if level_filter != "Всі рівні":
            query += " AND e.level = ?"
            params.append(level_filter)

        query += " ORDER BY a.created_at DESC"

        with sqlite3.connect(auth.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()

        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.table.setItem(i, 1, QTableWidgetItem(row[1]))
            self.table.setItem(i, 2, QTableWidgetItem(row[2]))
            self.table.setItem(i, 3, QTableWidgetItem(row[3]))
            self.table.setItem(i, 4, QTableWidgetItem(str(row[4]) if row[4] else "Без місця"))
            self.table.setItem(i, 5, QTableWidgetItem(row[5]))

            # Зберігаємо реальний шлях до файлу у прихованих даних (Qt.UserRole)
            doc_item = QTableWidgetItem("✅ Є" if row[6] else "❌ Немає")
            doc_item.setData(Qt.UserRole, row[6])
            self.table.setItem(i, 6, doc_item)