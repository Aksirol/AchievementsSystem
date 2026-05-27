import sqlite3
import os


def create_database():
    # Перевіряємо, чи існує папка data, якщо ні - створюємо
    os.makedirs('data/documents', exist_ok=True)
    db_path = os.path.join('data', 'achievements.db')

    # Підключення до БД (файл створиться автоматично, якщо не існує)
    conn = sqlite3.connect(db_path)

    # Вмикаємо підтримку зовнішніх ключів у SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # Створення таблиць згідно з ER-діаграмою
    tables = [
        """
        CREATE TABLE IF NOT EXISTS USERS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS ACADEMIC_YEARS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS TEACHERS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT,
            phone TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS CLASSES (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            grade_number INTEGER NOT NULL,
            academic_year_id INTEGER,
            curator_id INTEGER,
            FOREIGN KEY(academic_year_id) REFERENCES ACADEMIC_YEARS(id) ON DELETE SET NULL,
            FOREIGN KEY(curator_id) REFERENCES TEACHERS(id) ON DELETE SET NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS STUDENTS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            birth_date DATE,
            class_id INTEGER,
            photo_path TEXT,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY(class_id) REFERENCES CLASSES(id) ON DELETE SET NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS SUBJECTS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS EVENT_TYPES (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            description TEXT
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS EVENTS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            event_type_id INTEGER,
            subject_id INTEGER,
            level TEXT,
            event_date DATE,
            organizer TEXT,
            location TEXT,
            academic_year_id INTEGER,
            FOREIGN KEY(event_type_id) REFERENCES EVENT_TYPES(id) ON DELETE SET NULL,
            FOREIGN KEY(subject_id) REFERENCES SUBJECTS(id) ON DELETE SET NULL,
            FOREIGN KEY(academic_year_id) REFERENCES ACADEMIC_YEARS(id) ON DELETE SET NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS ACHIEVEMENTS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            event_id INTEGER NOT NULL,
            confirmed_by INTEGER,
            result TEXT,
            place INTEGER,
            diploma_type TEXT,
            document_path TEXT,
            note TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES STUDENTS(id) ON DELETE CASCADE,
            FOREIGN KEY(event_id) REFERENCES EVENTS(id) ON DELETE CASCADE,
            FOREIGN KEY(confirmed_by) REFERENCES USERS(id) ON DELETE SET NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS CLUBS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            supervisor_id INTEGER,
            schedule TEXT,
            FOREIGN KEY(supervisor_id) REFERENCES TEACHERS(id) ON DELETE SET NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS CLUB_MEMBERS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            club_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            joined_at DATE,
            left_at DATE,
            is_active BOOLEAN DEFAULT 1,
            FOREIGN KEY(club_id) REFERENCES CLUBS(id) ON DELETE CASCADE,
            FOREIGN KEY(student_id) REFERENCES STUDENTS(id) ON DELETE CASCADE
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS PORTFOLIO_EXPORTS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY(student_id) REFERENCES STUDENTS(id) ON DELETE CASCADE,
            FOREIGN KEY(created_by) REFERENCES USERS(id) ON DELETE SET NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS BACKUP_LOG (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            status TEXT,
            FOREIGN KEY(created_by) REFERENCES USERS(id) ON DELETE SET NULL
        );
        """
    ]

    for table_sql in tables:
        cursor.execute(table_sql)

    conn.commit()
    conn.close()
    print(f"База даних успішно створена за шляхом: {os.path.abspath(db_path)}")
    print(f"Папка для документів готова: {os.path.abspath('data/documents')}")


if __name__ == '__main__':
    create_database()