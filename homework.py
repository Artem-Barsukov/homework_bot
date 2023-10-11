import logging
import os
import time
from http import HTTPStatus

import requests
import telegram
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
    if not all(token_list):
        logging.critical('Не все токены заполнены!')
        raise Exception('Не все токены заполнены!')


def send_message(bot, message):
    """Отправка сообщения в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение отправлено.')
    except telegram.TelegramError as error:
        logging.error(f'Сообщение не отправлено: {error}')


def get_api_answer(timestamp):
    """Запрос к эндпоинту Яндекс.Практикум, получение данных."""
    try:
        responce = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )

        if responce.status_code != HTTPStatus.OK:
            raise Exception('В запросе переданы некорректные данные')
        return responce.json()
    except requests.RequestException() as error:
        raise Exception(error)


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('В ответе ожидается словарь')
    if (key_value := response.get('homeworks')) is None:
        raise KeyError('Ключ homeworks в словаре не найден.')
    if not isinstance(key_value, list):
        raise TypeError('В полученном словаре нет списка работ')


def parse_status(homework):
    """Получение значения статуса работы."""
    if (homework_name := homework.get('homework_name')) is None:
        raise KeyError('Ключ homework_name в словаре не найден.')
    if (status := homework.get('status')) is None:
        raise KeyError('Ключ status в словаре не найден.')
    if status not in HOMEWORK_VERDICTS:
        raise KeyError('Неожиданный статус')
    verdict = HOMEWORK_VERDICTS[status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_status = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homeworks = response['homeworks']
            if not homeworks:
                continue
            last_homework = homeworks[0]
            if last_status == last_homework['status']:
                logging.debug('Новые статусы отсутствуют.')
                continue
            message = parse_status(last_homework)
            send_message(bot, message)
            last_status = last_homework['status']
            timestamp = response['current_date']

        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
        finally:
            time.sleep(RETRY_PERIOD)


logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(message)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

if __name__ == '__main__':
    main()
