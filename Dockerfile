FROM python:3.9

ENV PYTHONBUFFERED True

WORKDIR /app

COPY . ./

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

RUN pip install -r requirements.txt

EXPOSE 8080

ENV PORT=8080

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app