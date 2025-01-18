from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
from datetime import datetime, timedelta
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

CITY_COORDINATES = {
    "Bogor": {"lat": -6.5962986, "lon": 106.7972421},
    "Kabupaten Bogor": {"lat": -6.5453255, "lon": 107.0017425},
    "Depok": {"lat": -6.40719, "lon": 106.8158371},
    "Tangerang": {"lat": -6.1761924, "lon": 106.6382161},
    "Tangerang Selatan": {"lat": -6.3227016, "lon": 106.7085737},
    "Bekasi": {"lat": -6.2349858, "lon": 106.9945444},
    "Jakarta": {"lat": -6.2838182, "lon": 106.8048633},
    "Kabupaten Bekasi": {"lat": -6.2027897, "lon": 107.1649161}
}

# Load model dan scaler
try:
    model = tf.keras.models.load_model("model/uv_imam2.h5")
    scaler = joblib.load("model/scaler.pkl")
    logger.info("Model dan scaler berhasil dimuat.")
except Exception as e:
    logger.error(f"Error loading model or scaler: {e}")
    raise RuntimeError(f"Error loading model or scaler: {e}")

# Schema untuk input API
class UVIndexRequest(BaseModel):
    city: str
    date: str

    @validator("city")
    def validate_city(cls, value):
        if value not in CITY_COORDINATES:
            raise ValueError(f"Kota tidak valid. Kota yang tersedia: {', '.join(CITY_COORDINATES.keys())}")
        return value

    @validator("date")
    def validate_date(cls, value):
        try:
            date_obj = datetime.strptime(value, "%Y-%m-%d")
            # Tambahan validasi untuk memastikan tanggal tidak di masa lalu
            if date_obj.date() < datetime.now().date():
                raise ValueError("Tanggal tidak boleh di masa lalu")
            return value
        except ValueError as e:
            raise ValueError("Format tanggal harus YYYY-MM-DD")

# Schema untuk input API 14 hari
class UVIndexFortnightRequest(BaseModel):
    city: str
    start_date: str

    @validator("city")
    def validate_city(cls, value):
        if value not in CITY_COORDINATES:
            raise ValueError(f"Kota tidak valid. Kota yang tersedia: {', '.join(CITY_COORDINATES.keys())}")
        return value

    @validator("start_date")
    def validate_start_date(cls, value):
        try:
            date_obj = datetime.strptime(value, "%Y-%m-%d")
            if date_obj.date() < datetime.now().date():
                raise ValueError("Tanggal tidak boleh di masa lalu")
            return value
        except ValueError as e:
            raise ValueError("Format tanggal harus YYYY-MM-DD")

# Fungsi preprocessing yang lebih robust
def preprocess_input(city: str, date: str):
    try:
        # Ambil koordinat dari dictionary
        coords = CITY_COORDINATES[city]
        lat, lon = coords["lat"], coords["lon"]

        # Konversi tanggal
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        day_of_year = date_obj.timetuple().tm_yday
        month = date_obj.month
        weekday = date_obj.weekday()

        # Default weather features (sesuaikan dengan model training)
        default_weather = [
            25.0,  # tempC
            70.0,  # humidity
            50.0,  # cloudcover
            0.0,   # precipMM
            1013.25  # pressure
        ]

        # Gabungkan semua fitur
        input_features = np.array([[
            lat, lon, 
            day_of_year, month, weekday,
            *default_weather
        ]])

        # Normalisasi menggunakan scaler yang sama dengan training
        input_scaled = scaler.transform(input_features)
        
        return input_scaled

    except Exception as e:
        raise ValueError(f"Error dalam preprocessing: {str(e)}")

# Endpoint prediksi UV Index
@app.post("/predict")
async def predict_uv_index(request: UVIndexRequest):
    try:
        # Preprocess input
        input_scaled = preprocess_input(request.city, request.date)
        
        # Prediksi
        prediction = model.predict(input_scaled)
        uv_index = float(prediction[0][0])

        # Format response
        return {
            "status": "success",
            "data": {
                "city": request.city,
                "coordinates": CITY_COORDINATES[request.city],
                "date": request.date,
                "predicted_uv_index": round(uv_index, 2),
                "uv_risk_level": get_uv_risk_level(uv_index)
            }
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error dalam prediksi: {str(e)}")
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal server")

# Endpoint prediksi UV Index untuk 14 hari
@app.post("/predict-fortnight")
async def predict_uv_index_fortnight(request: UVIndexFortnightRequest):
    """
    Endpoint untuk memprediksi UV Index untuk 14 hari ke depan.
    
    Parameters:
    - city: Nama kota
    - start_date: Tanggal awal prediksi (format: YYYY-MM-DD)
    
    Returns:
    - Array prediksi UV Index untuk 14 hari berturut-turut
    """
    try:
        start_date = datetime.strptime(request.start_date, "%Y-%m-%d")
        predictions = []

        # Prediksi untuk 14 hari kedepan
        for i in range(14):
            current_date = start_date + timedelta(days=i)
            current_date_str = current_date.strftime("%Y-%m-%d")
            
            # Preprocess input untuk tanggal tersebut
            input_scaled = preprocess_input(request.city, current_date_str)
            
            # Prediksi
            prediction = model.predict(input_scaled)
            uv_index = float(prediction[0][0])
            
            # Format hasil prediksi
            predictions.append({
                "date": current_date_str,
                "predicted_uv_index": round(uv_index, 2),
                "uv_risk_level": get_uv_risk_level(uv_index)
            })

        # Format response
        return {
            "status": "success",
            "data": {
                "city": request.city,
                "coordinates": CITY_COORDINATES[request.city],
                "total_days": 14,
                "predictions": predictions
            }
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error dalam prediksi: {str(e)}")
        raise HTTPException(status_code=500, detail="Terjadi kesalahan internal server")

# Fungsi helper untuk menentukan tingkat risiko UV
def get_uv_risk_level(uv_index: float) -> str:
    if uv_index <= 2:
        return "Rendah"
    elif uv_index <= 5:
        return "Sedang"
    elif uv_index <= 7:
        return "Tinggi"
    elif uv_index <= 10:
        return "Sangat Tinggi"
    else:
        return "Ekstrim"

# Endpoint status
@app.get("/status")
def get_status():
    return {"status": "OK"}

# Endpoint root
@app.get("/")
def read_root():
    return {"message": "Welcome to UV Index Prediction API!"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)