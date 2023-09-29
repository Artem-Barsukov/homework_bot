import os
from time import time
import requests
import telegram
from telegram import Bot
from telegram.ext import Updater
from dotenv import load_dotenv


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
    """Проверка на наличие необходимых токенов."""
    token_list = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for token in token_list:
        if token is None:
            raise Exception('Не все токены заполнены!')


def send_message(bot, message):
    """Отправка сообщения в Telegram."""
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(timestamp):
    """Запрос к эндпоинту Яндекс.Практикум, получение данных."""
    responce = requests.get(
        ENDPOINT,
        headers=HEADERS,
        params={'from_date': timestamp}
    )
    if responce.status_code != 200:
        raise Exception('В запросе переданы некорректные данные (токен/дата)')
    return responce.json()


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('В ответе ожидается словарь')
    if 'homeworks' not in response:
        raise KeyError('Ключ homeworks в словаре не найден.')
    if not isinstance(response['homeworks'], list):
        raise TypeError('В полученном словаре нет списка работ')
    return True


def parse_status(homework):
    """Получение значения статуса работы."""
    if 'homework_name' not in homework:
        raise KeyError('Ключ homework_name в словаре не найден.')
    homework_name = homework['homework_name']
    status = homework['status']
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())


    ...

    while True:
        try:

            ...

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
        ...


if __name__ == '__main__':
    main()
