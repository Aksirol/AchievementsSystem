import sqlite3
import os
import shutil
import zipfile
import sys
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QFileDialog,
                             QMessageBox, QHeaderView, QApplication)
from PyQt5.QtCore import QProcess
import auth


class BackupPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)

        # Кнопки управління
        btn_layout = QHBoxLayout()
        self.backup_btn = QPushButton("Створити резервну копію")
        self.backup_btn.clicked.connect(self.create_backup)
        self.restore_btn = QPushButton("Відновити з архіву")
        self.restore_btn.clicked.connect(self.restore_backup)

        btn_layout.addWidget(self.backup_btn)
        btn_layout.addWidget(self.restore_btn)
        self.layout.addLayout(btn_layout)

        # Журнал операцій (Таблиця)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Дата", "Користувач", "Операція / Файл"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

        self.load_log()

    def load_log(self):
        query = """
            SELECT b.id, b.created_at, u.username, b.status || ': ' || b.file_path 
            FROM BACKUP_LOG b
            LEFT JOIN USERS u ON b.created_by = u.id
            ORDER BY b.created_at DESC
        """
        with sqlite3.connect(auth.DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute(query)
            rows = cur.fetchall()

        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.table.setItem(i, 1, QTableWidgetItem(row[1]))
            self.table.setItem(i, 2, QTableWidgetItem(row[2] if row[2] else "Система"))
            self.table.setItem(i, 3, QTableWidgetItem(row[3]))

    def log_operation(self, file_path, status):
        user_id = auth.Session.current_user['id'] if auth.Session.current_user else None
        with sqlite3.connect(auth.DB_PATH) as conn:
            conn.execute("INSERT INTO BACKUP_LOG (file_path, created_by, status) VALUES (?, ?, ?)",
                         (os.path.basename(file_path), user_id, status))
            conn.commit()
        self.load_log()

    def create_backup(self):
        date_str = datetime.now().strftime('%Y-%m-%d')
        default_name = f"achievements_backup_{date_str}.zip"

        # Вибір місця збереження (TC-7.1, TC-7.3)
        path, _ = QFileDialog.getSaveFileName(self, "Зберегти резервну копію", default_name, "ZIP Archives (*.zip)")
        if not path: return

        try:
            # Зберігаємо вміст папки data у zip-архів
            base_name = path.replace('.zip', '')
            # base_dir='data' зберігає структуру папки в архіві
            shutil.make_archive(base_name, 'zip', root_dir='.', base_dir='data')

            self.log_operation(path, "Створення копії")
            QMessageBox.information(self, "Успіх", f"Резервну копію успішно створено:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Помилка створення бекапу: {e}")

    def restore_backup(self):
        # Вибір архіву (TC-7.2)
        path, _ = QFileDialog.getOpenFileName(self, "Обрати резервну копію", "", "ZIP Archives (*.zip)")
        if not path: return

        reply = QMessageBox.warning(self, "Увага",
                                    "Відновлення перезапише поточну базу даних та всі документи!\nПрограма буде перезапущена. Продовжити?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                # Розпакування архіву (він містить папку data)
                with zipfile.ZipFile(path, 'r') as zip_ref:
                    zip_ref.extractall('.')  # Розпаковуємо в корінь проекту

                # Запис у відновлену БД
                self.log_operation(path, "Відновлення з копії")

                QMessageBox.information(self, "Успіх", "Відновлення успішне. Програма зараз перезапуститься.")

                # Перезапуск програми
                QApplication.quit()
                QProcess.startDetached(sys.executable, sys.argv)

            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Помилка відновлення: {e}")