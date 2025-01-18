FROM python:3.8-slim

ENV PYTHONBUFFERED True

COPY . /app

WORKDIR /app

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

RUN pip install -r requirements.txt

EXPOSE 8080

ENV PORT=8080

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app