import logging
import signal
import argparse
from marketplace_data_import.megamarket_scraper import process_categories, handle_sigint

def main(test_mode=False):
    signal.signal(signal.SIGINT, handle_sigint)
    
    # Настройка параметров подключения к базе данных PostgreSQL
    db_name = "megamarket1"  # Имя базы данных
    user = "postgres"  # Имя пользователя базы данных
    password = "p161054p"  # Пароль пользователя базы данных
    host = "localhost"  # Хост базы данных (обычно localhost)
    port = "5433"  # Порт базы данных (5433)

    while True:
        process_categories(db_name, user, password, host, port, test_mode)
        # if test_mode:
        #     break

if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    main(False)
