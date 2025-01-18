from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from datetime import datetime
import numpy as np
import tensorflow as tf
import joblib
import logging

# Inisialisasi aplikasi FastAPI
app = FastAPI()

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfigurasi CORS
origins = ["*"]
methods = ["GET", "POST"]
headers = ["Content-Type"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=methods,
    allow_headers=headers,
)

# Load model dan scaler
try:
    model = tf.keras.models.load_model("uv_index_prediction_model_final.h5")
    scaler = joblib.load("scaler.pkl")
    logger.info("Model dan scaler berhasil dimuat.")
except Exception as e:
    logger.error(f"Error loading model or scaler: {e}")
    raise RuntimeError(f"Error loading model or scaler: {e}")

# Schema untuk input API
class UVIndexRequest(BaseModel):
    city_name: str
    lat: float
    lon: float
    date: str

    @validator("date")
    def validate_date(cls, value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            raise ValueError("Date must be in the format YYYY-MM-DD")

# Fungsi preprocessing
def preprocess_input(lat, lon, date):
    try:
        # Konversi tanggal ke fitur temporal
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        day_of_year = date_obj.timetuple().tm_yday
        month = date_obj.month
        weekday = date_obj.weekday()  # Monday=0, Sunday=6

        # Nilai default untuk cuaca (hanya gunakan jumlah yang dibutuhkan)
        # Jika model hanya membutuhkan 10 fitur, gunakan fitur berikut:
        default_weather = [25.0, 70.0, 50.0, 0.0, 1013.25]  # Contoh data default cuaca

        # Pilih hanya 5 fitur cuaca yang diperlukan
        selected_weather_features = default_weather[:5]  # Pilih sesuai kebutuhan model

        # Gabungkan semua fitur menjadi satu array
        input_data = np.array([[lat, lon, day_of_year, month, weekday, *selected_weather_features]])

        # Pastikan array memiliki 10 fitur (sesuaikan dengan input model)
        if input_data.shape[1] != 10:
            raise ValueError(f"Expected 10 features, but got {input_data.shape[1]}.")

        # Normalisasi input data
        input_scaled = scaler.transform(input_data)

        return input_scaled  # Pastikan input_scaled memiliki 10 fitur
    except Exception as e:
        raise ValueError(f"Error preprocessing input: {e}")

# Endpoint prediksi UV Index
@app.post("/predict")
def predict_uv_index(request: UVIndexRequest):
    try:
        # Preprocess input
        input_scaled = preprocess_input(request.lat, request.lon, request.date)

        # Validasi bentuk input (harus memiliki 10 fitur)
        if input_scaled.shape[1] != 10:
            raise ValueError(f"Input shape mismatch. Expected 10 features, got {input_scaled.shape[1]}.")

        # Prediksi UV Index
        prediction = model.predict(input_scaled)
        uv_index = float(prediction[0][0])

        return {
            "city_name": request.city_name,
            "latitude": request.lat,
            "longitude": request.lon,
            "date": request.date,
            "predicted_uv_index": round(uv_index, 2),
        }

    except ValueError as ve:
        logger.error(f"Value error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Internal server error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

# Endpoint status
@app.get("/status")
def get_status():
    return {"status": "OK"}

# Endpoint root
@app.get("/")
def read_root():
    return {"message": "Welcome to UV Index Prediction API!"}
