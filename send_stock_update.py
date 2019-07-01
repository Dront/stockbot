#!/usr/bin/env python
import argparse
from collections import namedtuple
import datetime as dt
import logging
import os

import requests


STOCK_URL = 'https://www.alphavantage.co/query'
DATE_FORMAT = '%Y-%m-%d'


Stock = namedtuple(
    'Stock',
    ['open', 'high', 'low', 'close', 'volume', 'date']
)


def get_stocks(symbol, token):
    """doc: https://www.alphavantage.co/documentation/#daily"""
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'apikey': token,
        'datatype': 'json',
        'outputsize': 'compact',
    }
    response = requests.get(STOCK_URL, params=params)
    response.raise_for_status()
    raw_data = response.json()['Time Series (Daily)']
    return (
        Stock(
            date=dt.datetime.strptime(datestr, DATE_FORMAT).date(),
            **{key.split(' ', 1)[1]: float(value) for key, value in stock_data.items()}
        )
        for datestr, stock_data in raw_data.items()
    )


class TGException(Exception):
    pass


class TGBot:
    """doc: https://core.telegram.org/bots/api"""

    def __init__(self, token):
        self.token = token

    def _tg_request(self, method, func, *args, **kwargs):
        url = f'https://api.telegram.org/bot{self.token}/{func}'
        response = requests.request(method, url, *args, **kwargs)
        response.raise_for_status()
        data = response.json()
        if not data.get('ok', False):
            raise TGException(f'Something wrong with {method} request to {url}: {data}')
        return data

    def _get(self, func, *args, **kwargs):
        return self._tg_request('get', func, *args, **kwargs)

    def _post(self, func, *args, **kwargs):
        return self._tg_request('post', func, *args, **kwargs)

    def get_me(self):
        return self._get('getMe')

    def updates(self):
        return self._get('getUpdates')

    def send_message(self, chat_id, message, disable_notification=False):
        params = {
            'text': message,
            'chat_id': chat_id,
            'disable_notification': disable_notification,
        }
        return self._post('sendMessage', params=params)


MSG_TEMPLATE = """
Данные по {symbol} за {current_date}:
* цена открытия: {open:.2f}$;
* цена закрытия: {close:.2f}$;
* объем: {volume:.2f} ед.;
* {trend}: {dollar_diff:.2f}$ ({percent_diff:.2f}%).
"""

def format_message(stock, symbol):
    dollar_diff = stock.close - stock.open
    percent_diff = (dollar_diff / stock.open - 1)
    template_context = {
        'symbol': symbol,
        'current_date': stock.date.strftime(DATE_FORMAT),
        'open': stock.open,
        'close': stock.close,
        'volume': stock.volume,
        'trend': 'рост' if dollar_diff > 0 else 'падение',
        'dollar_diff': dollar_diff,
        'percent_diff': percent_diff,
    }
    return MSG_TEMPLATE.format(**template_context).strip()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('stock_symbol', help='like GSH or MSFT')
    parser.add_argument('tg_chat_id', type=int,
                        help='telegram chat id: https://core.telegram.org/bots/api#sendmessage')
    return parser.parse_args()


def get_env_var(var_name, help_text):
    env_var = os.environ.get(var_name)
    if not env_var:
        error = f'"{var_name}" environment variable is required: {help_text}'
        raise EnvironmentError(error)
    return env_var


def main(stock_token, stock_symbol, tg_token, tg_chat_id):
    logging.info('getting stocks')
    stocks = get_stocks(stock_symbol, stock_token)
    last_stock = max(stocks, key=lambda stock: stock.date)
    logging.info('last stock: %s', last_stock)
    message = format_message(last_stock, stock_symbol)
    logging.info('sending message \n%s\nto chat %d', message, tg_chat_id)
    bot = TGBot(tg_token)
    bot.send_message(tg_chat_id, message, disable_notification=True)
    logging.info('done')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    args = parse_args()
    stock_token = get_env_var('STOCK_TOKEN', 'https://www.alphavantage.co/support/#api-key')
    tg_token = get_env_var('TG_TOKEN', 'https://core.telegram.org/bots#6-botfather')
    main(stock_token, args.stock_symbol, tg_token, args.tg_chat_id)
