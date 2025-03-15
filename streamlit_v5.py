import streamlit as st
import requests
from datetime import datetime
import math
import pytz
import suncalc
from timezonefinder import TimezoneFinder
import folium
from streamlit_folium import folium_static

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

# Fetch weather data from OpenWeatherMap
def fetch_weather_data(lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url)
    return response.json()

# Function to display an interactive map with OpenWeatherMap layers
def show_weather_map(lat, lon):
    map_url = f"https://tile.openweathermap.org/map/temp_new/2/{lon}/{lat}.png?appid={api_key}"

    # Create Folium Map
    m = folium.Map(location=[lat, lon], zoom_start=8)
    folium.TileLayer('openstreetmap').add_to(m)

    # Overlay Weather Layer
    folium.raster_layers.TileLayer(
        tiles=f"https://tile.openweathermap.org/map/clouds_new/{8}/{lon}/{lat}.png?appid={api_key}",
        attr="OpenWeatherMap",
        name="Clouds",
        overlay=True,
        control=True
    ).add_to(m)

    folium.raster_layers.TileLayer(
        tiles=f"https://tile.openweathermap.org/map/temp_new/{8}/{lon}/{lat}.png?appid={api_key}",
        attr="OpenWeatherMap",
        name="Temperature",
        overlay=True,
        control=True
    ).add_to(m)

    folium.LayerControl().add_to(m)

    # Display Map in Streamlit
    folium_static(m)

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

    # Display results
    st.subheader(f"Weather Conditions in {city_name}")
    st.write(f"**Temperature:** {temp} °C")
    st.write(f"**Humidity:** {humidity}%")
    st.write(f"**Wind Direction:** {wind_deg}°")
    st.write(f"**Wind Speed:** {wind_speed} m/s")
    st.write(f"**Cloud Cover:** {cloud_cover}%")

    # Show weather map
    st.subheader("Live Weather Map")
    show_weather_map(city['lat'], city['lon'])
