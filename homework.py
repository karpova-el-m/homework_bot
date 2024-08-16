import os

from dotenv import load_dotenv
import time
import requests
from telebot import TeleBot, types

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность переменных окружения."""
    env_tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for env in env_tokens:
        if env is None:
            return False


def send_message(bot, message):
    """
    Отправляет сообщение в Telegram-чат.
    Принимает на вход два параметра: экземпляр класса TeleBot и строку
    с текстом сообщения.
    """
    chat = message.chat
    name = message.chat.first_name
    bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text='')


class HTTPError(Exception):
    pass


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    response = requests.get(
        ENDPOINT,
        headers=HEADERS,
        params={'from_date': timestamp}
    )
    if response.status_code != 200:
        raise HTTPError
    return response.json()


def check_response(response):
    """
    Проверяет ответ API на соответствие ожидаемому типу данных.
    В качестве параметра функция получает ответ API, приведённый
    к типам данных Python.
    """
    if not (
        type(response) is dict
        and 'homeworks' in response
        and type(response['homeworks']) is list
    ):
        return False


def parse_status(homework):
    """
    Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент из списка
    домашних работ.
    """
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(timestamp)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
        # else:
        #     pass
        time.sleep(RETRY_PERIOD)

if __name__ == '__main__':
    main()
