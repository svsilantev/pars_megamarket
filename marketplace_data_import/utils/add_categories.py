import sqlite3

# Открываем файл с ссылками
with open('full_catalog_links.txt', 'r', encoding='utf-8') as file:
    links = file.readlines()

# Открываем или создаем базу данных
conn = sqlite3.connect('megamarket.db')
cursor = conn.cursor()

# Создаем таблицу categories, если она не существует
cursor.execute('''
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_url TEXT NOT NULL,
    user_name TEXT NOT NULL
)
''')

# Добавляем ссылки в таблицу categories
for link in links:
    cursor.execute('''
    INSERT INTO categories (category_url, user_name)
    VALUES (?, ?)
    ''', (link.strip(), 'user1'))

# Сохраняем изменения и закрываем соединение с базой данных
conn.commit()
conn.close()

