# stockbot
Sends last stock info to selected telegram chat on schedule.

# Usage
Configs:
* `<stock_token>` - alphavantage api token - https://www.alphavantage.co/support/#api-key
* `<tg_token>` - telegram bot token - https://core.telegram.org/bots#6-botfather
* config.json - see sample config in sample_config.json

Run:
```bash
docker build -t stockbot .
docker run --mount type=bind,src="$(pwd)"/config.json,dst=/config.json -e STOCK_TOKEN=<stock_token> -e TG_TOKEN=<tg_token> -t stockbot
```
or:
```bash
docker docker run --mount type=bind,src="$(pwd)"/config.json,dst=/config.json -e STOCK_TOKEN=<stock_token> -e TG_TOKEN=<tg_token> -t dront/stockbot:latest
```
where:

Single run (requires python 3.6+):
```bash
pip3 install -r requirements.txt
export STOCK_TOKEN=<stock_token>
export TG_TOKEN=<tg_token>
python3 send_stock_update.py config.json
```
or
```bash
docker build -t stockbot .
docker run --mount type=bind,src="$(pwd)"/config.json,dst=/config.json  -e STOCK_TOKEN=<stock_token> -e TG_TOKEN=<tg_token> -t stockbot ./send_stock_update.py /config.json
```

To get tg_chat_id add bot to chat and run in python interpreter:
```python
from send_stock_update import TGBot
TGBot(<tg_token>).updates()
```
and look for the last "chat" object with field "id".
