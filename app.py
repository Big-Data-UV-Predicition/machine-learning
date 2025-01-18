from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import numpy as np
import tensorflow as tf
import joblib

# Inisialisasi aplikasi FastAPI
app = FastAPI()

origins = ["https://bi-fe.cangcimen.my.id"] 
methods = ["GET", "POST"]
headers = ["Content-Type"] 

app.add_middleware(
    CORSMiddleware, 
    allow_origins = origins,
    allow_credentials = False,
    allow_methods = methods,
    allow_headers = headers    
)

# Load model dan scaler
try:
    model = tf.keras.models.load_model("uv_index_prediction_model_final.h5")
    scaler = joblib.load("scaler.pkl")  # Pastikan file scaler.pkl ada
except Exception as e:
    raise RuntimeError(f"Error loading model or scaler: {e}")

# Schema untuk input API
class UVIndexRequest(BaseModel):
    city_name: str
    lat: float
    lon: float
    date: str  # Format YYYY-MM-DD

# Fungsi preprocessing
def preprocess_input(lat, lon, date):
    try:
        # Konversi tanggal ke fitur temporal
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        day_of_year = date_obj.timetuple().tm_yday
        month = date_obj.month
        weekday = date_obj.weekday()  # Monday=0, Sunday=6

        # Nilai default untuk cuaca
        default_weather = [25.0, 70.0, 50.0, 0.0, 1013.25]

        # Buat array input
        input_data = np.array([[lat, lon, day_of_year, month, weekday, *default_weather]])

        # Normalisasi input data
        input_scaled = scaler.transform(input_data)
        return input_scaled

    except Exception as e:
        raise ValueError(f"Error preprocessing input: {e}")

# Endpoint prediksi UV Index
@app.post("/predict")
def predict_uv_index(request: UVIndexRequest):
    try:
        # Preprocess input
        input_scaled = preprocess_input(request.lat, request.lon, request.date)

        # Prediksi UV Index
        prediction = model.predict(input_scaled)
        uv_index = float(prediction[0][0])

        return {
            "city_name": request.city_name,
            "latitude": request.lat,
            "longitude": request.lon,
            "date": request.date,
            "predicted_uv_index": round(uv_index, 2)
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

# Endpoint status
@app.get("/status")
def get_status():
    return {"status": "OK"}

# Endpoint root
@app.get("/")
def read_root():
    return {"message": "Welcome to UV Index Prediction API!"}
