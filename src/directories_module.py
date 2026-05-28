import sqlite3
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QFormLayout, QLineEdit,
                             QMessageBox, QDialog, QHeaderView, QTabWidget, QInputDialog)
import auth

# --- Діалог Додавання/Редагування Вчителя залишається без змін ---
class TeacherDialog(QDialog):
    def __init__(self, teacher_id=None, parent=None):
        super().__init__(parent)
        self.teacher_id = teacher_id
        self.setWindowTitle("Картка вчителя")
        self.setMinimumWidth(300)
        self.layout = QFormLayout(self)

        self.lname_input = QLineEdit()
        self.fname_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()

        self.layout.addRow("Прізвище:", self.lname_input)
        self.layout.addRow("Ім'я:", self.fname_input)
        self.layout.addRow("Email:", self.email_input)
        self.layout.addRow("Телефон:", self.phone_input)

        self.save_btn = QPushButton("Зберегти")
        self.save_btn.clicked.connect(self.save_data)
        self.layout.addRow(self.save_btn)

        if self.teacher_id:
            self.load_data()

    def load_data(self):
        with sqlite3.connect(auth.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT last_name, first_name, email, phone FROM TEACHERS WHERE id=?", (self.teacher_id,))
            row = cur.fetchone()
            if row:
                self.lname_input.setText(row[0])
                self.fname_input.setText(row[1])
                self.email_input.setText(row[2] if row[2] else "")
                self.phone_input.setText(row[3] if row[3] else "")

    def save_data(self):
        lname = self.lname_input.text().strip()
        fname = self.fname_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()

        if not lname or not fname:
            QMessageBox.warning(self, "Помилка", "Заповніть обов'язкові поля: Прізвище та Ім'я.")
            return

        with sqlite3.connect(auth.DB_PATH) as conn:
            if self.teacher_id:
                conn.execute("UPDATE TEACHERS SET last_name=?, first_name=?, email=?, phone=? WHERE id=?",
                             (lname, fname, email, phone, self.teacher_id))
            else:
                conn.execute("INSERT INTO TEACHERS (last_name, first_name, email, phone) VALUES (?, ?, ?, ?)",
                             (lname, fname, email, phone))
            conn.commit()
        self.accept()

# --- Головна панель Довідників ---
class DirectoriesPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.init_teachers_tab()
        self.init_subjects_tab()

    def init_teachers_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        btn_layout = QHBoxLayout()
        self.add_teacher_btn = QPushButton("Додати вчителя")
        self.add_teacher_btn.clicked.connect(self.add_teacher)
        self.edit_teacher_btn = QPushButton("Редагувати")
        self.edit_teacher_btn.clicked.connect(self.edit_teacher)
        self.del_teacher_btn = QPushButton("Видалити")
        self.del_teacher_btn.clicked.connect(self.delete_teacher)

        btn_layout.addWidget(self.add_teacher_btn)
        btn_layout.addWidget(self.edit_teacher_btn)
        btn_layout.addWidget(self.del_teacher_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.teachers_table = QTableWidget()
        self.teachers_table.setColumnCount(5)
        self.teachers_table.setHorizontalHeaderLabels(["ID", "Прізвище", "Ім'я", "Email", "Телефон"])
        self.teachers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.teachers_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.teachers_table)

        self.tabs.addTab(tab, "Вчителі / Керівники")
        self.load_teachers()

    def init_subjects_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        btn_layout = QHBoxLayout()
        self.add_subject_btn = QPushButton("Додати предмет")
        self.add_subject_btn.clicked.connect(self.add_subject)
        self.edit_subject_btn = QPushButton("Редагувати")
        self.edit_subject_btn.clicked.connect(self.edit_subject)
        self.del_subject_btn = QPushButton("Видалити")
        self.del_subject_btn.clicked.connect(self.delete_subject)

        btn_layout.addWidget(self.add_subject_btn)
        btn_layout.addWidget(self.edit_subject_btn)
        btn_layout.addWidget(self.del_subject_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        self.subjects_table = QTableWidget()
        self.subjects_table.setColumnCount(2)
        self.subjects_table.setHorizontalHeaderLabels(["ID", "Назва предмету"])
        self.subjects_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.subjects_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.subjects_table)

        self.tabs.addTab(tab, "Предмети")
        self.load_subjects()

    def load_teachers(self):
        with sqlite3.connect(auth.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, last_name, first_name, email, phone FROM TEACHERS ORDER BY last_name")
            rows = cur.fetchall()

        self.teachers_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j in range(5):
                self.teachers_table.setItem(i, j, QTableWidgetItem(str(row[j]) if row[j] else ""))

    def add_teacher(self):
        if TeacherDialog(parent=self).exec_():
            self.load_teachers()

    def edit_teacher(self):
        row = self.teachers_table.currentRow()
        if row < 0: return
        teacher_id = int(self.teachers_table.item(row, 0).text())
        if TeacherDialog(teacher_id, parent=self).exec_():
            self.load_teachers()

    def delete_teacher(self):
        row = self.teachers_table.currentRow()
        if row < 0: return
        t_id = self.teachers_table.item(row, 0).text()
        name = self.teachers_table.item(row, 1).text()
        reply = QMessageBox.question(self, "Підтвердження", f"Видалити вчителя {name}?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            with sqlite3.connect(auth.DB_PATH) as conn:
                conn.execute("DELETE FROM TEACHERS WHERE id=?", (t_id,))
                conn.commit()
            self.load_teachers()

    def load_subjects(self):
        with sqlite3.connect(auth.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM SUBJECTS ORDER BY name")
            rows = cur.fetchall()

        self.subjects_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.subjects_table.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.subjects_table.setItem(i, 1, QTableWidgetItem(row[1]))

    def add_subject(self):
        name, ok = QInputDialog.getText(self, "Новий предмет", "Введіть назву предмету:")
        if ok and name.strip():
            with sqlite3.connect(auth.DB_PATH) as conn:
                conn.execute("INSERT INTO SUBJECTS (name) VALUES (?)", (name.strip(),))
                conn.commit()
            self.load_subjects()

    def edit_subject(self):
        row = self.subjects_table.currentRow()
        if row < 0: return
        s_id = self.subjects_table.item(row, 0).text()
        current_name = self.subjects_table.item(row, 1).text()
        name, ok = QInputDialog.getText(self, "Редагувати предмет", "Назва предмету:", QLineEdit.Normal, current_name)
        if ok and name.strip():
            with sqlite3.connect(auth.DB_PATH) as conn:
                conn.execute("UPDATE SUBJECTS SET name=? WHERE id=?", (name.strip(), s_id))
                conn.commit()
            self.load_subjects()

    def delete_subject(self):
        row = self.subjects_table.currentRow()
        if row < 0: return
        s_id = self.subjects_table.item(row, 0).text()
        name = self.subjects_table.item(row, 1).text()
        reply = QMessageBox.question(self, "Підтвердження", f"Видалити предмет {name}?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            with sqlite3.connect(auth.DB_PATH) as conn:
                conn.execute("DELETE FROM SUBJECTS WHERE id=?", (s_id,))
                conn.commit()
            self.load_subjects()