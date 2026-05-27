import sqlite3
import os
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QComboBox, QFileDialog,
                             QMessageBox, QLabel, QHeaderView, QTabWidget)
from PyQt5.QtCore import Qt
import auth

# Імпорти для ReportLab
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Реєстрація кириличного шрифту (переконайтеся, що файл fonts/arial.ttf існує)
FONT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'fonts', 'arial.ttf'))
try:
    pdfmetrics.registerFont(TTFont('Arial', FONT_PATH))
    BASE_FONT = 'Arial'
except Exception:
    print("Увага: Шрифт arial.ttf не знайдено. Кирилиця може не відображатись у PDF.")
    BASE_FONT = 'Helvetica'


class ReportsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.init_class_tab()
        self.init_student_tab()

    def init_class_tab(self):
        """Вкладка 1: Рейтинг та Звіт класу"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Фільтри
        filter_layout = QHBoxLayout()
        self.rep_year_combo = QComboBox()
        self.rep_class_combo = QComboBox()
        self.rep_class_combo.currentIndexChanged.connect(self.load_class_ranking)

        filter_layout.addWidget(QLabel("Навчальний рік:"))
        filter_layout.addWidget(self.rep_year_combo)
        filter_layout.addWidget(QLabel("Клас:"))
        filter_layout.addWidget(self.rep_class_combo)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Таблиця рейтингу
        self.ranking_table = QTableWidget()
        self.ranking_table.setColumnCount(3)
        self.ranking_table.setHorizontalHeaderLabels(["Учень", "Кількість досягнень", "Бали (Рейтинг)"])
        self.ranking_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.ranking_table)

        # Кнопка експорту
        self.export_class_btn = QPushButton("Експортувати звіт класу (PDF)")
        self.export_class_btn.clicked.connect(self.export_class_report)
        layout.addWidget(self.export_class_btn)

        self.tabs.addTab(tab, "Звіт та Рейтинг класу")
        self.load_filters()

    def init_student_tab(self):
        """Вкладка 2: Характеристика учня"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        filter_layout = QHBoxLayout()
        self.char_class_combo = QComboBox()
        self.char_class_combo.currentIndexChanged.connect(self.load_students_for_char)
        self.char_student_combo = QComboBox()

        filter_layout.addWidget(QLabel("Клас:"))
        filter_layout.addWidget(self.char_class_combo)
        filter_layout.addWidget(QLabel("Учень:"))
        filter_layout.addWidget(self.char_student_combo)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        self.generate_char_btn = QPushButton("Згенерувати характеристику (PDF)")
        self.generate_char_btn.clicked.connect(self.generate_characteristic)
        layout.addWidget(self.generate_char_btn)
        layout.addStretch()

        self.tabs.addTab(tab, "Генерація характеристики")

    def load_filters(self):
        with sqlite3.connect(auth.DB_PATH) as conn:
            self.rep_class_combo.clear()
            self.char_class_combo.clear()
            for row in conn.execute("SELECT id, name FROM CLASSES"):
                self.rep_class_combo.addItem(row[1], row[0])
                self.char_class_combo.addItem(row[1], row[0])

            self.rep_year_combo.clear()
            for row in conn.execute("SELECT id, name FROM ACADEMIC_YEARS"):
                self.rep_year_combo.addItem(row[1], row[0])

    def load_students_for_char(self):
        class_id = self.char_class_combo.currentData()
        self.char_student_combo.clear()
        if not class_id: return
        with sqlite3.connect(auth.DB_PATH) as conn:
            for row in conn.execute("SELECT id, last_name || ' ' || first_name FROM STUDENTS WHERE class_id = ?",
                                    (class_id,)):
                self.char_student_combo.addItem(row[1], row[0])

    def load_class_ranking(self):
        class_id = self.rep_class_combo.currentData()
        if not class_id: return

        # Обчислення рейтингу (кількість досягнень + умовні бали за місця)
        query = """
            SELECT s.last_name || ' ' || s.first_name,
                   COUNT(a.id) as ach_count,
                   SUM(CASE WHEN a.place = 1 THEN 3 WHEN a.place = 2 THEN 2 WHEN a.place = 3 THEN 1 ELSE 0.5 END) as points
            FROM STUDENTS s
            LEFT JOIN ACHIEVEMENTS a ON s.id = a.student_id
            WHERE s.class_id = ?
            GROUP BY s.id
            ORDER BY points DESC, ach_count DESC
        """
        with sqlite3.connect(auth.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute(query, (class_id,))
            rows = cur.fetchall()

        self.ranking_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.ranking_table.setItem(i, 0, QTableWidgetItem(row[0]))
            self.ranking_table.setItem(i, 1, QTableWidgetItem(str(row[1])))
            self.ranking_table.setItem(i, 2, QTableWidgetItem(str(row[2] if row[2] else 0)))

    def export_class_report(self):
        class_name = self.rep_class_combo.currentText()
        if not class_name: return

        path, _ = QFileDialog.getSaveFileName(self, "Зберегти звіт", f"Звіт_класу_{class_name}.pdf", "PDF (*.pdf)")
        if not path: return

        doc = SimpleDocTemplate(path, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('TitleCyrillic', fontName=BASE_FONT, fontSize=16, alignment=1, spaceAfter=20)

        elements.append(Paragraph(f"Зведений звіт досягнень класу: {class_name}", title_style))

        data = [["Учень", "Кількість досягнень", "Бали"]]
        for row in range(self.ranking_table.rowCount()):
            data.append([
                self.ranking_table.item(row, 0).text(),
                self.ranking_table.item(row, 1).text(),
                self.ranking_table.item(row, 2).text()
            ])

        table = Table(data, colWidths=[250, 150, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (-1, -1), BASE_FONT),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

        try:
            doc.build(elements)
            QMessageBox.information(self, "Успіх", f"Звіт збережено: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Помилка створення PDF: {e}")

    def generate_characteristic(self):
        student_id = self.char_student_combo.currentData()
        student_name = self.char_student_combo.currentText()
        if not student_id: return

        path, _ = QFileDialog.getSaveFileName(self, "Зберегти характеристику",
                                              f"Характеристика_{student_name.replace(' ', '_')}.pdf", "PDF (*.pdf)")
        if not path: return

        # Збір даних для характеристики
        with sqlite3.connect(auth.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT c.name FROM CLUBS c JOIN CLUB_MEMBERS cm ON c.id = cm.club_id WHERE cm.student_id = ?",
                        (student_id,))
            clubs = [row[0] for row in cur.fetchall()]

            cur.execute(
                "SELECT e.name, a.place, e.level FROM ACHIEVEMENTS a JOIN EVENTS e ON a.event_id = e.id WHERE a.student_id = ?",
                (student_id,))
            achievements = cur.fetchall()

            # Запис в історію експорту (PORTFOLIO_EXPORTS)
            user_id = auth.Session.current_user['id']
            cur.execute("INSERT INTO PORTFOLIO_EXPORTS (student_id, file_path, created_by) VALUES (?, ?, ?)",
                        (student_id, path, user_id))
            conn.commit()

        # Формування PDF
        doc = SimpleDocTemplate(path, pagesize=A4)
        styles = getSampleStyleSheet()
        normal_style = ParagraphStyle('NormalCyrillic', fontName=BASE_FONT, fontSize=12, spaceAfter=10)
        title_style = ParagraphStyle('TitleCyrillic', fontName=BASE_FONT, fontSize=16, alignment=1, spaceAfter=20)

        elements = [Paragraph(f"ХАРАКТЕРИСТИКА", title_style)]

        text = f"Учень/учениця <b>{student_name}</b> має високий рівень позакласної активності. "
        if clubs:
            text += f"Бере активну участь у роботі таких гуртків та секцій: {', '.join(clubs)}. "
        else:
            text += "У гуртках на даний час не задіяна(ий). "

        elements.append(Paragraph(text, normal_style))
        elements.append(Spacer(1, 10))

        if achievements:
            elements.append(Paragraph("<b>Основні досягнення:</b>", normal_style))
            ach_data = [["Захід", "Рівень", "Місце"]]
            for ach in achievements:
                place_str = str(ach[1]) if ach[1] else "Учасник"
                ach_data.append([ach[0], ach[2], place_str])

            table = Table(ach_data, colWidths=[250, 150, 100])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('FONTNAME', (0, 0), (-1, -1), BASE_FONT),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("Зареєстрованих досягнень у заходах поки немає.", normal_style))

        elements.append(Spacer(1, 30))
        elements.append(Paragraph(f"Дата формування: {datetime.now().strftime('%Y-%m-%d')}", normal_style))

        try:
            doc.build(elements)
            QMessageBox.information(self, "Успіх", f"Характеристику згенеровано: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Помилка створення PDF: {e}")