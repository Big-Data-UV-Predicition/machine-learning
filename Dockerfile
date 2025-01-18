FROM python:3.10-slim

ENV PYTHONBUFFERED True

WORKDIR /app

COPY . ./

ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=8080

RUN pip install -r requirements.txt

EXPOSE 8080

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app