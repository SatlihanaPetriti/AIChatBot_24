import logging
import tiktoken

class Logger:
    def __init__(self, filename):
        self.filename = filename
        # Устанавливаем кодировку для модели GPT-3.5-turbo-0125
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo-0125")
        # Конфигурируем систему логирования с заданным именем файла, уровнем логирования, форматом сообщений и кодировкой
        logging.basicConfig(filename=filename, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')
    
    def log_message(self, sender, message):
        # Подсчитываем количество токенов в сообщении
        context_tokens = len(self.encoding.encode(message))
        # Логируем отправителя, сообщение и количество токенов
        logging.info(f'{sender}: {message}\nContext tokens: {context_tokens}')

    def log_generated_tokens(self, generated_tokens):
        # Логируем количество сгенерированных токенов
        logging.info(f'Generated tokens: {generated_tokens}')

# Создаем экземпляр логгера с именем файла 'conversation.log'
logger = Logger('conversation.log')
