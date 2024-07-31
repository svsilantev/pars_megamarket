import logging
import os
import psutil
import time
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def init_driver():
    logging.info("Определение пути к драйверу")
    if platform.system() == "Windows":
        chrome_driver_path = "chromedriver.exe"
    else:
        chrome_driver_path = "./chromedriver"  # Указываем текущий рабочий каталог

    service = ChromeService(executable_path=chrome_driver_path)
    options = webdriver.ChromeOptions()
    if platform.system() == "Linux":
        options.binary_location = "/usr/bin/google-chrome"
        options.add_argument('--remote-debugging-port=9222')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-features=VizDisplayCompositor')
    options.add_argument('--disable-web-security')
    options.add_argument('--disable-setuid-sandbox')
    options.add_argument('--disable-logging')
    options.add_argument('--no-first-run')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-client-side-phishing-detection')
    options.add_argument('--disable-default-apps')
    options.add_argument('--disable-hang-monitor')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--disable-prompt-on-repost')
    options.add_argument('--disable-sync')
    options.add_argument('--disable-translate')
    options.add_argument('--metrics-recording-only')
    options.add_argument('--mute-audio')
    options.add_argument('--no-default-browser-check')
    options.add_argument('--no-pings')
    options.add_argument('--password-store=basic')
    options.add_argument('--use-mock-keychain')

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
        logging.info(f"Загрузка страницы: {url}")
        
        # Ожидание элемента, который точно должен присутствовать на странице
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.catalog-items-list__container'))
            )
            logging.info("Элементы списка товаров найдены")
        except TimeoutException:
            logging.error("Ошибка: не удалось найти элементы списка товаров")
            return None

        # Получаем HTML-код страницы
        page_source = driver.page_source
        logging.info("Страница загружена успешно")
        logging.info(page_source[:1000])  # Печатаем первые 1000 символов HTML-кода страницы
        
        return page_source

    except TimeoutException:
        logging.error(f"Ошибка: не удалось загрузить страницу {url}")
        return None

if __name__ == "__main__":
    # Если работаете на Linux, добавьте поддержку виртуального дисплея
    if platform.system() == "Linux":
        from pyvirtualdisplay import Display
        display = Display(visible=0, size=(1920, 1080))
        display.start()
        os.environ["DISPLAY"] = ":99"
    else:
        display = None

    driver = init_driver()
    try:
        urls = [
            "https://megamarket.ru/catalog/alkogol",
            "https://megamarket.ru/catalog/kofemashiny",
            "https://megamarket.ru/catalog/oborudovanie-dlya-umnogo-doma",
            "https://megamarket.ru/catalog/smartfony"
        ]
        
        for url in urls:
            get_page_source(driver, url)
    finally:
        logging.info("Завершение работы и закрытие драйвера")
        driver.quit()
        kill_processes_by_pids(get_chrome_pids())
        if display:
            display.stop()
