import sqlite3

connect = sqlite3.connect("habits_bot.db")
cursor = connect.cursor()

cursor.executescript("""
    /* Таблица для хранения зарегистрированных пользователей */
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    );

    /* Таблица для хранения дел */
    CREATE TABLE IF NOT EXISTS todos (
        todo_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        todo TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    );

    /* Таблица напоминаний */
    CREATE TABLE IF NOT EXISTS reminders (
        user_id INTEGER,
        reminder_time TEXT NOT NULL,
        todo TEXT NOT NULL,
        reminded_once INTEGER DEFAULT 0,
        PRIMARY KEY (user_id, todo),
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    );

    /* Таблица сессий */
    CREATE TABLE IF NOT EXISTS sessions (
        user_id_telegram INTEGER PRIMARY KEY,
        user_id INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    );
""")

connect.commit()


def load_logged_in():
    """Функция, которая загружает данные об авторизованных пользователях из таблицы sessions"""
    cursor.execute("SELECT user_id_telegram, user_id FROM sessions")
    return {row[0]: row[1] for row in cursor.fetchall()}

logged_in = load_logged_in()

def is_logged_in(user_id: int) -> bool:
    """Функция, которая проверяет, авторизован ли пользователь"""
    return user_id in logged_in