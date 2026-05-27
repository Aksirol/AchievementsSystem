import sqlite3
import bcrypt
import os
import sys

# Визначаємо корінь проекту залежно від того, як запущена програма
if getattr(sys, 'frozen', False):
    # Якщо запущено як зібраний .exe файл
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Якщо запущено як звичайний Python-скрипт в IDE
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Абсолютний шлях до бази даних
DB_PATH = os.path.join(BASE_DIR, 'data', 'achievements.db')

# Створюємо папку data/documents поруч з .exe (якщо її раптом немає)
os.makedirs(os.path.join(BASE_DIR, 'data', 'documents'), exist_ok=True)

class Session:
    """Клас для зберігання даних поточного авторизованого користувача"""
    current_user = None

def hash_password(password: str) -> str:
    """Хешує пароль за допомогою bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Перевіряє відповідність пароля хешу."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_default_admin():
    """Створює адміністратора за замовчуванням, якщо користувачів ще немає."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM USERS")
    if cursor.fetchone()[0] == 0:
        admin_pass = hash_password("admin123")
        cursor.execute(
            "INSERT INTO USERS (username, password_hash, role) VALUES (?, ?, ?)",
            ("admin", admin_pass, "Адміністратор")
        )
        conn.commit()
    conn.close()


def authenticate(username, password):
    """Перевіряє облікові дані та повертає статус авторизації."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role FROM USERS WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return "NOT_FOUND"  # Для TC-2.3

    if verify_password(password, user['password_hash']):
        Session.current_user = dict(user)
        return "SUCCESS"  # Для TC-2.1

    return "WRONG_PASSWORD"  # Для TC-2.2

def logout():
    """Очищає поточну сесію."""
    Session.current_user = None