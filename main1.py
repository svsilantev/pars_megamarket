import logging
import signal
import argparse
from marketplace_data_import.megamarket_scraper import process_categories, handle_sigint

def main(test_mode=False):
    signal.signal(signal.SIGINT, handle_sigint)
    while True:
        db_path = "megamarket1.db"
        process_categories(db_path, test_mode)
        # if test_mode:
        #     break

if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    main(False)
