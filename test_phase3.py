import sqlite3
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))
from auth import DB_PATH


def run_extended_tests():
    print("--- Запуск розширеного тест-плану: Фаза 3 ---\n")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        # Підготовка тестових даних
        cur.execute(
            "INSERT INTO ACADEMIC_YEARS (name, start_date, end_date) VALUES ('TEST_2026', '2026-09-01', '2027-05-31')")
        year_id = cur.lastrowid

        # TC-3.1: Додавання нового класу
        cur.execute("INSERT INTO CLASSES (name, grade_number, academic_year_id) VALUES ('11-Б', 11, ?)", (year_id,))
        class_id = cur.lastrowid
        print("✅ TC-3.1 PASS: Клас 11-Б успішно створено та прив'язано до навчального року.")

        # TC-3.2: Додавання учня до класу
        cur.execute(
            "INSERT INTO STUDENTS (first_name, last_name, class_id, is_active) VALUES ('Петро', 'Коваленко', ?, 1)",
            (class_id,))
        student1_id = cur.lastrowid
        cur.execute(
            "INSERT INTO STUDENTS (first_name, last_name, class_id, is_active) VALUES ('Ганна', 'Шевченко', ?, 1)",
            (class_id,))
        student2_id = cur.lastrowid
        cur.execute("SELECT COUNT(*) FROM STUDENTS WHERE class_id = ?", (class_id,))
        if cur.fetchone()[0] == 2:
            print("✅ TC-3.2 PASS: Учні коректно додані та відображаються у списку класу.")

        # TC-3.3: Редагування даних учня
        cur.execute("UPDATE STUDENTS SET first_name = 'Петрик', last_name = 'Коваль' WHERE id = ?", (student1_id,))
        cur.execute("SELECT first_name, last_name FROM STUDENTS WHERE id = ?", (student1_id,))
        updated_name = cur.fetchone()
        if updated_name == ('Петрик', 'Коваль'):
            print("✅ TC-3.3 PASS: Дані учня успішно відредаговано в БД.")

        # TC-3.4: Пошук за прізвищем (SQL LIKE)
        search_term = "%Шевч%"
        cur.execute("SELECT last_name FROM STUDENTS WHERE last_name LIKE ?", (search_term,))
        search_result = cur.fetchall()
        if len(search_result) == 1 and search_result[0][0] == 'Шевченко':
            print("✅ TC-3.4 PASS: Пошук за фрагментом прізвища працює коректно.")

        # TC-3.5: Деактивація учня
        cur.execute("UPDATE STUDENTS SET is_active = 0 WHERE id = ?", (student2_id,))
        cur.execute("SELECT COUNT(*) FROM STUDENTS WHERE class_id = ? AND is_active = 1", (class_id,))
        active_count = cur.fetchone()[0]
        if active_count == 1:
            print("✅ TC-3.5 PASS: Деактивований учень зник зі списку активних, але запис у БД збережено.")

        # TC-3.6: Порожній список класу
        cur.execute("INSERT INTO CLASSES (name, grade_number, academic_year_id) VALUES ('12-В', 12, ?)", (year_id,))
        empty_class_id = cur.lastrowid
        cur.execute("SELECT * FROM STUDENTS WHERE class_id = ?", (empty_class_id,))
        empty_result = cur.fetchall()
        if len(empty_result) == 0:
            print("✅ TC-3.6 PASS: Запит для порожнього класу повертає порожній список без помилок (готовність для UI).")

        # --- ДОДАТКОВІ ТЕСТИ ---

        # TC-3.7: Коректність сортування учнів
        cur.execute(
            "INSERT INTO STUDENTS (first_name, last_name, class_id, is_active) VALUES ('Андрій', 'Авраменко', ?, 1)",
            (class_id,))
        cur.execute("SELECT last_name FROM STUDENTS WHERE class_id = ? ORDER BY last_name ASC, first_name ASC",
                    (class_id,))
        sorted_names = [row[0] for row in cur.fetchall()]
        if sorted_names == ['Авраменко', 'Коваль', 'Шевченко']:  # Шевченко деактивована, але в загальному списку є
            print("✅ TC-3.7 (Бонус) PASS: Модуль сортування даних таблиці за прізвищем працює ідеально.")

        # TC-3.8: Захист від втрати даних (Foreign Key Constraint)
        try:
            # Спроба видалити клас, у якому є учні
            cur.execute("DELETE FROM CLASSES WHERE id = ?", (class_id,))
        except sqlite3.IntegrityError:
            print("❌ TC-3.8 FAIL: Помилка налаштування зовнішніх ключів.")
        else:
            # Перевіряємо, чи спрацював ON DELETE SET NULL (як ми налаштували в міграціях)
            cur.execute("SELECT class_id FROM STUDENTS WHERE id = ?", (student1_id,))
            if cur.fetchone()[0] is None:
                print("✅ TC-3.8 (Бонус) PASS: При видаленні класу учні не видаляються, їх class_id стає NULL.")

    except Exception as e:
        print(f"❌ Помилка під час тестування: {e}")

    finally:
        # Відкочуємо транзакцію, щоб тестові дані не засмічували робочу БД
        conn.rollback()
        conn.close()

    print("\n⚠️ Вказівки для перевірки GUI:")
    print(
        "- TC-3.4 (Пошук у реальному часі): Відкрийте програму, почніть вводити літери в поле пошуку. Таблиця має миттєво скорочуватись.")
    print(
        "- TC-3.6 (Порожній клас): Оберіть у фільтрі клас, в якому немає учнів. Переконайтесь, що програма не 'вилітає', а таблиця просто стає порожньою.")


if __name__ == "__main__":
    run_extended_tests()