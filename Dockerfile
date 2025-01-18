# Base image menggunakan Python 3.11
FROM python:3.10-slim

# Memastikan output log Python segera dikirim ke terminal (tidak buffering)
ENV PYTHONUNBUFFERED=1

# Menetapkan direktori kerja di dalam kontainer
WORKDIR /app

# Salin file requirements terlebih dahulu untuk memanfaatkan layer cache Docker
COPY requirements.txt .

# Menginstal dependencies Python yang dibutuhkan
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh konten direktori lokal ke dalam direktori kerja di kontainer
COPY . .

# Menetapkan variabel lingkungan untuk aplikasi Flask
ENV FLASK_APP=app.py \
    FLASK_ENV=production \
    PORT=8080

# Membuka port 8080 di kontainer
EXPOSE 8080

# Menentukan perintah default untuk menjalankan aplikasi
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "0", "app:app"]