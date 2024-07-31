import logging
import psutil
import time
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def init_driver():
    logging.info("Определение пути к драйверу")
    if platform.system() == "Windows":
        chrome_driver_path = "chromedriver.exe"
    else:
        chrome_driver_path = "./chromedriver"   

    service = ChromeService(executable_path=chrome_driver_path)
    options = webdriver.ChromeOptions()
    if platform.system() == "Linux":
        options.binary_location = "/usr/bin/google-chrome" 
        options.add_argument('--remote-debugging-port=9222')
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

    logging.info("Инициализация драйвера браузера")
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
        
        # Добавляем паузу для полной загрузки страницы
        time.sleep(2)
        
        # Получаем HTML-код страницы
        page_source = driver.page_source
        print(page_source)
        return page_source
        
    except TimeoutException:
        logging.error(f"Ошибка: не удалось загрузить страницу {url}")
        return None

if __name__ == "__main__":
    driver = init_driver()
    try:
        url = "https://megamarket.ru/catalog/alkogol"
        get_page_source(driver, url)
    finally:
        logging.info("Завершение работы и закрытие драйвера")
        driver.quit()
        kill_processes_by_pids(get_chrome_pids())
