FROM python:3.7-alpine

COPY requirements.txt /
RUN pip install -r /requirements.txt

RUN apk add tzdata; cp /usr/share/zoneinfo/Europe/Moscow /etc/localtime; echo "Europe/Moscow" > /etc/timezone; apk del tzdata

RUN echo '0 12 * * TUE-SAT source /.env; /send_stock_update.py "$STOCK_SYMBOL" "$TG_CHAT"' | crontab -

COPY send_stock_update.py /

CMD env > /.env; crond -f -L /dev/stdout
