import streamlit as st
import requests
from datetime import datetime
import math
import pytz
import suncalc
from timezonefinder import TimezoneFinder
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display
from math import sqrt
from thermo.chemical import Chemical
import pandas as pd


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
        return 'A' if solar_insolation == 'Strong' else 'B' if solar_insolation == 'Moderate' else 'C' if solar_insolation == 'Slight' else 'E' if night_time == 'Night >50%' else 'F'
    elif wind_speed < 5:
        return 'B' if solar_insolation == 'Strong' else 'B' if solar_insolation == 'Moderate' else 'C' if solar_insolation == 'Slight' else 'D' if night_time == 'Night >50%' else 'E'
    elif wind_speed < 6:
        return 'C' if solar_insolation == 'Strong' else 'C' if solar_insolation == 'Moderate' else 'D' if solar_insolation == 'Slight' else 'D'
    else:
        return 'C' if solar_insolation == 'Strong' else 'D' if solar_insolation in ['Moderate', 'Slight'] else 'D'


def Chemical_Generation_Rate(min_Vw, max_Vw, min_Ta, max_Ta, min_As, max_As):

  #Generate Random Variables from Inputs
  v_wind_samples = np.random.uniform(min_Vw, max_Vw, num_samples)
  Air_Temp_samples = np.random.uniform(Temp_Conversion(min_Ta), Temp_Conversion(max_Ta), num_samples)
  As_samples = np.random.uniform(min_As, max_As, num_samples)

  #Compute Molecular Diffusion Coefficient (m2/s)

  Diff_C = (4.14 * 10**-4 * Air_Temp_samples**1.9 * np.sqrt((1/29)+(1/MW)) * MW**-0.33) / Patm

  G_Rate = 1300 * Diff_C**2 * Vkin**-.9 * ((100 * Vkin * v_wind_samples) / Diff_C)**(0.625*(Vkin / Diff_C)**0.3)*np.sqrt(As_samples)**-0.11 * np.sqrt(Patm / (Patm - Pv)) * Pv / (R * Air_Temp_samples) * MW * As_samples

  return G_Rate

# Define your chemical dictionary
chemicals = {
    'Toluene': {'name': 'Toluene', 'IDLH': 500, 'STEL': 150, 'PEL': 10, 'Conversion': 1.25},
    'Acetone': {'name': 'Acetone','IDLH': 2500, 'STEL': 2499, 'PEL': 1000, 'Conversion': 2.38},
    'Benzene': {'name': 'Benzene','IDLH': 500, 'STEL': 5, 'PEL': 1, 'Conversion': 3.19},
    'Hydrogen Sulfide': {'name': 'Hydrogen Sulfide','IDLH': 100, 'STEL': 50, 'PEL': 20, 'Conversion': 1.40}
}

# Constants
num_samples = 10000
Patm = 101325
Vkin = 1.56 * 10**-5
R = 8.3144

def Temp_Conversion(F):
    return (F - 32) * 5/9 + 273.15

def Chemical_Generation_Rate(min_Vw, max_Vw, min_Ta, max_Ta, min_As, max_As, chem_name):
    chemical = Chemical(chem_name)
    MW = chemical.MW
    v_wind_samples = np.random.uniform(min_Vw, max_Vw, num_samples)
    Air_Temp_samples = np.random.uniform(Temp_Conversion(min_Ta), Temp_Conversion(max_Ta), num_samples)
    vapor_pressure_func = np.vectorize(chemical.VaporPressure)
    Pv_samples = vapor_pressure_func(Air_Temp_samples)
    As_samples = np.random.uniform(min_As, max_As, num_samples)
    Diff_C = (4.14 * 10**-4 * Air_Temp_samples**1.9 * np.sqrt((1/29)+(1/MW)) * MW**-0.33) / Patm
    G_Rate = 1300 * Diff_C**2 * Vkin**-.9 * ((100 * Vkin * v_wind_samples) / Diff_C)**(0.625*(Vkin / Diff_C)**0.3)*np.sqrt(As_samples)**-0.11 * np.sqrt(Patm / (Patm - Pv_samples)) * Pv_samples / (R * Air_Temp_samples) * MW * As_samples
    return G_Rate

def get_sigma(stability_class, x):
    if stability_class == 'A':  # Very Unstable
        sigma_y = 0.22 * x ** 0.894
        sigma_z = 0.20 * x ** 0.911
    elif stability_class == 'B':  # Moderately Unstable
        sigma_y = 0.16 * x ** 0.894
        sigma_z = 0.12 * x ** 0.911
    elif stability_class == 'C':  # Slightly Unstable
        sigma_y = 0.11 * x ** 0.894
        sigma_z = 0.08 * x ** 0.911
    elif stability_class == 'D':  # Neutral
        sigma_y = 0.08 * x ** 0.894
        sigma_z = 0.06 * x ** 0.911
    elif stability_class == 'E':  # Slightly Stable
        sigma_y = 0.06 * x ** 0.894
        sigma_z = 0.03 * x ** 0.911
    elif stability_class == 'F':  # Very Stable
        sigma_y = 0.04 * x ** 0.894
        sigma_z = 0.016 * x ** 0.911
    return sigma_y, sigma_z

def calculate_concentration(x, y, Q, u, sigma_y, sigma_z, chem_name):
    C_gm3 = (Q / (2 * np.pi * sigma_y * sigma_z * u)) * np.exp(-y**2 / (2 * sigma_y**2)) * np.exp(-((0 - 10)**2 / (2 * sigma_z**2)))
    C_ppm = ((C_gm3 *1000) / chemicals[chem_name]['Conversion'])
    return C_ppm

