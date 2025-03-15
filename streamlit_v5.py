import streamlit as st
import requests
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

# Function to fetch weather data
def fetch_weather_data(lat, lon):
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    response = requests.get(url)
    return response.json()

# Function to create and show radar map
def show_radar_map(lat, lon):
    # Create base map
    m = folium.Map(location=[lat, lon], zoom_start=7)

    # Add OpenWeatherMap radar (precipitation) layer
    folium.raster_layers.TileLayer(
        tiles=f"https://tile.openweathermap.org/map/precipitation_new/6/{lon}/{lat}.png?appid={api_key}",
        attr="OpenWeatherMap",
        name="Precipitation Radar",
        overlay=True,
        control=True
    ).add_to(m)

    # Add optional layers (Clouds, Wind, Temperature)
    folium.raster_layers.TileLayer(
        tiles=f"https://tile.openweathermap.org/map/clouds_new/6/{lon}/{lat}.png?appid={api_key}",
        attr="OpenWeatherMap",
        name="Cloud Coverage",
        overlay=True,
        control=True
    ).add_to(m)

    folium.raster_layers.TileLayer(
        tiles=f"https://tile.openweathermap.org/map/wind_new/6/{lon}/{lat}.png?appid={api_key}",
        attr="OpenWeatherMap",
        name="Wind Speed",
        overlay=True,
        control=True
    ).add_to(m)

    # Add layer control
    folium.LayerControl().add_to(m)

    # Display map in Streamlit
    folium_static(m)

# Streamlit UI
st.title("Weather & Radar Viewer")

# City selection dropdown
city_name = st.selectbox("Select a City:", list(cities.keys()))

if st.button("Get Weather Data & Radar"):
    city = cities[city_name]
    
    # Fetch weather data
    weather_data = fetch_weather_data(city['lat'], city['lon'])
    temp = weather_data['main']['temp']
    humidity = weather_data['main']['humidity']
    wind_speed = weather_data['wind']['speed']
    wind_deg = weather_data['wind']['deg']
    cloud_cover = weather_data['clouds']['all']

    # Display weather conditions
    st.subheader(f"Weather Conditions in {city_name}")
    st.write(f"**Temperature:** {temp} °C")
    st.write(f"**Humidity:** {humidity}%")
    st.write(f"**Wind Direction:** {wind_deg}°")
    st.write(f"**Wind Speed:** {wind_speed} m/s")
    st.write(f"**Cloud Cover:** {cloud_cover}%")

    # Display radar map
    st.subheader("Live Weather Radar")
    show_radar_map(city['lat'], city['lon'])
