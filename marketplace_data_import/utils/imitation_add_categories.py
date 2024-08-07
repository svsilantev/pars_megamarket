import sqlite3

# Подключение к базе данных
conn = sqlite3.connect('megamarket.db')
cursor = conn.cursor()

# Создание списка новых строк
new_rows = [
    ('user1', 'https://megamarket.ru/catalog/noutbuki/'),
    ('user1', 'https://megamarket.ru/catalog/noutbuki/'),
    ('user1', 'https://megamarket.ru/catalog/noutbuki/'),
    ('user1', 'https://megamarket.ru/catalog/noutbuki/'),
    ('user1', 'https://megamarket.ru/catalog/noutbuki/')
]

# SQL запрос для вставки новых строк
insert_query = """
INSERT INTO categories (user_name, category_url, category_name, pages_loaded, load_time, load_date, load_time_start, load_time_end) 
VALUES (?, ?, NULL, NULL, NULL, NULL, NULL, NULL)
"""

# Выполнение вставки новых строк
cursor.executemany(insert_query, new_rows)

# Сохранение изменений
conn.commit()

# Закрытие соединения с базой данных
conn.close()
