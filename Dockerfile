FROM python:3.10-slim

ENV PYTHONBUFFERED=1 \
    APP_HOME=/app \
    PORT=8000

WORKDIR ${APP_HOME}

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "8", "--timeout", "0", "app:app"]