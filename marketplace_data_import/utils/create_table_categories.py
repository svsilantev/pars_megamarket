import sqlite3

def create_categories_table():
    conn = sqlite3.connect('megamarket/megamarket.db')
    cursor = conn.cursor()

    # Удаление старой таблицы, если она существует
    cursor.execute('DROP TABLE IF EXISTS categories')

    # Создание новой таблицы категорий
    cursor.execute('''
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT,
            category_url TEXT,
            category_name TEXT,
            pages_loaded INTEGER,
            load_time REAL,
            load_date TEXT,
            load_time_start TEXT,
            load_time_end TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("Таблица категорий успешно создана.")

create_categories_table()
