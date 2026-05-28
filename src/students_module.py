import sqlite3
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QLineEdit, QFormLayout,
                             QMessageBox, QComboBox, QDialog, QCheckBox, QHeaderView, QLabel, QInputDialog, QDateEdit)
from PyQt5.QtCore import Qt, QDate
import auth


# --- Діалог Додавання Класу ---
class ClassDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Додати клас")
        self.layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Напр. 10-А")
        self.grade_input = QLineEdit()
        self.grade_input.setPlaceholderText("Напр. 10")
        self.year_combo = QComboBox()
        self.curator_combo = QComboBox()

        self.load_relations()

        self.layout.addRow("Назва класу:", self.name_input)
        self.layout.addRow("Паралель (число):", self.grade_input)
        self.layout.addRow("Навчальний рік:", self.year_combo)
        self.layout.addRow("Куратор:", self.curator_combo)

        self.save_btn = QPushButton("Зберегти")
        self.save_btn.clicked.connect(self.save_data)
        self.layout.addRow(self.save_btn)

    def load_relations(self):
        with sqlite3.connect(auth.DB_PATH) as conn:
            cur = conn.cursor()
            self.year_combo.addItem("Не обрано", None)
            for row in cur.execute("SELECT id, name FROM ACADEMIC_YEARS"):
                self.year_combo.addItem(row[1], row[0])

            self.curator_combo.addItem("Не обрано", None)
            for row in cur.execute("SELECT id, last_name || ' ' || first_name FROM TEACHERS"):
                self.curator_combo.addItem(row[1], row[0])

    def save_data(self):
        name = self.name_input.text().strip()
        grade = self.grade_input.text().strip()
        year_id = self.year_combo.currentData()
        curator_id = self.curator_combo.currentData()

        if not name or not grade.isdigit():
            QMessageBox.warning(self, "Помилка", "Введіть коректну назву та числову паралель.")
            return

        with sqlite3.connect(auth.DB_PATH) as conn:
            conn.execute("INSERT INTO CLASSES (name, grade_number, academic_year_id, curator_id) VALUES (?, ?, ?, ?)",
                         (name, int(grade), year_id, curator_id))
            conn.commit()
        self.accept()


# --- Діалог Навчального року (Виправлення КРИТ-3) ---
class AcademicYearDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Додати навчальний рік")
        self.layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Напр. 2026-2027")

        # Динамічне підставлення поточного року
        current_year = QDate.currentDate().year()

        self.start_date = QDateEdit()
        self.start_date.setDate(QDate(current_year, 9, 1))
        self.start_date.setCalendarPopup(True)

        self.end_date = QDateEdit()
        self.end_date.setDate(QDate(current_year + 1, 5, 31))
        self.end_date.setCalendarPopup(True)

        self.layout.addRow("Назва року:", self.name_input)
        self.layout.addRow("Дата початку:", self.start_date)
        self.layout.addRow("Дата закінчення:", self.end_date)

        self.save_btn = QPushButton("Зберегти")
        self.save_btn.clicked.connect(self.save_data)
        self.layout.addRow(self.save_btn)

    def save_data(self):
        name = self.name_input.text().strip()
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")

        if not name:
            QMessageBox.warning(self, "Помилка", "Введіть назву навчального року.")
            return

        with sqlite3.connect(auth.DB_PATH) as conn:
            conn.execute("INSERT INTO ACADEMIC_YEARS (name, start_date, end_date) VALUES (?, ?, ?)",
                         (name, start, end))
            conn.commit()
        self.accept()

