FROM python:3.7-alpine

RUN apk add tzdata; cp /usr/share/zoneinfo/Europe/Moscow /etc/localtime; echo "Europe/Moscow" > /etc/timezone; apk del tzdata

COPY requirements.txt /
RUN pip install -r /requirements.txt

RUN echo '0 12 * * SUN source /.env; /send_stock_update.py /config.json'  | crontab -

COPY send_stock_update.py /

CMD env > /.env; crond -f -L /dev/stdout
