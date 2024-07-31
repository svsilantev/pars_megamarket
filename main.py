# main.py
import logging
import signal
from marketplace_data_import.megamarket_scraper import process_categories, handle_sigint

def main(test_mode=False):
    signal.signal(signal.SIGINT, handle_sigint)
    while True:
        process_categories(test_mode)
        if test_mode:
            break

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main(test_mode=True)
