import logging
import os
import sys
import time

import requests
from dotenv import load_dotenv
from telebot import apihelper, TeleBot

from exceptions import (
    HomeworkNameError,
    HomeworkStatusError,
    MessageSendingError,
    RequestExceptionError,
    RequestedKeyError,
    UnexpectedStatusError,
)

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
            logging.critical(
                f'Ошибка запуска бота без переменной окружения {env}.'
            )
    if None in env_tokens:
        sys.exit()


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат."""
    logging.debug('Начало отправки сообщения.')
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.debug('Сообщение отправлено.')
    except (apihelper.ApiException, requests.RequestException) as error:
        text = f'Ошибка при отправке сообщения: {error}.'
        logging.error(text)
        raise MessageSendingError(text)


def get_api_answer(timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    request_kwargs = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp}
    }
    logging.debug('Отправка запроса к API.')
    try:
        response = requests.get(**request_kwargs)
    except requests.ConnectionError as connection_err:
        raise ConnectionError(
            f'Ошибка соединения с сервером {connection_err}: {request_kwargs}.'
        )
    except requests.RequestException as request_err:
        raise RequestExceptionError(f'{request_err}: {request_kwargs}')
    if response.status_code != 200:
        raise UnexpectedStatusError('API-сервис вернул код, отличный от 200.')
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие ожидаемому типу данных."""
    logging.debug('Начало проверки ответа от сервера')
    if not type(response) is dict:
        raise TypeError('Ответ API не соответствует ожидаемому типу данных.')
    elif 'homeworks' not in response:
        raise RequestedKeyError('В ответе API отсутствует ожидаемый ключ.')
    elif not type(response['homeworks']) is list:
        raise TypeError(
            'Данные по ключу не соответствует ожидаемому типу данных.'
        )


def parse_status(homework):
    """Получает из информации о конкретной домашней работе статус работы."""
    if homework is None:
        return 'Домашняя работа за указанный период не найдена.'
    if 'homework_name' not in homework:
        raise HomeworkNameError('Домашняя работа не найдена.')
    homework_name = homework['homework_name']
    if 'status' not in homework:
        raise HomeworkStatusError('Отсутствует ключ статуса проверки работы.')
    status = homework['status']
    if status not in HOMEWORK_VERDICTS:
        raise HomeworkStatusError('Некорректиный статус проверки работы.')
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    previous_message = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homeworks = response['homeworks']
            if len(homeworks) > 0:
                homework = homeworks[0]
            else:
                homework = None
            message = parse_status(homework)
            if message != previous_message:
                send_message(bot, message)
            previous_message = message
        except MessageSendingError as error:
            message = f'Сбой при отправке сообщения в телеграм: {error}'
            logging.error(message)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if message != previous_message:
                send_message(bot, message)
            previous_message = message
        finally:
            timestamp = int(time.time())
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logger = logging.getLogger("homework_logger")
    logging.basicConfig(
        level=logging.DEBUG,
        filename='homework.log',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
    )
    handler = logging.StreamHandler(stream=None)
    main()
