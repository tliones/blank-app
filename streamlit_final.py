import streamlit as st
import requests
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import math
import pytz
import suncalc
from timezonefinder import TimezoneFinder
from thermo.chemical import Chemical

# OpenWeatherMap API Key (replace with your actual API key)
api_key = 'f8f0a843de6209c90148d9350e81e55a'

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

def Temp_Conversion(F):
    return (F - 32) * 5/9 + 273.15

def Chemical_Generation_Rate(v_wind, min_Ta, max_Ta, min_As, max_As, chem_name):
    num_samples = 10000
    Patm = 101325
    Vkin = 1.56 * 10**-5
    R = 8.3144
    chemical = Chemical(chem_name)
    MW = chemical.MW
    
    Air_Temp_samples = np.random.uniform(Temp_Conversion(min_Ta), Temp_Conversion(max_Ta), num_samples)
    Pv_samples = np.vectorize(chemical.VaporPressure)(Air_Temp_samples)
    As_samples = np.random.uniform(min_As, max_As, num_samples)
    Diff_C = (4.14 * 10**-4 * Air_Temp_samples**1.9 * np.sqrt((1/29)+(1/MW)) * MW**-0.33) / Patm
    
    G_Rate = 1300 * Diff_C**2 * Vkin**-.9 * ((100 * Vkin * v_wind) / Diff_C)**(0.625*(Vkin / Diff_C)**0.3)*np.sqrt(As_samples)**-0.11 * np.sqrt(Patm / (Patm - Pv_samples)) * Pv_samples / (R * Air_Temp_samples) * MW * As_samples
    return G_Rate

# Streamlit UI
st.title("Weather & Chemical Generation Rate Calculator")

# Step 1: City Selection
city_name = st.selectbox("Select a City:", list(cities.keys()))

if st.button("Get Weather Data"):
    city = cities[city_name]
    weather_data = fetch_weather_data(city['lat'], city['lon'])
    
    temp = weather_data['main']['temp']
    humidity = weather_data['main']['humidity']
    wind_speed = weather_data['wind']['speed']
    cloud_cover = weather_data['clouds']['all']
    
    st.subheader(f"Weather Conditions in {city_name}")
    st.write(f"**Temperature:** {temp} °C")
    st.write(f"**Humidity:** {humidity}%")
    st.write(f"**Wind Speed:** {wind_speed} m/s")
    st.write(f"**Cloud Cover:** {cloud_cover}%")
    
    # Step 2: Chemical Selection
    st.subheader("Chemical Selection and Generation Rate Calculation")
    chemicals = ['Water', 'Ethanol', 'Benzene', 'Acetone']
    chem_name = st.selectbox('Select Chemical:', chemicals)
    
    min_Ta = st.slider('Min Temperature (°F):', 0.0, 100.0, 0.0, 0.1)
    max_Ta = st.slider('Max Temperature (°F):', 0.0, 100.0, 100.0, 0.1)
    min_As = st.slider('Min Surface Area (m²):', 0.0, 10.0, 0.0, 0.1)
    max_As = st.slider('Max Surface Area (m²):', 0.0, 20.0, 10.0, 0.1)
    
    if st.button('Calculate Generation Rate'):
        G_Rate = Chemical_Generation_Rate(wind_speed, min_Ta, max_Ta, min_As, max_As, chem_name)
        median_value = np.median(G_Rate)
        percentile_95 = np.percentile(G_Rate, 95)
        
        plt.figure(figsize=(10, 5))
        plt.hist(G_Rate, bins=50, alpha=0.7, color='blue', edgecolor='black', density=True)
        plt.axvline(median_value, color='r', linestyle='--', linewidth=2, label=f'Median: {median_value:.2f}')
        plt.axvline(percentile_95, color='g', linestyle='-.', linewidth=2, label=f'95th Percentile: {percentile_95:.2f}')
        plt.xlabel("Generation Rate (gm/min)")
        plt.ylabel("Density")
        plt.title("Distribution of the Generation Rate")
        st.pyplot(plt)
        
        st.write(f"**Median:** {median_value:.2f} gm/min")
        st.write(f"**95th Percentile:** {percentile_95:.2f} gm/min")

