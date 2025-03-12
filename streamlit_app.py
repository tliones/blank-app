#Generate Random Values for Inputs (v, Temp, Length, Width)
num_samples = 10000
MW = 92.1
Patm = 101325
Pv = 2800
Vkin = 1.56 * 10**-5
R = 8.3144

def Temp_Conversion(F):
  return (F - 32) * 5/9 + 273.15


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

# Streamlit UI
st.title('Chemical Generation Rate Calculator')

chem_name = st.selectbox('Select Chemical:', list(chemicals.keys()))
min_Vw = st.slider('Min Vw (m/s):', 0.0, 20.0, 0.0, 0.1)
max_Vw = st.slider('Max Vw (m/s):', 0.0, 20.0, 20.0, 0.1)
min_Ta = st.slider('Min Ta (°F):', 0.0, 100.0, 0.0, 0.1)
max_Ta = st.slider('Max Ta (°F):', 0.0, 100.0, 100.0, 0.1)
min_As = st.slider('Min As (m²):', 0.0, 10.0, 0.0, 0.1)
max_As = st.slider('Max As (m²):', 0.0, 20.0, 10.0, 0.1)

if st.button('Calculate Generation Rate'):
    G_Rate = Chemical_Generation_Rate(min_Vw, max_Vw, min_Ta, max_Ta, min_As, max_As, chem_name)
    st.write('Generation Rate Calculated!')
    plt.figure(figsize=(10, 5))
    plt.hist(G_Rate, bins=50, alpha=0.7, color='blue', edgecolor='black', density=True)
    plt.xlabel("Generation Rate (G) (gm/min)")
    plt.ylabel("Density")
    plt.title("Distribution of the Generation Rate (G)")
    st.pyplot(plt)
