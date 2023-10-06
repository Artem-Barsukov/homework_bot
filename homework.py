import logging
import os
import time

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
    for token in token_list:
        if token is None:
            logging.critical('Не все токены заполнены!')
            raise Exception('Не все токены заполнены!')


def send_message(bot, message):
    """Отправка сообщения в Telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение отправлено.')
    except telegram.TelegramError as error:
        logging.error('Сообщение не отправлено.')
        raise Exception(error)


def get_api_answer(timestamp):
    """Запрос к эндпоинту Яндекс.Практикум, получение данных."""
    try:
        responce = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )

        if responce.status_code != 200:
            raise Exception('В запросе переданы некорректные данные')
        return responce.json()
    except requests.RequestException() as error:
        logging.error(f'Ошибка запроса к API {error}')


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('В ответе ожидается словарь')
    if 'homeworks' not in response:
        logging.error('Ключ homeworks в словаре не найден.')
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
    if status not in HOMEWORK_VERDICTS:
        logging.error('Неожиданный статус')
        raise KeyError('Неожиданный статус')
    else:
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
            if homeworks:
                last_homework = homeworks[0]
                if last_status != last_homework['status']:
                    message = parse_status(last_homework)
                    send_message(bot, message)
                    last_status = last_homework['status']
                else:
                    logging.debug('Новые статусы отсутствуют.')

            timestamp = homeworks['current_date']
        except Exception as error:
            message = f'Сбой в работе программы: {error}'

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
