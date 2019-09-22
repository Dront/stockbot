#!/usr/bin/env python
import argparse
from collections import namedtuple
import datetime as dt
import json
import logging
import os

import requests


STOCK_URL = 'https://www.alphavantage.co/query'


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
            date=dt.datetime.strptime(datestr, '%Y-%m-%d').date(),
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

    def get_chat(self, chat_id):
        return self._get('getChat', params={'chat_id': chat_id})

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
Данные по {symbol}:
Цена закрытия {first_date:%d-%m-%Y}: {first_price:.2f}$;
Цена закрытия {last_date:%d-%m-%Y}: {last_price:.2f}$;
{trend}: {dollar_diff:.2f}$ ({percent_diff:.2f}%).
"""


def format_message(first_stock, last_stock, symbol):
    dollar_diff = last_stock.close - first_stock.close
    percent_diff = (dollar_diff / first_stock.close) * 100
    template_context = {
        'symbol': symbol,
        'first_date': first_stock.date,
        'last_date': last_stock.date,
        'first_price': first_stock.close,
        'last_price': last_stock.close,
        'trend': 'Рост' if dollar_diff > 0 else 'Падение',
        'dollar_diff': dollar_diff,
        'percent_diff': percent_diff,
    }
    return MSG_TEMPLATE.format(**template_context).strip()


def first(filter_func, iterable):
    for item in iterable:
        if filter_func(item):
            return item
    raise ValueError('Does not exist')


def get_stock_message(stock_symbol, stock_period, stock_token):
    logging.info('getting stocks for %s', stock_symbol)
    stocks = get_stocks(stock_symbol, stock_token)

    stocks = sorted(stocks, key=lambda stock: stock.date, reverse=True)
    last_stock = stocks[0]
    logging.info('last stock: %s', last_stock)
    first_stock_date = last_stock.date - dt.timedelta(days=stock_period)
    first_stock = first(lambda stock: stock.date <= first_stock_date, stocks)
    logging.info('first stock: %s', first_stock)

    message = format_message(first_stock, last_stock, stock_symbol)
    logging.info('%s message: """%s"""', stock_symbol, message)
    return message


StockConfig = namedtuple('StockConfig', ['symbol', 'period'])


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('config_path')
    return parser.parse_args()


def get_env_var(var_name, help_text):
    env_var = os.environ.get(var_name)
    if not env_var:
        error = f'"{var_name}" environment variable is required: {help_text}'
        raise EnvironmentError(error)
    return env_var


def parse_config(config_path):
    with open(config_path) as f:
        config_data = json.load(f)
    tg_chat_id = config_data['tg_chat_id']
    stocks = [StockConfig(**stock_config_data) for stock_config_data in config_data['stocks']]
    return tg_chat_id, stocks


def main(stock_token, tg_token, tg_chat_id, stocks_config):
    stock_messages = [get_stock_message(config.symbol, config.period, stock_token) for config in stocks_config]
    message = '\n\n'.join(stock_messages)
    bot = TGBot(tg_token)
    logging.info('sending message to chat %d', tg_chat_id)
    bot.send_message(tg_chat_id, message, disable_notification=True)
    logging.info('done')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    stock_token = get_env_var('STOCK_TOKEN', 'https://www.alphavantage.co/support/#api-key')
    tg_token = get_env_var('TG_TOKEN', 'https://core.telegram.org/bots#6-botfather')
    config_path = parse_args().config_path
    tg_chat_id, stock_configs = parse_config(config_path)

    main(stock_token, tg_token, tg_chat_id, stock_configs)
