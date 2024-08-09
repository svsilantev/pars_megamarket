from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import logging
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Настройка параметров браузера
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Путь к драйверу ChromeDriver
chrome_driver_path = "chromedriver.exe"
service = Service(executable_path=chrome_driver_path)

# Инициализация драйвера
driver = webdriver.Chrome(service=service, options=chrome_options)

# Открытие страницы
driver.get("https://megamarket.ru/catalog/")

# Ждем, чтобы страница полностью загрузилась
time.sleep(5)

# Сохраняем HTML-контент для отладки
with open('debug_page_selenium.html', 'w', encoding='utf-8') as file:
    file.write(driver.page_source)

# Поиск всех ссылок с классами 'catalog-navigation-menu__third-level-subcategory-link' и 'inverted-catalog-category__link'
try:
    links1 = driver.find_elements(By.CLASS_NAME, 'catalog-navigation-menu__third-level-subcategory-link')
    links2 = driver.find_elements(By.CLASS_NAME, 'inverted-catalog-category__link')
    logger.info(f"Найдено {len(links1)} ссылок с классом 'catalog-navigation-menu__third-level-subcategory-link'")
    logger.info(f"Найдено {len(links2)} ссылок с классом 'inverted-catalog-category__link'")
except Exception as e:
    logger.error(f"Ошибка при поиске ссылок: {e}")
    raise

# Извлекаем href из найденных ссылок
hrefs1 = [link.get_attribute('href') for link in links1]
hrefs2 = [link.get_attribute('href') for link in links2]

# Объединяем все href в один список
hrefs = hrefs1 + hrefs2

# Записываем ссылки в файл
file_path = 'catalog_links.txt'  # Измененный путь для локального хранения
try:
    with open(file_path, 'w', encoding='utf-8') as file:
        for href in hrefs:
            file.write(href + '\n')
    logger.info(f"Ссылки успешно выгружены в файл {file_path}")
except Exception as e:
    logger.error(f"Ошибка при записи ссылок в файл: {e}")
    raise

# Закрываем драйвер
driver.quit()
