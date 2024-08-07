import logging
import time
import sqlite3
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

def get_unique_categories():
    conn = sqlite3.connect('megamarket.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT category_url FROM categories')
    categories = cursor.fetchall()
    conn.close()
    return categories

def parse_items(page_source, category):
    soup = BeautifulSoup(page_source, 'html.parser')
    container = soup.find('div', class_='catalog-items-list__container')
    if not container:
        logging.error("Не удалось найти контейнер с классом 'catalog-items-list__container'")
        return []

    items = container.find_all('div', class_='catalog-item-regular-desktop')
    logging.info(f"Найдено товаров: {len(items)}")

    result = []

    for item in items:
        merchant_name_element = item.select_one('span[data-test="merchant-name"]')
        product_name_element = item.select_one('a[data-test="product-name-link"]')
        original_price_element = item.select_one('span[data-test="discount-price"]')
        discounted_price_element = item.select_one('div[data-test="product-price"]')
        discount_percent_element = item.select_one('div[data-test="discount-text"]')
        bonus_percent_element = item.select_one('span[data-test="bonus-percent"]')
        bonus_amount_element = item.select_one('span[data-test="bonus-amount"]')
        rating_element = item.select_one('div[data-test="rating-stars-value"]')
        reviews_count_element = item.select_one('div.catalog-item-review__review-amount')

        if not product_name_element or not discounted_price_element:
            logging.warning("Не найдено необходимых данных для товара")
            continue

        product_name = product_name_element.get_text(strip=True)
        volume = product_name.split(',')[-1].strip()  # Извлекаем объем из наименования
        original_price = float(original_price_element.get_text(strip=True).replace(' ', '').replace('₽', '')) if original_price_element else None
        discounted_price = float(discounted_price_element.get_text(strip=True).replace(' ', '').replace('₽', ''))
        discount_percent = float(discount_percent_element.get_text(strip=True).replace('%', '').replace('-', '')) if discount_percent_element else None
        bonus_percent = float(bonus_percent_element.get_text(strip=True).replace('%', '')) if bonus_percent_element else None
        bonus_amount = float(bonus_amount_element.get_text(strip=True).replace(' ', '').replace('₽', '')) if bonus_amount_element else None
        final_price = discounted_price - (bonus_amount if bonus_amount else 0)
        rating = float(rating_element['style'].replace('width:', '').replace('%', '').replace(';', '').strip()) if rating_element else None
        reviews_count = int(reviews_count_element.get_text(strip=True).replace(' ', '')) if reviews_count_element else None
        merchant = merchant_name_element.get_text(strip=True) if merchant_name_element else 'Unknown'

        logging.info(f"Товар: Name={product_name}, Original Price={original_price}, Discounted Price={discounted_price}, "
                     f"Discount Percent={discount_percent}, Bonus Percent={bonus_percent}, Bonus Amount={bonus_amount}, "
                     f"Final Price={final_price}")

        result.append({
            "load_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "category": category,
            "name": product_name,
            "merchant": merchant,
            "original_price": original_price,
            "discounted_price": discounted_price,
            "discount_percent": discount_percent,
            "bonus_percent": bonus_percent,
            "bonus_amount": bonus_amount,
            "final_price": final_price,
            "rating": rating,
            "reviews_count": reviews_count
        })

    return result