# --- Діалог Додавання/Редагування Учня ---
# --- Діалог Додавання/Редагування Учня ---
class StudentDialog(QDialog):
    def __init__(self, student_id=None, parent=None):
        super().__init__(parent)
        self.student_id = student_id
        self.setWindowTitle("Картка учня")
        self.setMinimumWidth(350)
        self.layout = QFormLayout(self)

        self.fname_input = QLineEdit()
        self.lname_input = QLineEdit()
        self.class_combo = QComboBox()

        # Нові поля: дата народження та фото
        self.birth_date = QDateEdit()
        self.birth_date.setCalendarPopup(True)
        self.birth_date.setDate(QDate(2010, 1, 1))

        self.photo_path = None
        from PyQt5.QtWidgets import QFileDialog
        self.photo_btn = QPushButton("Обрати фото...")
        self.photo_btn.clicked.connect(self.select_photo)
        self.photo_label = QLabel("Фото не обрано")

        self.load_classes()

        self.layout.addRow("Ім'я:", self.fname_input)
        self.layout.addRow("Прізвище:", self.lname_input)
        self.layout.addRow("Дата народж.:", self.birth_date)
        self.layout.addRow("Клас:", self.class_combo)
        self.layout.addRow(self.photo_btn, self.photo_label)

        self.save_btn = QPushButton("Зберегти")
        self.save_btn.clicked.connect(self.save_data)
        self.layout.addRow(self.save_btn)

        if self.student_id:
            self.load_data()

    def load_classes(self):
        self.class_combo.addItem("Не призначено", None)
        with sqlite3.connect(auth.DB_PATH) as conn:
            for row in conn.execute("SELECT id, name FROM CLASSES"):
                self.class_combo.addItem(row[1], row[0])

    def select_photo(self):
        from PyQt5.QtWidgets import QFileDialog
        import os
        path, _ = QFileDialog.getOpenFileName(self, "Обрати фото", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.photo_path = path
            self.photo_label.setText(os.path.basename(path))

    def load_data(self):
        with sqlite3.connect(auth.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT first_name, last_name, class_id, birth_date, photo_path FROM STUDENTS WHERE id=?",
                        (self.student_id,))
            row = cur.fetchone()
            if row:
                self.fname_input.setText(row[0])
                self.lname_input.setText(row[1])
                if row[2]:
                    index = self.class_combo.findData(row[2])
                    self.class_combo.setCurrentIndex(index)
                if row[3]:
                    self.birth_date.setDate(QDate.fromString(row[3], "yyyy-MM-dd"))
                if row[4]:
                    self.photo_label.setText("✅ Фото завантажено")

    def save_data(self):
        fname = self.fname_input.text().strip()
        lname = self.lname_input.text().strip()
        class_id = self.class_combo.currentData()
        bdate = self.birth_date.date().toString("yyyy-MM-dd")

        if not fname or not lname:
            QMessageBox.warning(self, "Помилка", "Заповніть ім'я та прізвище")
            return

        import shutil
        from datetime import datetime
        import os

        saved_photo = None
        if self.photo_path:
            ext = os.path.splitext(self.photo_path)[1]
            saved_photo = f"photo_{int(datetime.now().timestamp())}{ext}"
            dest_path = os.path.join(auth.BASE_DIR, 'data', 'documents', saved_photo)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy(self.photo_path, dest_path)

        with sqlite3.connect(auth.DB_PATH) as conn:
            if self.student_id:
                if saved_photo:
                    conn.execute(
                        "UPDATE STUDENTS SET first_name=?, last_name=?, class_id=?, birth_date=?, photo_path=? WHERE id=?",
                        (fname, lname, class_id, bdate, saved_photo, self.student_id))
                else:
                    conn.execute("UPDATE STUDENTS SET first_name=?, last_name=?, class_id=?, birth_date=? WHERE id=?",
                                 (fname, lname, class_id, bdate, self.student_id))
            else:
                conn.execute(
                    "INSERT INTO STUDENTS (first_name, last_name, class_id, birth_date, photo_path, is_active) VALUES (?, ?, ?, ?, ?, 1)",
                    (fname, lname, class_id, bdate, saved_photo))
            conn.commit()
        self.accept()


# --- Головна панель управління учнями ---
class StudentsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # Верхнє меню довідників
        dir_layout = QHBoxLayout()
        self.add_year_btn = QPushButton("Додати навч. рік")
        self.add_year_btn.clicked.connect(self.add_academic_year)
        self.add_class_btn = QPushButton("Додати клас")
        self.add_class_btn.clicked.connect(self.add_class)
        dir_layout.addWidget(self.add_year_btn)
        dir_layout.addWidget(self.add_class_btn)
        dir_layout.addStretch()
        self.layout.addLayout(dir_layout)

        # Фільтри пошуку
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Пошук за прізвищем...")
        self.search_input.textChanged.connect(self.load_students)

        self.class_filter = QComboBox()
        self.class_filter.currentIndexChanged.connect(self.load_students)

        self.active_check = QCheckBox("Показувати деактивованих")
        self.active_check.stateChanged.connect(self.load_students)

        filter_layout.addWidget(QLabel("Пошук:"))
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(QLabel("Клас:"))
        filter_layout.addWidget(self.class_filter)
        filter_layout.addWidget(self.active_check)
        self.layout.addLayout(filter_layout)

        # Таблиця
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Прізвище", "Ім'я", "Клас", "Статус"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.layout.addWidget(self.table)

        # Кнопки управління учнями
        btn_layout = QHBoxLayout()
        self.add_student_btn = QPushButton("Додати учня")
        self.add_student_btn.clicked.connect(self.add_student)
        self.edit_student_btn = QPushButton("Редагувати учня")
        self.edit_student_btn.clicked.connect(self.edit_student)
        self.deactivate_btn = QPushButton("Деактивувати/Активувати")
        self.deactivate_btn.clicked.connect(self.toggle_status)

        btn_layout.addWidget(self.add_student_btn)
        btn_layout.addWidget(self.edit_student_btn)
        btn_layout.addWidget(self.deactivate_btn)
        self.layout.addLayout(btn_layout)

        self.update_class_filter()
        self.load_students()

    def add_academic_year(self):
        dialog = AcademicYearDialog(self)
        if dialog.exec_():
            QMessageBox.information(self, "Успіх", "Навчальний рік додано!")

    def add_class(self):
        dialog = ClassDialog(self)
        if dialog.exec_():
            self.update_class_filter()

    def update_class_filter(self):
        self.class_filter.clear()
        self.class_filter.addItem("Всі класи", None)
        with sqlite3.connect(auth.DB_PATH) as conn:
            for row in conn.execute("SELECT id, name FROM CLASSES"):
                self.class_filter.addItem(row[1], row[0])

    def load_students(self):
        search = f"%{self.search_input.text()}%"
        class_id = self.class_filter.currentData()
        show_inactive = self.active_check.isChecked()

        query = """
            SELECT s.id, s.last_name, s.first_name, c.name, s.is_active 
            FROM STUDENTS s
            LEFT JOIN CLASSES c ON s.class_id = c.id
            WHERE s.last_name LIKE ?
        """
        params = [search]

        if class_id:
            query += " AND s.class_id = ?"
            params.append(class_id)

        if not show_inactive:
            query += " AND s.is_active = 1"

        query += " ORDER BY s.last_name, s.first_name"

        with sqlite3.connect(auth.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            rows = cur.fetchall()

        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.table.setItem(i, 1, QTableWidgetItem(row[1]))
            self.table.setItem(i, 2, QTableWidgetItem(row[2]))
            self.table.setItem(i, 3, QTableWidgetItem(row[3] if row[3] else "—"))
            status = "Активний" if row[4] else "Деактивований"
            self.table.setItem(i, 4, QTableWidgetItem(status))

    def add_student(self):
        dialog = StudentDialog(parent=self)
        if dialog.exec_():
            self.load_students()

    def edit_student(self):
        row = self.table.currentRow()
        if row < 0: return
        student_id = int(self.table.item(row, 0).text())
        dialog = StudentDialog(student_id, parent=self)
        if dialog.exec_():
            self.load_students()

    def toggle_status(self):
        row = self.table.currentRow()
        if row < 0: return
        student_id = int(self.table.item(row, 0).text())
        current_status = self.table.item(row, 4).text()
        new_status = 0 if current_status == "Активний" else 1

        with sqlite3.connect(auth.DB_PATH) as conn:
            conn.execute("UPDATE STUDENTS SET is_active = ? WHERE id = ?", (new_status, student_id))
            conn.commit()
        self.load_students()