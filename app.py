from flask import Flask, request, jsonify
import requests
import pandas as pd
import numpy as np
import tensorflow as tf
import joblib
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Paths to model and scaler
MODEL_PATH = 'model/uv_model_tf.h5'
SCALER_PATH = 'model/scaler.pkl'
UV_INDEX_FILE = 'uv_indeks.txt'

# Ensure required files exist
if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH) or not os.path.exists(UV_INDEX_FILE):
    raise FileNotFoundError("Model, scaler, or UV index file not found. Ensure the training script has been run.")

# Load model and scaler
try:
    model = tf.keras.models.load_model(MODEL_PATH, custom_objects=None)  # Added custom_objects=None
except Exception as e:
    raise RuntimeError(f"Error loading model: {e}")

try:
    scaler = joblib.load(SCALER_PATH)
except Exception as e:
    raise RuntimeError(f"Error loading scaler: {e}")

# Load UV categories
try:
    with open(UV_INDEX_FILE, 'r') as f:
        uv_categories = [line.strip() for line in f.readlines()]
except Exception as e:
    raise RuntimeError(f"Error loading UV categories: {e}")

# Helper function to categorize UV index
def categorize_uv_index(uv_index):
    if uv_index <= 2:
        return uv_categories[0]  # Low
    elif uv_index <= 5:
        return uv_categories[1]  # Moderate
    elif uv_index <= 7:
        return uv_categories[2]  # High
    elif uv_index <= 10:
        return uv_categories[3]  # Very High
    else:
        return uv_categories[4]  # Extreme

# Fetch weather forecast data
def fetch_forecast_data(api_key, city):
    url = "http://api.worldweatheronline.com/premium/v1/weather.ashx"
    params = {
        'key': api_key,
        'q': city,
        'format': 'json',
        'num_of_days': 3,
        'tp': 24
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error fetching forecast data: {str(e)}")

# Process forecast data to DataFrame
def process_forecast_to_df(data):
    rows = []
    for day in data['data']['weather']:
        date = day['date']
        for hour in day['hourly']:
            row = {
                'date': date,
                'time': hour['time'],
                'tempC': float(hour['tempC']),
                'windspeedKmph': float(hour['windspeedKmph']),
                'humidity': float(hour['humidity']),
                'cloudcover': float(hour['cloudcover']),
                'precipMM': float(hour['precipMM']),
                'pressure': float(hour['pressure']),
                'visibility': float(hour['visibility']),
                'FeelsLikeC': float(hour['FeelsLikeC']),
            }
            rows.append(row)

    return pd.DataFrame(rows)

# Prepare features for model prediction
def prepare_features(df):
    df['date'] = pd.to_datetime(df['date'])
    df['hour'] = df['time'].astype(int) // 100

    df['month'] = df['date'].dt.month
    df['day'] = df['date'].dt.day
    df['day_of_week'] = df['date'].dt.dayofweek
    df['is_daylight'] = ((df['hour'] >= 6) & (df['hour'] <= 18)).astype(int)
    df['daylight_hours'] = 12

    features = [
        'month', 'day', 'day_of_week', 'hour',
        'tempC', 'windspeedKmph', 'humidity',
        'cloudcover', 'precipMM', 'pressure',
        'visibility', 'FeelsLikeC', 'is_daylight',
        'daylight_hours'
    ]
    return df[features]

@app.route("/")
def index():
    return jsonify({
        "status": {
            "code": 200,
            "message": "Weather Prediction API is working.",
        },
        "data": {
            'Project_Name': 'UV Index Prediction',
            'Team': 'Cangcimen',
            'Anggota': [
                {'NPM': '065121068', 'Nama': 'Sandy Budi Wirawan', 'Universitas': 'Pakuan'},
                {'NPM': '065121083', 'Nama': 'Saidina Hikam', 'Universitas': 'Pakuan'},
                {'NPM': '065121076', 'Nama': 'M.Athar Kautsar', 'Universitas': 'Pakuan'},
                {'NPM': '065121077', 'Nama': 'M.Imam Fahrudin', 'Universitas': 'Pakuan'},
                {'NPM': '065121085', 'Nama': 'M.Leon Fadilah', 'Universitas': 'Pakuan'},
                {'NPM': '065121111', 'Nama': 'Eri Mustika Alam', 'Universitas': 'Pakuan'},
            ],
            'Created_By': 'Cangcimen Team',
            'CopyRight': '@2025 All Rights Reserved!'
        }
    }), 200

@app.route('/predict', methods=['POST'])
def predict_realtime():
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        city = data.get('city')

        if not api_key or not city:
            return jsonify({'status': 'error', 'message': 'API key and city are required.'}), 400

        # Fetch weather forecast data
        forecast_data = fetch_forecast_data(api_key, city)

        # Process forecast data into a DataFrame
        df = process_forecast_to_df(forecast_data)
        
        # Prepare features for model prediction
        X = prepare_features(df)

        # Scale the features using the loaded scaler
        X_scaled = scaler.transform(X)
        
        # Make predictions
        predictions = model.predict(X_scaled).flatten()

        # Store predictions and categorize UV index
        df['predicted_uvIndex'] = predictions
        df['uv_category'] = df['predicted_uvIndex'].apply(categorize_uv_index)

        # Filter data to only include future predictions
        now = datetime.utcnow()
        df['datetime'] = pd.to_datetime(df['date']) + pd.to_timedelta(df['hour'], unit='h')
        df = df[df['datetime'] >= now]

        # Format the result for output
        result = df[['datetime', 'predicted_uvIndex', 'uv_category']].to_dict(orient='records')
        
        return jsonify({'status': 'success', 'predictions': result})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)