def save_to_temp_database(data):
    conn = sqlite3.connect('megamarket.db')
    cursor = conn.cursor()
    
    for item in data:
        cursor.execute('''
            INSERT INTO temp_products (load_date, category, name, merchant, original_price, discounted_price, 
                                       discount_percent, bonus_percent, bonus_amount, final_price, rating, reviews_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (item['load_date'], item['category'], item['name'], item['merchant'], item['original_price'],
              item['discounted_price'], item['discount_percent'], item['bonus_percent'], item['bonus_amount'],
              item['final_price'], item['rating'], item['reviews_count']))
    
    conn.commit()
    conn.close()

def get_category_name(page_source):
    if page_source is None:
        return 'Unknown'
    soup = BeautifulSoup(page_source, 'html.parser')
    category_element = soup.find('h1', itemprop='name', class_='catalog-header__title')
    if category_element:
        category_name = category_element.get_text(strip=True).replace('страница', '').strip()
        return category_name
    return 'Unknown'

def get_next_categories_to_process():
    conn = sqlite3.connect('megamarket.db')
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
        WHERE id > ? 
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
    
    conn.close()
    return categories

def process_categories(test_mode=False):
    global driver
    driver = init_driver()
    original_pids = get_chrome_pids()

    categories = get_next_categories_to_process()

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
                page_source = get_page_source(driver, url)

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
                    save_to_temp_database(items)
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

            conn = sqlite3.connect('megamarket.db')
            cursor = conn.cursor()

            if category_name and category_name != 'Unknown':
                logging.info(f"Попытка удалить старые записи для категории: {category_name}")
                cursor.execute('DELETE FROM products WHERE category = ?', (category_name,))
                logging.info(f"Удалены старые записи для категории: {category_name}")

                cursor.execute('SELECT COUNT(*) FROM temp_products')
                temp_count = cursor.fetchone()[0]
                logging.info(f"Количество записей во временной таблице перед вставкой: {temp_count}")

                cursor.execute('''
                    INSERT INTO products (load_date, category, name, merchant, original_price, discounted_price, 
                                          discount_percent, bonus_percent, bonus_amount, final_price, rating, reviews_count)
                    SELECT load_date, category, name, merchant, original_price, discounted_price, discount_percent,
                        bonus_percent, bonus_amount, final_price, rating, reviews_count
                    FROM temp_products
                ''')
                logging.info(f"Вставлены новые данные для категории: {category_name}")

                cursor.execute('SELECT COUNT(*) FROM products WHERE category = ?', (category_name,))
                product_count = cursor.fetchone()[0]
                logging.info(f"Количество записей в основной таблице после вставки: {product_count}")

                cursor.execute('DELETE FROM temp_products')
                logging.info(f"Очищена временная таблица для категории: {category_name}")

                # Вставка максимального бонусного процента по категории
                cursor.execute('''
                    SELECT MAX(bonus_percent) FROM products WHERE category = ?
                ''', (category_name,))
                max_bonus_percent = cursor.fetchone()[0]

                cursor.execute('''
                    UPDATE categories 
                    SET category_name = ?, load_time = ?, load_date = ?, load_time_start = ?, load_time_end = ?, 
                        items_count = ?, pages_loaded = ?, max_bonus_percent = ? 
                    WHERE category_url = ?
                ''', (category_name, load_time, load_date, datetime.fromtimestamp(load_time_start).strftime('%Y-%m-%d %H:%M:%S'), 
                      datetime.fromtimestamp(load_time_end).strftime('%Y-%m-%d %H:%M:%S'), total_items_count, pages_loaded, max_bonus_percent, category_url))
                logging.info(f"Обновлена категория: {category_name} в таблице categories")
            else:
                logging.error("Не удалось определить имя категории. Пропуск удаления и вставки записей.")
            conn.commit()
            conn.close()

    finally:
        if driver:
            driver.quit()
        current_pids = get_chrome_pids()
        new_pids = set(current_pids) - set(original_pids)
        kill_processes_by_pids(new_pids)


def handle_sigint(signal, frame):
    logging.info("Получен сигнал SIGINT. Завершение работы...")
    if driver:
        driver.quit()
    time.sleep(2)  # Добавляем задержку для завершения всех соединений
    sys.exit(0)

def main(test_mode=False):
    signal.signal(signal.SIGINT, handle_sigint)
    while True:
        process_categories(test_mode)
        # if test_mode:
        #     break

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levellevel)s - %(message)s')
    main(test_mode=True)
