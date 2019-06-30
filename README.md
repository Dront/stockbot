# stockbot
Sends last stock info to selected telegram chat daily (tuesday-saturday are days with updates) at 12.

# Usage
Run:
```bash
docker build -t stockbot .
docker run -e STOCK_TOKEN=<stock_token> -e TG_TOKEN=<tg_token> -e STOCK_SYMBOL=<symbol> -e TG_CHAT=<chat_id> -t stockbot
```
or:
```bash
docker docker run -e STOCK_TOKEN=<stock_token> -e TG_TOKEN=<tg_token> -e STOCK_SYMBOL=<symbol> -e TG_CHAT=<chat_id> -t dront/stockbot:latest
```
where:
`<stock_token>` - alphavantage api token - https://www.alphavantage.co/support/#api-key
`<tg_token>` - telegram bot token - https://core.telegram.org/bots#6-botfather
`<symbol>` - stock symbol (something like `GSH` or `MSFT`)
`<chat_id>` - telegram chat id

Single run (requires python 3.6+):
```python
pip3 install -r requirements.txt
export STOCK_TOKEN=<stock_token>
export TG_TOKEN=<tg_token>
python3 send_stock_update.py <symbol> <chat_id>
```

To get chat id add bot to chat and run in python interpreter:
```python
from send_stock_update import TGBot
TGBot(<tg_token>).updates()
```
and look for the last "chat" object with field "id".
