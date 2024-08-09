import logging
import time
import psycopg2
from datetime import datetime
from bs4 import BeautifulSoup
import psutil
from marketplace_data_import.browser_setup import init_driver, get_page_source
import signal
import sys

driver = None  # Глобальная переменная для драйвера

def get_chrome_pids():
    chrome_pids = []
    for proc in psutil.process_iter(attrs=['pid', 'name']):
        if 'chrome' in proc.info['name'].lower():
            chrome_pids.append(proc.info['pid'])
    return chrome_pids

def kill_processes_by_pids(pids):
    for pid in pids:
        try:
            proc = psutil.Process(pid)
            proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def get_db_connection(db_name, user, password, host='localhost', port='5433'):
    start_time = time.time()  # Время начала выполнения
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port,
            options='-c client_encoding=utf8'
        )
        return conn
    except Exception as e:
        logging.error(f"Ошибка при подключении к базе данных: {e}")
        raise
    finally:
        logging.info(f"Время подключения к базе данных: {time.time() - start_time:.2f} сек")

def get_unique_categories(conn):
    start_time = time.time()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT category_url FROM categories')
    categories = cursor.fetchall()
    cursor.close()  # Закрываем курсор
    logging.info(f"Время получения уникальных категорий: {time.time() - start_time:.2f} сек")
    return categories

def parse_items(page_source, category):
    start_time = time.time()
    soup = BeautifulSoup(page_source, 'html.parser')
    container = soup.find('div', class_='catalog-items-list__container')
    if not container:
        logging.error("Не удалось найти контейнер с классом 'catalog-items-list__container'")
        return []

    items = container.find_all('div', class_='catalog-item-regular-desktop')
    # logging.info(f"Найдено товаров: {len(items)}")

    result = []

    for item in items:
        # Извлечение всех необходимых данных за один проход
        product_link = item.select_one('a.catalog-item-regular-desktop__title-link')
        merchant_name = item.select_one('span[data-test="merchant-name"]')
        product_name = item.select_one('a[data-test="product-name-link"]')
        original_price = item.select_one('span[data-test="discount-price"]')
        discounted_price = item.select_one('div[data-test="product-price"]')
        discount_percent = item.select_one('div[data-test="discount-text"]')
        bonus_percent = item.select_one('span[data-test="bonus-percent"]')
        bonus_amount = item.select_one('span[data-test="bonus-amount"]')
        rating = item.select_one('div[data-test="rating-stars-value"]')
        reviews_count = item.select_one('div.catalog-item-review__review-amount')

        # Быстрая проверка наличия обязательных элементов
        if not product_name or not discounted_price:
            continue

        product_name_text = product_name.get_text(strip=True)
        original_price_value = float(original_price.get_text(strip=True).replace(' ', '').replace('₽', '')) if original_price else None
        discounted_price_value = float(discounted_price.get_text(strip=True).replace(' ', '').replace('₽', ''))
        discount_percent_value = float(discount_percent.get_text(strip=True).replace('%', '').replace('-', '')) if discount_percent else None
        bonus_percent_value = float(bonus_percent.get_text(strip=True).replace('%', '')) if bonus_percent else None
        bonus_amount_value = float(bonus_amount.get_text(strip=True).replace(' ', '').replace('₽', '')) if bonus_amount else None
        final_price = discounted_price_value - (bonus_amount_value if bonus_amount_value else 0)
        rating_value = float(rating['style'].replace('width:', '').replace('%', '').replace(';', '').strip()) if rating else None
        reviews_count_value = int(reviews_count.get_text(strip=True).replace(' ', '')) if reviews_count else None
        merchant_name_text = merchant_name.get_text(strip=True) if merchant_name else 'Unknown'
        product_link_url = 'https://megamarket.ru' + product_link['href'] if product_link else None

        result.append({
            "load_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "name": product_name_text,
            "merchant": merchant_name_text,
            "original_price": original_price_value,
            "discounted_price": discounted_price_value,
            "discount_percent": discount_percent_value,
            "bonus_percent": bonus_percent_value,
            "bonus_amount": bonus_amount_value,
            "final_price": final_price,
            "rating": rating_value,
            "reviews_count": reviews_count_value,
            "product_link": product_link_url
        })

    logging.info(f"Время парсинга товаров: {time.time() - start_time:.2f} сек")
    return result