# Plotting function
def plot_data(stability_class, Q, u, chem_name):
    # Define grid in x and y directions
    x_values = np.linspace(10, 1000, 100)  # Downwind distance from 10m to 1000m
    y_values = np.linspace(-100, 100, 100)  # Crosswind distance from -100m to 100m
    X, Y = np.meshgrid(x_values, y_values)
    concentration_map = np.zeros_like(X)

    # Compute concentration map for the selected stability class
    for i in range(len(x_values)):
        sigma_y, sigma_z = get_sigma(stability_class, x_values[i])
        for j in range(len(y_values)):
            concentration_map[j, i] = calculate_concentration(x_values[i], y_values[j], Q, u, sigma_y, sigma_z, chem_name)

    #contour_levels = [0.5, 5, 500]  # TLV, STEL, IDLH in ppm
    
    contour_levels = [chemicals[chem_name]['PEL'],chemicals[chem_name]['STEL'],chemicals[chem_name]['IDLH']]
    
    fig, ax = plt.subplots(figsize=(12, 7))
    heatmap = ax.pcolormesh(X, Y, concentration_map, shading='auto', cmap='viridis')
    plt.colorbar(heatmap, label='Concentration (ppm)', ax=ax)
    contours = ax.contour(X, Y, concentration_map, levels=contour_levels, colors=['yellow', 'orange', 'red'], linewidths=2)
    ax.clabel(contours, inline=True, fontsize=8, fmt='%1.1f ppm')
    ax.set_title(f'Ground-Level {chem_name} Concentration (x-y Plane) with Hazard Contours')
    ax.set_xlabel('Distance Downwind (m)')
    ax.set_ylabel('Distance Crosswind (m)')
    plt.show()
    st.pyplot(fig)

    #Create a DF of Distances:

    # Thresholds
    thresholds = {'TLV': chemicals[chem_name]['PEL'],'STEL': chemicals[chem_name]['STEL'],'IDLH':chemicals[chem_name]['IDLH']}
    results = {'Threshold': [], 'Level': [],'Max Y-Distance (m)': [],'Max X-Distance (m)': []}

    # Analyze distances for each threshold
    for name, level in thresholds.items():
        mask = concentration_map >= level
        if np.any(mask):
            y_dist = np.max(np.abs(Y[mask]))  # Maximum y-distance from centerline
            x_dist = np.max(X[mask])          # Maximum x-distance from source
        else:
            y_dist = 0
            x_dist = 0
            
        # Append results
        results['Threshold'].append(name)
        results['Level'].append(level)
        results['Max Y-Distance (m)'].append(y_dist)
        results['Max X-Distance (m)'].append(x_dist)

    df_results = pd.DataFrame(results)
    st.dataframe(df_results)

    





# Streamlit UI
st.title("Dispersion Model")

# Widgets
city_name = st.selectbox("Select a City:", list(cities.keys()))
chem_name = st.selectbox('Select Chemical:', list(chemicals.keys()))
min_Vw = st.slider('Min Vw (m/s):', 0.0, 20.0, 0.0, 0.1)
max_Vw = st.slider('Max Vw (m/s):', 0.0, 20.0, 20.0, 0.1)
min_Ta = st.slider('Min Ta (°F):', 0.0, 100.0, 0.0, 0.1)
max_Ta = st.slider('Max Ta (°F):', 0.0, 100.0, 100.0, 0.1)
min_As = st.slider('Min As (m²):', 0.0, 10.0, 0.0, 0.1)
max_As = st.slider('Max As (m²):', 0.0, 20.0, 10.0, 0.1)




if st.button("Dispersion Model"):
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

    #calculate generation rate
    G_Rate = Chemical_Generation_Rate(min_Vw, max_Vw, min_Ta, max_Ta, min_As, max_As, chem_name)
    median_value = np.median(G_Rate)
    percentile_95 = np.percentile(G_Rate, 95)



    # Display results For Weather
    st.subheader(f"Weather Conditions in {city_name}")
    st.write(f"**Temperature:** {temp} °C")
    st.write(f"**Humidity:** {humidity}%")
    st.write(f"**Wind Direction:** {wind_deg}°")
    st.write(f"**Wind Speed:** {wind_speed} m/s")
    st.write(f"**Cloud Cover:** {cloud_cover}%")
    st.write(f"**Solar Altitude:** {solar_altitude:.2f} degrees")
    st.write(f"**Calculated Stability Class:** {stability_class}")

    #Display Results for Generation Rate

    plt.figure(figsize=(10, 5))
    plt.hist(G_Rate, bins=50, alpha=0.7, color='blue', edgecolor='black', density=True)

    plt.axvline(median_value, color='r', linestyle='--', linewidth=2, label=f'Median: {median_value:.2f}')
    plt.axvline(percentile_95, color='g', linestyle='-.', linewidth=2, label=f'95th Percentile: {percentile_95:.2f}')
  
    plt.xlabel("Generation Rate (G) (gm/min)")
    plt.ylabel("Density")
    plt.title("Distribution of the Generation Rate (G)")
    st.pyplot(plt)

    st.write(f"**Median:** {median_value:.2f} gm/min")
    st.write(f"**95th Percentile:** {percentile_95:.2f} gm/min")

    plot_data(stability_class, (percentile_95 / 60), wind_speed, chem_name)
