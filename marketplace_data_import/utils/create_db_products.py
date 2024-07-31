import sqlite3

def create_products_table():
    conn = sqlite3.connect('megamarket/megamarket.db')
    cursor = conn.cursor()

    # Удаление старой таблицы, если она существует
    cursor.execute('DROP TABLE IF EXISTS products')

    # Создание новой таблицы продуктов
    cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            load_date TEXT,
            category TEXT,
            name TEXT,
            merchant TEXT,
            original_price REAL,
            discounted_price REAL,
            discount_percent REAL,
            bonus_percent REAL,
            bonus_amount REAL,
            final_price REAL,
            rating REAL,
            reviews_count INTEGER
        )
    ''')

    conn.commit()
    conn.close()
    print("Таблица 'products' успешно создана.")

if __name__ == "__main__":
    create_products_table()
