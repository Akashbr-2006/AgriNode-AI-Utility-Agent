import requests
import random
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

#Knowledge Base: Diverse crops for different Indian climates
CROP_KNOWLEDGE = [
    {"name": "Wheat", "min_temp": 10, "max_temp": 24, "min_rain": 40, "max_rain": 100, "weight": 0.90},
    {"name": "Rice (Paddy)", "min_temp": 22, "max_temp": 35, "min_rain": 150, "max_rain": 400, "weight": 0.88},
    {"name": "Bajra (Millet)", "min_temp": 25, "max_temp": 38, "min_rain": 20, "max_rain": 70, "weight": 0.95},
    {"name": "Coffee", "min_temp": 15, "max_temp": 28, "min_rain": 120, "max_rain": 250, "weight": 0.92},
    {"name": "Mustard", "min_temp": 10, "max_temp": 20, "min_rain": 20, "max_rain": 60, "weight": 0.82},
    {"name": "Jute", "min_temp": 24, "max_temp": 37, "min_rain": 160, "max_rain": 300, "weight": 0.85},
    {"name": "Cotton", "min_temp": 20, "max_temp": 32, "min_rain": 50, "max_rain": 120, "weight": 0.80}
]

STATE_COORDS = {
    "Karnataka": {"lat": 12.97, "lon": 77.59},
    "Rajasthan": {"lat": 26.23, "lon": 73.02},
    "Punjab": {"lat": 30.90, "lon": 75.85},
    "West Bengal": {"lat": 22.57, "lon": 88.36},
    "Maharashtra": {"lat": 18.52, "lon": 73.85},
    "Himachal Pradesh": {"lat": 31.10, "lon": 77.17}
}
#costum function 
def get_season(date_str):
    month = datetime.strptime(date_str, "%Y-%m-%d").month
    if 6 <= month <= 10: return "Kharif"
    if month >= 11 or month <= 3: return "Rabi"
    return "Zaid"

def fetch_climate(lat, lon, date_str):
    month = datetime.strptime(date_str, "%Y-%m-%d").month
    url = f"https://climate-api.open-meteo.com/v1/climate?latitude={lat}&longitude={lon}&start_date=1991-01-01&end_date=2020-12-31&models=ERA5&daily=temperature_2m_mean,precipitation_sum"
    
    try:
        res = requests.get(url).json()
        start = (month - 1) * 30
        end = month * 30
        t_data = res['daily']['temperature_2m_mean'][start:end]
        r_data = res['daily']['precipitation_sum'][start:end]
        return round(sum(t_data)/len(t_data), 1), round(sum(r_data)/len(r_data), 1)
    except:
        return round(random.uniform(15, 35), 1), round(random.uniform(30, 200), 1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    state = data.get('state')
    date = data.get('date')
    
    coords = STATE_COORDS.get(state)
    season = get_season(date)
    temp, rain = fetch_climate(coords['lat'], coords['lon'], date)
    
    results = []
    for crop in CROP_KNOWLEDGE:
        t_score = 50 if (crop['min_temp'] <= temp <= crop['max_temp']) else max(0, 50 - abs(temp - crop['min_temp'])*5)
        r_score = 50 if (crop['min_rain'] <= rain <= crop['max_rain']) else max(0, 50 - abs(rain - crop['min_rain'])*0.5)
        u_score = (t_score + r_score) * crop['weight']
        results.append({"name": crop['name'], "utility": round(u_score, 1)})

    sorted_res = sorted(results, key=lambda x: x['utility'], reverse=True)
    return jsonify({
        "location": state, "season": season, "temp": temp, "rain": rain,
        "best_crop": sorted_res[0], "all_results": sorted_res[:4]
    })

if __name__ == '__main__':
    app.run(debug=True)