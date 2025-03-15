import streamlit as st
import requests
from datetime import datetime
import math
import pytz
import suncalc
from timezonefinder import TimezoneFinder

# OpenWeatherMap API Key
api_key = 'f8f0a843de6209c90148d9350e81e55a'  # Replace with your actual API key

# Cities Dictionary
cities = {
    'Duluth, MN': {'lat': 46.7867, 'lon': -92.1005},
    'Houston, TX': {'lat': 29.7604, 'lon': -95.3698},
    'Chicago, IL': {'lat': 41.8781, 'lon': -87.6298},
    'Cushing, OK': {'lat': 35.9851, 'lon': -96.7665},
    'Minot, ND': {'lat': 48.2325, 'lon': -101.2963},
    'Kansas City, MO': {'lat': 39.0997, 'lon': -94.5786},
    'Casper, WY': {'lat': 42.8501, 'lon': -106.3252},
    'Corpus Christi, TX': {'lat': 27.8006, 'lon': -97.3964}
}

def fetch_weather_data(lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url)
    return response.json()

def calculate_solar_altitude(lat, lon):
    tf = TimezoneFinder()

    # Get UTC Time
    utc_datetime_str = requests.get("http://worldtimeapi.org/api/timezone/etc/UTC").json()['datetime']
    utc_datetime = datetime.fromisoformat(utc_datetime_str.replace('Z', '+00:00'))

    # Find the timezone and convert local time
    timezone_str = tf.timezone_at(lat=lat, lng=lon)
    timezone = pytz.timezone(timezone_str)
    local_time = utc_datetime.astimezone(timezone)

    # Calculate solar altitude
    position = suncalc.get_position(local_time, lat=lat, lng=lon)
    solar_altitude = position['altitude'] * (180 / math.pi)

    return solar_altitude

def determine_stability_class(wind_speed, cloud_cover, solar_altitude):
    CI = cloud_cover / 10

    if math.sin(solar_altitude) > 0.1:
        E_Flux = 1111 * (1 - 0.0071 * CI**2) * (math.sin(solar_altitude) - 0.1)
    else:
        E_Flux = 0

    if E_Flux > 851:
        solar_insolation = 'Strong'
    elif E_Flux > 526:
        solar_insolation = 'Moderate'
    elif E_Flux > 176:
        solar_insolation = 'Slight'
    else:
        solar_insolation = 'None'

    night_time = 'Night >50%' if cloud_cover > 50 else 'Night <50%'

    # Selecting stability class based on wind speed and conditions
    if wind_speed < 2:
        return 'A' if solar_insolation == 'Strong' else 'B' if solar_insolation == 'Moderate' else 'C' if solar_insolation == 'Slight' else 'E' if night_time == 'Night >50%' else 'F'
    elif wind_speed < 3:
        return 'A-B' if solar_insolation == 'Strong' else 'B' if solar_insolation == 'Moderate' else 'C' if solar_insolation == 'Slight' else 'E' if night_time == 'Night >50%' else 'F'
    elif wind_speed < 5:
        return 'B' if solar_insolation == 'Strong' else 'B-C' if solar_insolation == 'Moderate' else 'C' if solar_insolation == 'Slight' else 'D' if night_time == 'Night >50%' else 'E'
    elif wind_speed < 6:
        return 'C' if solar_insolation == 'Strong' else 'C-D' if solar_insolation == 'Moderate' else 'D' if solar_insolation == 'Slight' else 'D'
    else:
        return 'C' if solar_insolation == 'Strong' else 'D' if solar_insolation in ['Moderate', 'Slight'] else 'D'

# Streamlit UI
st.title("Weather & Stability Class Calculator")

# City selection dropdown
city_name = st.selectbox("Select a City:", list(cities.keys()))

if st.button("Get Weather Data"):
    city = cities[city_name]
    
    # Fetch weather data
    weather_data = fetch_weather_data(city['lat'], city['lon'])
    temp = weather_data['main']['temp']
    humidity = weather_data['main']['humidity']
    wind_speed = weather_data['wind']['speed']
    wind_deg = weather_data['wind']['deg']
    cloud_cover = weather_data['clouds']['all']

    # Calculate solar altitude and stability class
    solar_altitude = calculate_solar_altitude(city['lat'], city['lon'])
    stability_class = determine_stability_class(wind_speed, cloud_cover, solar_altitude)

    # Display results
    st.subheader(f"Weather Conditions in {city_name}")
    st.write(f"**Temperature:** {temp} °C")
    st.write(f"**Humidity:** {humidity}%")
    st.write(f"**Wind Direction:** {wind_deg}°")
    st.write(f"**Wind Speed:** {wind_speed} m/s")
    st.write(f"**Cloud Cover:** {cloud_cover}%")
    st.write(f"**Solar Altitude:** {solar_altitude:.2f} degrees")
    st.write(f"**Calculated Stability Class:** {stability_class}")