def save_to_temp_database(data, conn):
    start_time = time.time()
    cursor = conn.cursor()
    
    for item in data:
        cursor.execute('''
            INSERT INTO temp_products (load_date, category, name, merchant, original_price, discounted_price, 
                                       discount_percent, bonus_percent, bonus_amount, final_price, rating, reviews_count, product_link)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (item['load_date'], item['category'], item['name'], item['merchant'], item['original_price'],
              item['discounted_price'], item['discount_percent'], item['bonus_percent'], item['bonus_amount'],
              item['final_price'], item['rating'], item['reviews_count'], item['product_link']))
    
    conn.commit()
    cursor.close()  # Закрываем курсор
    logging.info(f"Время сохранения данных во временную таблицу: {time.time() - start_time:.2f} сек")

def get_category_name(page_source):
    start_time = time.time()
    if page_source is None:
        return 'Unknown'
    soup = BeautifulSoup(page_source, 'html.parser')
    category_element = soup.find('h1', itemprop='name', class_='catalog-header__title')
    if category_element:
        category_name = category_element.get_text(strip=True).replace('страница', '').strip()
        logging.info(f"Время определения имени категории: {time.time() - start_time:.2f} сек")
        return category_name
    logging.info(f"Время определения имени категории: {time.time() - start_time:.2f} сек")
    return 'Unknown'

def get_next_categories_to_process(conn):
    start_time = time.time()
    cursor = conn.cursor()
    
    # Получаем ID категории с самым поздним временем окончания
    cursor.execute('''
        SELECT id 
        FROM categories 
        ORDER BY COALESCE(load_time_end, '1970-01-01 00:00:00') DESC 
        LIMIT 1
    ''')
    last_processed_id = cursor.fetchone()
    last_processed_id = last_processed_id[0] if last_processed_id else 0
    
    # Получаем категории, начиная с категории с ID + 1
    cursor.execute('''
        SELECT id, category_url 
        FROM categories 
        WHERE id > %s 
        ORDER BY id
    ''', (last_processed_id,))
    categories = cursor.fetchall()
    
    # Если после самой свежей категории нет больше категорий, начинаем с начала
    if not categories:
        cursor.execute('''
            SELECT id, category_url 
            FROM categories 
            ORDER BY id
        ''')
        categories = cursor.fetchall()
    
    cursor.close()  # Закрываем курсор
    logging.info(f"Время получения следующей категории для обработки: {time.time() - start_time:.2f} сек")
    return categories

def process_categories(db_name, user, password, host='localhost', port='5433', test_mode=False):
    global driver
    conn = get_db_connection(db_name, user, password, host, port)
    driver = init_driver()
    original_pids = get_chrome_pids()

    categories = get_next_categories_to_process(conn)

    try:
        for category_id, category_url in categories:
            logging.info(f"Переход на URL: {category_url}")
            category_name = 'Unknown'
            page_number = 0
            pages_loaded = 0
            load_time_start = time.time()
            total_items_count = 0

            while True:
                if page_number == 0:
                    url = category_url
                else:
                    url = f"{category_url}/page-{page_number}/"

                logging.info(f"Загрузка страницы: {url}")
                start_time = time.time()  # Время начала загрузки страницы
                page_source = get_page_source(driver, url)
                load_duration = time.time() - start_time  # Время, затраченное на загрузку страницы
                logging.info(f"Время загрузки страницы {url}: {load_duration:.2f} сек")

                if page_source:
                    if page_number == 0:
                        category_name = get_category_name(page_source)
                        logging.info(f"Определено имя категории: {category_name}")
                    items = parse_items(page_source, category_name)
                    if not items and page_number > 0:
                        logging.info(f"Нет больше товаров на странице {page_number}. Переход к следующей категории.")
                        break
                    total_items_count += len(items)
                    pages_loaded += 1
                    save_to_temp_database(items, conn)
                else:
                    logging.error(f"Ошибка: не удалось загрузить страницу {url}")
                    logging.error(f"Не удалось получить страницу {page_number}. Переход к следующей категории.")
                    break
                page_number += 1
                if test_mode and page_number > 1:
                    break

            load_time_end = time.time()
            load_time = round(load_time_end - load_time_start, 0)
            load_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if category_name and category_name != 'Unknown':
                logging.info(f"Попытка удалить старые записи для категории: {category_name}")
                cursor = conn.cursor()
                cursor.execute('DELETE FROM products WHERE category = %s', (category_name,))
                logging.info(f"Удалены старые записи для категории: {category_name}")

                cursor.execute('SELECT COUNT(*) FROM temp_products')
                temp_count = cursor.fetchone()[0]
                logging.info(f"Количество записей во временной таблице перед вставкой: {temp_count}")

                cursor.execute('''
                    INSERT INTO products (load_date, category, name, merchant, original_price, discounted_price, 
                                          discount_percent, bonus_percent, bonus_amount, final_price, rating, reviews_count, product_link)
                    SELECT load_date, category, name, merchant, original_price, discounted_price, discount_percent,
                        bonus_percent, bonus_amount, final_price, rating, reviews_count, product_link
                    FROM temp_products
                ''')
                logging.info(f"Вставлены новые данные для категории: {category_name}")

                cursor.execute('SELECT COUNT(*) FROM products WHERE category = %s', (category_name,))
                product_count = cursor.fetchone()[0]
                logging.info(f"Количество записей в основной таблице после вставки: {product_count}")

                cursor.execute('DELETE FROM temp_products')
                logging.info(f"Очищена временная таблица для категории: {category_name}")

                # Вставка максимального бонусного процента по категории
                cursor.execute('''
                    SELECT MAX(bonus_percent) FROM products WHERE category = %s
                ''', (category_name,))
                max_bonus_percent = cursor.fetchone()[0]

                cursor.execute('''
                    UPDATE categories 
                    SET category_name = %s, load_time = %s, load_date = %s, load_time_start = %s, load_time_end = %s, 
                        items_count = %s, pages_loaded = %s, max_bonus_percent = %s 
                    WHERE category_url = %s
                ''', (category_name, load_time, load_date, datetime.fromtimestamp(load_time_start).strftime('%Y-%m-%d %H:%M:%S'), 
                      datetime.fromtimestamp(load_time_end).strftime('%Y-%m-%d %H:%M:%S'), total_items_count, pages_loaded, max_bonus_percent, category_url))
                logging.info(f"Обновлена категория: {category_name} в таблице categories")
            else:
                logging.error("Не удалось определить имя категории. Пропуск удаления и вставки записей.")
            conn.commit()

    finally:
        if driver:
            driver.quit()
        current_pids = get_chrome_pids()
        new_pids = set(current_pids) - set(original_pids)
        kill_processes_by_pids(new_pids)
        conn.close()

def handle_sigint(signal, frame):
    logging.info("Получен сигнал SIGINT. Завершение работы...")
    if driver:
        driver.quit()
    time.sleep(2)  # Добавляем задержку для завершения всех соединений
    sys.exit(0)
