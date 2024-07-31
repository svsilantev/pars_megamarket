import time
import logging
import psutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import urllib.parse

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

chrome_driver_path = "D:\\YandexDisk\\Python\\Development\\chromedriver-win64\\chromedriver.exe"
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

def init_driver():
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

def connect_to_megamarket():
    driver = init_driver()
    original_pids = get_chrome_pids()

    # url = f"https://megamarket.ru/catalog/alkogol/"
    url = f"https://megamarket.ru/catalog/alkogol/page-2/"
    
    # base_url = "https://megamarket.ru/catalog/alkogol/"
    # params = {
    #     "filters": '{"FE476AD4A46D4F8EA7B1AB7F30ED017S":["7443"]}'
    # }
    # encoded_params = urllib.parse.urlencode(params)
    # url = f"{base_url}#?{encoded_params}"
    
    try:
        logging.info(f"Переход на URL: {url}")
        driver.get(url)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        logging.info("Страница загружена успешно")
        time.sleep(3000)
    except TimeoutException:
        logging.error(f"Ошибка: не удалось загрузить страницу {url}")
    finally:
        driver.quit()
        current_pids = get_chrome_pids()
        new_pids = set(current_pids) - set(original_pids)
        kill_processes_by_pids(new_pids)

if __name__ == "__main__":
    connect_to_megamarket()
