import logging
import psutil
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from retrying import retry

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def init_driver():
    logging.info("Инициализация драйвера браузера")
    chrome_driver_path = "chromedriver.exe"
    service = ChromeService(executable_path=chrome_driver_path)
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--ignore-certificate-errors-spki-list')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--disable-extensions')
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument('--disable-plugins-discovery')
    options.add_argument('--incognito')
    options.add_argument('--disable-third-party-cookies')
    options.add_argument('--disable-site-isolation-trials')
    options.add_argument('--disable-features=VizDisplayCompositor')
    # Убираем отключение JavaScript
    options.add_argument('--disable-javascript')
    
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_cdp_cmd('Network.enable', {})
    blocking_rules = {
        'urls': [
            '*://cdn.jsdelivr.net/*',
            '*://gc.kis.v2.scr.kaspersky-labs.com/*',
            '*://js-agent.newrelic.com/*',
            '*://www.google-analytics.com/*',
            '*://www.googletagmanager.com/*',
            '*://metrika_match.html/*', 
            '*://www.youtube.com/*',
            '*favicon*',
            '*google.com*',
            '*.css',
            '*mc.yandex.ru',
            '*.ddmanager.ru',
            '*.adspire.io',
            '*.megamarket.tech',
            '*.group-ib.com',
            '*.js',
        ]
    }
    driver.execute_cdp_cmd('Network.setBlockedURLs', blocking_rules)
    return driver

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

def get_page_source(driver, url):
    try:
        logging.info(f"Переход на URL: {url}")
        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        logging.info("Страница загружена успешно")
        
        # Ожидание подгрузки всех элементов списка товаров
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.catalog-items-list__container'))
        )
        
        # # Добавляем паузу для полной загрузки страницы
        # time.sleep(1.5)
        
        # Получаем HTML-код страницы
        page_source = driver.page_source
        return page_source
        
    except TimeoutException:
        logging.error(f"Ошибка: не удалось загрузить страницу {url}")
        return None

# Декоратор для повторных попыток
@retry(stop_max_attempt_number=5, wait_fixed=60000)  # 5 попыток с интервалом в 1 минуту
def try_get_page_source_minutely(driver, url):
    source = get_page_source(driver, url)
    if source is None:
        raise Exception("Не удалось загрузить страницу")
    return source

@retry(stop_max_attempt_number=5, wait_fixed=3600000)  # 5 попыток с интервалом в 1 час
def try_get_page_source_hourly(driver, url):
    source = get_page_source(driver, url)
    if source is None:
        raise Exception("Не удалось загрузить страницу")
    return source

@retry(stop_max_attempt_number=5, wait_fixed=21600000)  # 5 попыток с интервалом в 6 часов
def try_get_page_source_6hourly(driver, url):
    source = get_page_source(driver, url)
    if source is None:
        raise Exception("Не удалось загрузить страницу")
    return source

def get_page_source_with_retries(driver, url):
    try:
        return try_get_page_source_minutely(driver, url)
    except Exception:
        logging.info("Попытки подключения каждую минуту не удались. Переход к попыткам подключения каждый час.")
        try:
            return try_get_page_source_hourly(driver, url)
        except Exception:
            logging.info("Попытки подключения каждый час не удались. Переход к попыткам подключения каждые 6 часов.")
            return try_get_page_source_6hourly(driver, url)

# Пример использования
if __name__ == "__main__":
    driver = init_driver()
    url = "url = https://megamarket.ru/catalog/alkogol"
    page_source = get_page_source_with_retries(driver, url)
    time.sleep(600)
    if page_source:
        logging.info("HTML-код страницы успешно получен")
    else:
        logging.error("Не удалось получить HTML-код страницы после всех попыток")
    driver.quit()
