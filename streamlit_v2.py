#Import Libraries
import numpy as np
import matplotlib.pyplot as plt
import ipywidgets as widgets
import streamlit as st
from IPython.display import display
from math import sqrt
from thermo.chemical import Chemical

# Define chemical dictionary
chemicals = {
    'Water': {'name': 'Water'},
    'Ethanol': {'name': 'Ethanol'},
    'Benzene': {'name': 'Benzene'},
    'Acetone': {'name': 'Acetone'}
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
def Gaussian_Plume(Q, u, H, stability_class):
    x_values = np.linspace(10, 1000, 100)  # Downwind distances (m)
    y_values = np.linspace(-200, 200, 50)  # Crosswind distances (m)
    X, Y = np.meshgrid(x_values, y_values)

    sigma_y_coeff, sigma_z_coeff = stability_classes[stability_class]
    sigma_y = sigma_y_coeff * X  # Crosswind dispersion
    sigma_z = sigma_z_coeff * X  # Vertical dispersion

    C = (Q / (2 * np.pi * u * sigma_y * sigma_z)) * np.exp(-Y**2 / (2 * sigma_y**2)) * (
        np.exp(-H**2 / (2 * sigma_z**2)) + np.exp(-(H + 2 * H)**2 / (2 * sigma_z**2))
    )
    return X, Y, C

# Streamlit UI
st.title('Chemical Generation & Air Dispersion Model')

# User input
chem_name = st.selectbox('Select Chemical:', list(chemicals.keys()))
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

# Compute and display results
if st.button('Calculate'):
    # Compute Generation Rate
    G_Rate = Chemical_Generation_Rate(min_Vw, max_Vw, min_Ta, max_Ta, min_As, max_As, chem_name)
    median_value = np.median(G_Rate)
    percentile_95 = np.percentile(G_Rate, 95)

    # Display histogram
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(G_Rate, bins=50, alpha=0.7, color='blue', edgecolor='black', density=True)
    ax.axvline(median_value, color='r', linestyle='--', linewidth=2, label=f'Median: {median_value:.2f}')
    ax.axvline(percentile_95, color='g', linestyle='-.', linewidth=2, label=f'95th Percentile: {percentile_95:.2f}')
    ax.set_xlabel("Generation Rate (gm/min)")
    ax.set_ylabel("Density")
    ax.set_title("Distribution of the Generation Rate (G)")
    ax.legend()
    st.pyplot(fig)

    # Display calculated values
    st.write(f"**Median Generation Rate:** {median_value:.2f} gm/min")
    st.write(f"**95th Percentile Generation Rate:** {percentile_95:.2f} gm/min")

    # Compute dispersion model
    X, Y, C = Gaussian_Plume(percentile_95 / 60, u, H, stability_class)

    # Plot plume
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    contour = ax2.contourf(X, Y, C, levels=20, cmap="jet")
    plt.colorbar(contour, ax=ax2, label="Concentration (gm/m³)")
    ax2.set_xlabel("Downwind Distance (m)")
    ax2.set_ylabel("Crosswind Distance (m)")
    ax2.set_title(f"Gaussian Plume Dispersion - {chem_name}")
    st.pyplot(fig2)

