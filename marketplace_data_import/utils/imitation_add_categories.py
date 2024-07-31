import logging
import time
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup
from browser_setup import init_driver, get_chrome_pids, kill_processes_by_pids, get_page_source

def get_unique_categories():
    conn = sqlite3.connect('megamarket/megamarket.db')
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
        original_price_element = item.select_one('div[data-test="original-price"]')
        discounted_price_element = item.select_one('div[data-test="product-price"]')
        discount_percent_element = item.select_one('span[data-test="discount-percent"]')
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
    conn = sqlite3.connect('megamarket/megamarket.db')
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

def main(test_mode=False):
    start_time = time.time()
    driver = init_driver()
    original_pids = get_chrome_pids()

    categories = get_unique_categories()

    try:
        for category_url, in categories:
            logging.info(f"Переход на URL: {category_url}")
            page_number = 1
            while True:
                url = f"{category_url}/page-{page_number}/"
                logging.info(f"Загрузка страницы: {url}")
                page_source = get_page_source(driver, url)
                if page_source:
                    category_name = get_category_name(page_source)
                    items = parse_items(page_source, category_name)
                    if not items:
                        logging.info(f"Нет больше товаров на странице {page_number}. Переход к следующей категории.")
                        break
                    save_to_temp_database(items)
                else:
                    logging.error(f"Не удалось получить страницу {page_number}. Переход к следующей категории.")
                    break
                page_number += 1
                if test_mode and page_number > 1:
                    break

            conn = sqlite3.connect('megamarket/megamarket.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE categories SET category_name = ? WHERE category_url = ?', (category_name, category_url))
            cursor.execute('DELETE FROM products WHERE category = ?', (category_name,))
            cursor.execute('''
                INSERT INTO products (load_date, category, name, merchant, original_price, discounted_price, 
                                      discount_percent, bonus_percent, bonus_amount, final_price, rating, reviews_count)
                SELECT load_date, category, name, merchant, original_price, discounted_price, discount_percent,
                       bonus_percent, bonus_amount, final_price, rating, reviews_count
                FROM temp_products
            ''')
            cursor.execute('DELETE FROM temp_products')
            conn.commit()
            conn.close()

        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(f"Время выполнения: {elapsed_time:.2f} секунд")
    finally:
        driver.quit()
        current_pids = get_chrome_pids()
        new_pids = set(current_pids) - set(original_pids)
        kill_processes_by_pids(new_pids)

def get_category_name(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    category_element = soup.find('h1', itemprop='name', class_='catalog-header__title')
    if category_element:
        category_name = category_element.get_text(strip=True).replace('страница', '').strip()
        return category_name
    return 'Unknown'

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main(test_mode=True)
