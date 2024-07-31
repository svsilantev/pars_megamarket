import sqlite3

def create_temp_table():
    conn = sqlite3.connect('megamarket/megamarket.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS temp_products (
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

if __name__ == "__main__":
    create_temp_table()
    print("Временная таблица создана успешно.")
