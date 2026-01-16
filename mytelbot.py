import os  # Импорт модуля 'os' для взаимодействия с операционной системой
import yaml  # Импорт модуля 'yaml' для чтения YAML-файлов
import openai  # Импорт модуля 'openai' для взаимодействия с API OpenAI
import telebot  # Импорт модуля 'telebot' для создания Telegram-бота
from dotenv import load_dotenv  # Импорт функции 'load_dotenv' из модуля 'dotenv' для загрузки переменных среды
from logging_config import logger  # Импорт 'logger' из модуля 'logging_config' для ведения журнала
from tokens_count import count_tokens  # Импорт функции 'count_tokens' из модуля 'tokens_count' для подсчета токенов
import tiktoken  # Импорт модуля 'tiktoken' для операций с кодированием

load_dotenv()  # Загрузка переменных среды из файла .env
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Получение токена бота Telegram из переменных среды
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # Получение ключа API OpenAI из переменных среды


openai.api_key = OPENAI_API_KEY   # Инициализация OpenAI с помощью ключа API


bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)  # Инициализация Telegram-бота с предоставленным токеном


# Загрузка кодировки(encoding) для модели GPT
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo-0125") 


# Функция для чтения данных из файла data.yaml
def read_data_from_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:  # Открытие файла YAML в режиме чтения
        data = yaml.safe_load(file)  # Загрузка данных из файла YAML
    return data   # Возврат загруженных данных

# Функция для генерации ответа с использованием OpenAI с дополнительными данными
def generate_openai_response(query, university_data):
    # Определение максимального лимита токенов для каждого ответа
    max_tokens_per_response = 200  
    
    # Эта часть кода отвечает за разбиение запроса пользователя на более мелкие фрагменты, гарантируя, 
    # что каждый фрагмент не превышает максимального лимита токенов на ответ, установленного параметром max_tokens_per_response.
    query_chunks = []  
    current_chunk = "" 
    for token in query.split():  
        if len(current_chunk) + len(token) < max_tokens_per_response:  
            current_chunk += token + " "  
        else:
            query_chunks.append(current_chunk.strip())  
            current_chunk = token + " " 
    query_chunks.append(current_chunk.strip()) 
    
    # Генерация ответов для каждого фрагмента
    partial_responses = [] 
    for chunk in query_chunks:  
        prompt = f"{university_data}\n\nUser query: {chunk}"  # Создание подсказки для OpenAI на основе данных университета и текущего фрагмента
        response = openai.ChatCompletion.create(  # Генерация ответа с использованием OpenAI Chat Completion API
            model="gpt-3.5-turbo-0125",   # Указание модели GPT
            messages=[  # Предоставление сообщений модели для контекста
                # указываю роль моего бота.
                {"role": "system", "content": "You are a helpful assistant for answering RUDN university library-related questions only on the language of the user. You responses are short by containing only the required information."},
                {"role": "user", "content": prompt}, 
            ],
            temperature=0,  # Установка температуры на 0 для детерминированного вывода
            max_tokens=200,  # Установка максимального количества токенов для каждого ответа
            top_p=1,  # гарантирует, что на каждом шаге выбирается только наиболее вероятный токен, что приводит к более детерминированному результату.
            frequency_penalty=0,  # Устанавливаем ограничение по частоте на 0 для согласованных ответов (Telling the model not to penalize the frequency of tokens in the response.)
            presence_penalty=0  # Установка штрафа наличия на 0 для согласованных ответов ( the model has more freedom to include a wider range of tokens in the generated text, even if they may not be directly related to the user's query or the context provided. )
        )
        partial_response = response.choices[0].message['content'].strip()
    if partial_response:  # Check if the partial response is not empty
        partial_responses.append(partial_response)

#  Объединение частичных ответов с разделителем новой строки для формирования полного ответа
    complete_response = '\n\n'.join(partial_responses)  

# Remove empty details {'answer': ['']} from the response
    complete_response = complete_response.replace("{'answer': ['']}", "")
    return complete_response  

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_message(message):
    user_name = message.from_user.first_name   # Получение имени пользователя
    welcome_message = f"{user_name}, добро пожаловать!👋\nЯ Telegram-бот, который может отвечать на общие вопросы о библиотеке университета РУДН, используя OpenAI.\nНе стесняйтесь задавать мне что угодно.😊"  # Creating a welcome message
    bot.send_message(message.chat.id, welcome_message)  # Отправка приветственного сообщения пользователю

# Обработчик сообщений с текстом
@bot.message_handler(func=lambda message:True)
def handle_message(message):
    user_input = message.text  # Получение текстового сообщения, отправленного пользователем

    # Чтение данных из файла data.yaml
    university_data = read_data_from_file("data.yaml")  

    # Генерация ответа с использованием OpenAI с дополнительными данными
    openai_response = generate_openai_response(user_input, university_data)  

    # Расчет количества сгенерированных токенов
    generated_tokens = len(logger.encoding.encode(openai_response))  
   
    logger.log_message('User', user_input) 
    
    
    logger.log_message('Bot', openai_response) 

    # количества сгенерированных токенов
    logger.log_generated_tokens(generated_tokens)  

     # Отправка ответа, сгенерированного OpenAI, обратно пользователю
    bot.send_message(message.chat.id, openai_response)  
bot.polling() 
