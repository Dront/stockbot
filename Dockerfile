FROM python:3.7-alpine

COPY requirements.txt /
RUN pip install -r /requirements.txt

COPY send_stock_update.py /

ENTRYPOINT ["./send_stock_update.py"]
