import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import folium
from streamlit_folium import folium_static
from folium.plugins import HeatMap
from thermo.chemical import Chemical

# Define major cities with their coordinates
cities = {
    "New York, USA": (40.7128, -74.0060),
    "Los Angeles, USA": (34.0522, -118.2437),
    "London, UK": (51.5074, -0.1278),
    "Paris, France": (48.8566, 2.3522),
    "Tokyo, Japan": (35.6895, 139.6917),
    "Sydney, Australia": ( -33.8688, 151.2093)
}

# Constants
num_samples = 10000
Patm = 101325
Vkin = 1.56 * 10**-5
R = 8.3144

# Stability class coefficients (Pasquill-Gifford)
stability_classes = {
    'A': (0.22, 0.2),
    'B': (0.16, 0.12),
    'C': (0.11, 0.08),
    'D': (0.08, 0.06),
    'E': (0.06, 0.03),
    'F': (0.04, 0.016)
}

# Temperature conversion function
def Temp_Conversion(F):
    return (F - 32) * 5/9 + 273.15

# Function to calculate generation rate
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

# Gaussian plume function
def Gaussian_Plume(Q, u, H, stability_class, lat, lon):
    x_values = np.linspace(10, 1000, 50)  # Downwind distances (m)
    y_values = np.linspace(-200, 200, 25)  # Crosswind distances (m)
    X, Y = np.meshgrid(x_values, y_values)

    sigma_y_coeff, sigma_z_coeff = stability_classes[stability_class]
    sigma_y = sigma_y_coeff * X  # Crosswind dispersion
    sigma_z = sigma_z_coeff * X  # Vertical dispersion

    C = (Q / (2 * np.pi * u * sigma_y * sigma_z)) * np.exp(-Y**2 / (2 * sigma_y**2)) * (
        np.exp(-H**2 / (2 * sigma_z**2)) + np.exp(-(H + 2 * H)**2 / (2 * sigma_z**2))
    )

    # Convert local dispersion (x, y) to real-world lat/lon shifts
    latitudes, longitudes, concentrations = [], [], []
    for i in range(len(X)):
        for j in range(len(Y[i])):
            lat_shift = lat + (X[i, j] / 111000)  # Approx conversion: 1 deg = 111 km
            lon_shift = lon + (Y[i, j] / (111000 * np.cos(np.radians(lat))))  # Adjust for longitude
            latitudes.append(lat_shift)
            longitudes.append(lon_shift)
            concentrations.append(C[i, j])

    return latitudes, longitudes, concentrations

# Streamlit UI
st.title('Chemical Generation & Air Dispersion Model')

# Dropdown to select a city for dispersion modeling
selected_city = st.selectbox("Select a city for dispersion mapping:", list(cities.keys()))
city_lat, city_lon = cities[selected_city]

# User input for chemical properties
chem_name = st.selectbox('Select Chemical:', ["Water", "Ethanol", "Benzene", "Acetone"])
min_Vw = st.slider('Min Wind Speed (m/s):', 0.0, 20.0, 0.0, 0.1)
max_Vw = st.slider('Max Wind Speed (m/s):', 0.0, 20.0, 20.0, 0.1)
min_Ta = st.slider('Min Air Temperature (°F):', 0.0, 100.0, 0.0, 0.1)
max_Ta = st.slider('Max Air Temperature (°F):', 0.0, 100.0, 100.0, 0.1)
min_As = st.slider('Min Surface Area (m²):', 0.0, 10.0, 0.0, 0.1)
max_As = st.slider('Max Surface Area (m²):', 0.0, 20.0, 10.0, 0.1)

# Plume parameters
H = st.number_input("Release Height (m)", min_value=0.1, value=2.0, step=0.1)
u = st.number_input("Wind Speed at Release Height (m/s)", min_value=0.1, value=3.0, step=0.1)
stability_class = st.selectbox("Atmospheric Stability Class", list(stability_classes.keys()), index=3)

if st.button('Calculate'):
    # Compute Generation Rate
    G_Rate = Chemical_Generation_Rate(min_Vw, max_Vw, min_Ta, max_Ta, min_As, max_As, chem_name)
    percentile_95 = np.percentile(G_Rate, 95)

    # Compute dispersion model
    latitudes, longitudes, concentrations = Gaussian_Plume(percentile_95 / 60, u, H, stability_class, city_lat, city_lon)

    # Create a Folium map centered at the selected city
    map_dispersion = folium.Map(location=[city_lat, city_lon], zoom_start=10)

    # Add a heatmap of dispersion concentrations
    heat_data = [[lat, lon, conc] for lat, lon, conc in zip(latitudes, longitudes, concentrations)]
    HeatMap(heat_data, radius=15, blur=10, max_zoom=12).add_to(map_dispersion)

    # Display the map in Streamlit
    st.write(f"**Dispersion Map for {chem_name} in {selected_city}**")
    folium_static(map_dispersion)
