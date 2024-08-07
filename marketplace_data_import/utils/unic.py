import sqlite3

# Подключение к базе данных
conn = sqlite3.connect('megamarket.db')
cursor = conn.cursor()

# Запрос для получения неуникальных ссылок
cursor.execute('''
SELECT category_url, COUNT(*)
FROM categories
GROUP BY category_url
HAVING COUNT(*) > 1
''')

# Получение результатов запроса
duplicate_links = cursor.fetchall()

# Вывод неуникальных ссылок
for link, count in duplicate_links:
    print(f"Link: {link}, Count: {count}")

# Закрытие соединения с базой данных
conn.close()
