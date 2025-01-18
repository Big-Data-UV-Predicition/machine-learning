FROM python:3.10-slim

ENV PYTHONBUFFERED=1 \
    APP_HOME=/app \
    PORT=8080

WORKDIR ${APP_HOME}

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "0", "app:app"]