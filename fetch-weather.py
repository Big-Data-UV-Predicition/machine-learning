import requests
import json
from datetime import datetime, timedelta

# Fungsi untuk meminta data cuaca dari API
def get_weather_data(city, start_date, end_date):
    api_key = ''  # Gantilah dengan API key Anda
    url = f'https://api.worldweatheronline.com/premium/v1/past-weather.ashx?key={api_key}&q={city}&format=json&date={start_date}&enddate={end_date}&includelocation=yes&tp=24'
    
    # Mengirimkan request ke API
    response = requests.get(url)
    
    # Mengecek jika request berhasil
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return None

# Fungsi untuk memecah rentang tanggal menjadi bulan-bulan yang lebih kecil
def split_dates(start_date, end_date):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    date_ranges = []
    while start <= end:
        next_month = start.replace(day=28) + timedelta(days=4)  
        month_end = next_month - timedelta(days=next_month.day) 
        if month_end > end:
            month_end = end
        
        date_ranges.append((start.strftime("%Y-%m-%d"), month_end.strftime("%Y-%m-%d")))
        start = month_end + timedelta(days=1)
    
    return date_ranges

# Fungsi untuk meminta input dari user dan menyimpan data ke file JSON
def save_weather_data():
    city = input("Masukkan nama kota (contoh: Jakarta): ")
    start_date = input("Masukkan tanggal mulai (format: YYYY-MM-DD): ")
    end_date = input("Masukkan tanggal akhir (format: YYYY-MM-DD): ")
    
    date_ranges = split_dates(start_date, end_date)
    
    all_weather_data = []
    location_info = None
    request_info = None
    
    for date_range in date_ranges:
        print(f"Memproses data untuk rentang: {date_range[0]} hingga {date_range[1]}")
        data = get_weather_data(city, date_range[0], date_range[1])
        
        if data:
            if location_info is None and 'data' in data and 'nearest_area' in data['data']:
                location_info = data['data']['nearest_area'][0]
            
            if request_info is None and 'data' in data and 'request' in data['data']:
                request_info = data['data']['request'][0]
            
            if 'data' in data and 'weather' in data['data']:
                all_weather_data.extend(data['data']['weather'])
        else:
            print(f"Gagal mengambil data untuk rentang {date_range[0]} hingga {date_range[1]}")
    
    # Menyimpan data yang telah digabungkan ke dalam file JSON
    if all_weather_data:
        file_name = f"{start_date.split('-')[0]}-{end_date.split('-')[0]}-daily-{city.replace(' ', '-')}.json"
        
        # Membuat struktur data dengan menyertakan informasi lokasi dan request
        output_data = {
            'data': {
                'request': [request_info] if request_info else [],
                'nearest_area': [location_info] if location_info else [],
                'weather': all_weather_data
            }
        }
        
        with open(file_name, 'w') as json_file:
            json.dump(output_data, json_file, indent=4)
        
        print(f"Data berhasil disimpan dalam file {file_name}")
    else:
        print("Tidak ada data yang berhasil diambil.")

# Menjalankan fungsi untuk meminta input dan menyimpan data
save_weather_data()