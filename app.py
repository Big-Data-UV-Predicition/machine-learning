from flask import Flask, request, jsonify
import requests
import pandas as pd
import numpy as np
import tensorflow as tf
import joblib
import os
from datetime import datetime, timedelta

app = Flask(__name__)

MODEL_PATH = 'model/uv_model_tf.h5'
SCALER_PATH = 'model/scaler.pkl'
UV_INDEX_FILE = 'uv_indeks.txt'

if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
    raise FileNotFoundError("Model or scaler file not found. Ensure the training script has been run.")

model = tf.keras.models.load_model(MODEL_PATH) # On this line, fix this to load the model
scaler = joblib.load(SCALER_PATH)

with open(UV_INDEX_FILE, 'r') as f:
    uv_categories = [line.strip() for line in f.readlines()]

def categorize_uv_index(uv_index):
    if uv_index <= 2:
        return uv_categories[0] 
    elif uv_index <= 5:
        return uv_categories[2] 
    elif uv_index <= 7:
        return uv_categories[5] 
    elif uv_index <= 10:
        return uv_categories[8] 
    else:
        return uv_categories[10] 

def fetch_forecast_data(api_key, city):
    url = "http://api.worldweatheronline.com/premium/v1/weather.ashx"
    params = {
        'key': api_key,
        'q': city,
        'format': 'json',
        'num_of_days': 3,
        'tp': 24
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching forecast data: {response.status_code}, {response.text}")

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

@app.route('/predict-realtime', methods=['POST'])
def predict_realtime():
    try:

        data = request.get_json()
        api_key = data.get('api_key')
        city = data.get('city')

        if not api_key or not city:
            return jsonify({'status': 'error', 'message': 'API key and city are required.'}), 400

        forecast_data = fetch_forecast_data(api_key, city)

        df = process_forecast_to_df(forecast_data)
        X = prepare_features(df)

        X_scaled = scaler.transform(X)

        predictions = model.predict(X_scaled).flatten()

        df['predicted_uvIndex'] = predictions
        df['uv_category'] = df['predicted_uvIndex'].apply(categorize_uv_index)

        now = datetime.utcnow()
        df['datetime'] = pd.to_datetime(df['date']) + pd.to_timedelta(df['hour'], unit='h')
        df = df[df['datetime'] >= now]

        result = df[['datetime', 'predicted_uvIndex', 'uv_category']].to_dict(orient='records')
        return jsonify({'status': 'success', 'predictions': result})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=8080)