import logging
import sys

def setup_logger(log_file='fetch_messages.log', log_level=logging.DEBUG):
    """
    Настраивает логгер с заданным файлом и уровнем логирования.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Устанавливаем уровень логгера на DEBUG
    
    # Удаляем все существующие обработчики
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Создаем обработчик для файла, который будет записывать сообщения уровня INFO и выше
    file_handler = logging.FileHandler(log_file, encoding='windows-1251')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(filename)s - %(levelname)s - %(funcName)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    
    # Создаем обработчик для консоли, который будет выводить все сообщения уровня DEBUG и выше
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_formatter = logging.Formatter('%(asctime)s - %(filename)s - %(levelname)s - %(funcName)s - %(message)s')
    stream_handler.setFormatter(stream_formatter)
    
    # Добавляем обработчики к логгеру
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    
    return logger

# Установка системной кодировки на utf-8 для корректного отображения в консоли
sys.stdout.reconfigure(encoding='utf-8')

# # Пример использования
# logger = setup_logger()

# user = "User123"

# # Логирование сообщений различных уровней с включением имени пользователя в текст сообщения
# logger.debug(f'{user} - Это сообщение уровня DEBUG')
# logger.info(f'{user} - Это сообщение уровня INFO')
# logger.warning(f'{user} - Это сообщение уровня WARNING')
# logger.error(f'{user} - Это сообщение уровня ERROR')
# logger.critical(f'{user} - Это сообщение уровня CRITICAL')

# # Логирование особого случая
# logger.info(f'{user} - Особый случай: что-то интересное произошло')
