import sqlite3

# Подключение к базе данных
conn = sqlite3.connect('megamarket.db')
cursor = conn.cursor()

# Запрос для получения ID всех неуникальных ссылок, отсортированных по category_url и id
cursor.execute('''
SELECT id, category_url
FROM categories
WHERE category_url IN (
    SELECT category_url
    FROM categories
    GROUP BY category_url
    HAVING COUNT(*) > 1
)
ORDER BY category_url, id
''')

# Получение результатов запроса
duplicate_records = cursor.fetchall()

# Поиск и удаление второй неуникальной ссылки для каждой группы дублирующихся ссылок
current_url = None
second_id_to_delete = None

for record in duplicate_records:
    record_id, url = record

    if url != current_url:
        current_url = url
        second_id_to_delete = None
    elif second_id_to_delete is None:
        second_id_to_delete = record_id

        # Удаление второй неуникальной ссылки
        cursor.execute('DELETE FROM categories WHERE id = ?', (second_id_to_delete,))
        conn.commit()

# Закрытие соединения с базой данных
conn.close()
