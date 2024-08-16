import logging
import os
import time

import requests
from dotenv import load_dotenv
from telebot import TeleBot, types

from exceptions import (
    EnvError, HomeworkNameError, HomeworkStatusError, HTTPError, RequestExceptionError, SendMessageError
)

logger = logging.getLogger("homework_logger")
logging.basicConfig(
    level=logging.DEBUG,
    filename='homework.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
handler = logging.StreamHandler(stream=None)

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
    if None in env_tokens:
        logging.critical('Ошибка запуска бота без переменных окружения')
        raise EnvError


def send_message(bot, message):
    """
    Отправляет сообщение в Telegram-чат.
    Принимает на вход два параметра: экземпляр класса TeleBot и строку
    с текстом сообщения.
    """
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.debug('Сообщение отправлено')
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения: {error}')


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
    except requests.RequestException:
        raise RequestExceptionError
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
        raise TypeError
    elif len(response['homeworks']) == 0:
        logging.debug('Список домашних работ за указанный период пуст')


def parse_status(homework):
    """
    Извлекает из информации о конкретной домашней работе статус этой работы.
    В качестве параметра функция получает только один элемент из списка
    домашних работ.
    """
    if 'homework_name' not in homework:
        raise HomeworkNameError('Домашняя работа не найдена')
    homework_name = homework['homework_name']
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise HomeworkStatusError
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = 0
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homework = response['homeworks'][0]
            message = parse_status(homework)
            send_message(bot, message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
