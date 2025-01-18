FROM python:3.10-slim AS deps

ENV PYTHONBUFFERED=1

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.10-slim AS runner

WORKDIR /app

COPY --from=deps /app /app

ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=8080

EXPOSE 8080


CMD ["python", "app.py"]