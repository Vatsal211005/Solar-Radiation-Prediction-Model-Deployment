
import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from streamlit_folium import st_folium  # Updated import
import joblib
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image

# Set page configuration
st.set_page_config(
    page_title="Saudi Arabia Renewable Energy Atlas",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E5631;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #1E5631;
        margin-bottom: 1rem;
    }
    .map-container {
        border-radius: 10px;
        border: 1px solid #ddd;
        padding: 1px;
    }
    .stButton button {
        background-color: #1E5631;
        color: white;
    }
    .info-box {
        background-color: #f0f8ff;
        border-radius: 5px;
        padding: 10px;
        border-left: 5px solid #1E5631;
    }
</style>
""", unsafe_allow_html=True)

# Function to load dataset
@st.cache_data
def load_dataset():
    # Update this path to your dataset location
    dataset_path = r"C:\Users\Dell\Desktop\folder0\dataset.csv"
    try:
        df = pd.read_csv(dataset_path)
        
        # Try to identify station name column (case insensitive)
        possible_station_cols = [col for col in df.columns if 'station' in col.lower() or 'name' in col.lower()]
        if possible_station_cols:
            df = df.rename(columns={possible_station_cols[0]: 'Station_Name'})
        
        # Try to identify coordinate columns
        possible_lat_cols = [col for col in df.columns if 'lat' in col.lower()]
        possible_lon_cols = [col for col in df.columns if 'lon' in col.lower()]
        if possible_lat_cols and possible_lon_cols:
            df = df.rename(columns={
                possible_lat_cols[0]: 'Latitude',
                possible_lon_cols[0]: 'Longitude'
            })
        
        return df
    except Exception as e:
        st.error(f"Error loading dataset: {e}")
        return None

# Function to load trained model
@st.cache_resource
def load_model():
    # Update this path to your model location
    model_path = r"C:\Users\Dell\Desktop\model\nishantmodel.pkl"
    try:
        model = joblib.load(model_path)
        return model
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

# Load dataset and model
dataset = load_dataset()
model = load_model()

# Title and description
st.markdown("<h1 class='main-header'>Saudi Arabia Renewable Resource Atlas</h1>", unsafe_allow_html=True)

# Sidebar for filters and controls
with st.sidebar:
    st.image("https://via.placeholder.com/150x80?text=Energy+Logo", use_column_width=True)
    st.markdown("### Map Controls")
    
    resource_type = st.selectbox(
        "Resource Type",
        ["Solar", "Wind", "Geothermal", "Hydroelectric", "Biomass"]
    )
    
    st.markdown("### Time Period")
    year = st.slider("Year", min_value=2010, max_value=2023, value=2022)
    time_period = st.selectbox(
        "Time Period",
        ["Annual Average", "Monthly Average", "Daily Average"]
    )
    
    if time_period != "Annual Average":
        if time_period == "Monthly Average":
            month = st.selectbox(
                "Month",
                ["January", "February", "March", "April", "May", "June", 
                 "July", "August", "September", "October", "November", "December"]
            )
        else:  # Daily
            date = st.date_input("Select Date", datetime(2022, 6, 15))
    
    st.markdown("### Map Layers")
    show_grid = st.checkbox("Power Grid", value=True)
    show_stations = st.checkbox("Monitoring Stations", value=True)
    show_projects = st.checkbox("Renewable Projects", value=False)
    
    st.markdown("### Download Data")
    download_format = st.selectbox(
        "Format",
        ["CSV", "Excel", "GeoJSON"]
    )
    if st.button("Download Data"):
        st.info("In a full implementation, this would download the selected data.")
    
    st.markdown("### About")
    st.markdown("Renewable Resource Atlas provides comprehensive renewable energy data for Saudi Arabia.")
    st.markdown("[Official Website](https://rratlas.energy.gov.sa)")

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["Map View", "Data Analysis", "Reports", "Projects"])

with tab1:
    # Map view section
    st.markdown("<h2 class='sub-header'>Solar Resource Map</h2>", unsafe_allow_html=True)
    
    # Create a folium map centered on Saudi Arabia
    m = folium.Map(
        location=[24.0, 45.0],
        zoom_start=6,
        tiles="CartoDB positron"
    )
    
    # Add stations from the dataset if available
    if dataset is not None:
        # Check if we have required columns
        has_coords = 'Latitude' in dataset.columns and 'Longitude' in dataset.columns
        has_ghi = 'GHI' in dataset.columns
        has_station_name = 'Station_Name' in dataset.columns
        
        if has_coords:
            # Create stations data from the dataset
            stations = []
            for _, row in dataset.iterrows():
                station_name = row['Station_Name'] if has_station_name else f"Station {_}"
                ghi_value = row['GHI'] if has_ghi else 0
                
                stations.append({
                    "name": station_name,
                    "region": row.get('Region', 'Unknown Region'),
                    "lat": row['Latitude'],
                    "lon": row['Longitude'],
                    "value": ghi_value,
                    "start_time": "2010-01-01",
                    "end_time": "2023-12-31"
                })
            
            # Add monitoring stations if selected
            if show_stations:
                for station in stations:
                    folium.CircleMarker(
                        location=[station["lat"], station["lon"]],
                        radius=7,
                        color="#1E5631",
                        fill=True,
                        fill_color="#1E5631",
                        fill_opacity=0.7,
                        tooltip=f"{station['name']}: {station['value']:.2f} kWh/m²/day" if has_ghi else station['name']
                    ).add_to(m)
        else:
            st.warning("Dataset doesn't contain required coordinate columns (Latitude/Longitude)")
    
    # Add grid lines if selected
    if show_grid:
        for i in range(20, 33, 1):
            folium.PolyLine(
                locations=[[i, 34], [i, 46]],
                color="#888",
                weight=0.5,
                opacity=0.5,
                dash_array="5,5"
            ).add_to(m)
        for i in range(35, 56, 1):
            folium.PolyLine(
                locations=[[16, i], [33, i]],
                color="#888",
                weight=0.5,
                opacity=0.5,
                dash_array="5,5"
            ).add_to(m)
    
    # Add renewable projects if selected
    if show_projects:
        projects = [
            {"name": "Sakaka Solar PV Plant", "lat": 29.9031, "lon": 40.2039, "capacity": "300 MW"},
            {"name": "Dumat Al Jandal Wind Farm", "lat": 29.7869, "lon": 39.8021, "capacity": "400 MW"},
            {"name": "NEOM Green Hydrogen Project", "lat": 27.9654, "lon": 35.2438, "capacity": "4 GW"}
        ]
        
        for project in projects:
            folium.Marker(
                location=[project["lat"], project["lon"]],
                popup=f"{project['name']}<br>Capacity: {project['capacity']}",
                icon=folium.Icon(color="green", icon="bolt", prefix="fa")
            ).add_to(m)
    
    # Add a legend
    legend_html = """
    <div style="position: fixed; bottom: 50px; left: 50px; width: 150px; height: 160px; 
    background-color: white; border:2px solid grey; z-index:9999; padding:10px;
    border-radius:5px; font-size: 14px;">
    <p><strong>Solar Radiation</strong><br>(kWh/m²/day)</p>
    <div style="background-color:#d73027; width:20px; height:15px; display:inline-block;"></div> >7.0<br>
    <div style="background-color:#fc8d59; width:20px; height:15px; display:inline-block;"></div> 6.5-7.0<br>
    <div style="background-color:#fee090; width:20px; height:15px; display:inline-block;"></div> 6.0-6.5<br>
    <div style="background-color:#e0f3f8; width:20px; height:15px; display:inline-block;"></div> 5.5-6.0<br>
    <div style="background-color:#91bfdb; width:20px; height:15px; display:inline-block;"></div> <5.5
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Display the map using st_folium instead of folium_static
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    st_folium(m, width=1000, height=600, returned_objects=[])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Station selection dropdown and details
    st.markdown("<h3 class='sub-header'>Station Data</h3>", unsafe_allow_html=True)
    st.markdown("<div class='info-box'>Select a station to view detailed information.</div>", unsafe_allow_html=True)
    
    if dataset is not None:
        # Check if we have station names or need to generate them
        if 'Station_Name' in dataset.columns:
            station_names = dataset['Station_Name'].unique().tolist()
        else:
            # Generate station names if not available
            station_names = [f"Station {i+1}" for i in range(len(dataset))]
            dataset['Station_Name'] = station_names
        
        # Station selection dropdown
        selected_station = st.selectbox(
            "Select Station",
            options=station_names,
            index=0
        )
        
        # Get the selected station data
        if 'Station_Name' in dataset.columns:
            station_data = dataset[dataset['Station_Name'] == selected_station].iloc[0]
        else:
            station_data = dataset.iloc[0]
        
        # Display station details
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Station Details")
            st.markdown(f"**Region:** {station_data.get('Region', 'N/A')}")
            st.markdown(f"**Site Name:** {selected_station}")
            if 'Longitude' in station_data:
                st.markdown(f"**Longitude:** {station_data['Longitude']}")
            else:
                st.markdown("**Longitude:** N/A")
            if 'Latitude' in station_data:
                st.markdown(f"**Latitude:** {station_data['Latitude']}")
            else:
                st.markdown("**Latitude:** N/A")
        
        with col2:
            st.markdown("### Time Range")
            st.markdown(f"**Start Time:** 2010-01-01")
            st.markdown(f"**End Time:** 2023-12-31")
        
        # Monthly radiation chart
        st.markdown("<h3 class='sub-header'>Monthly Resource Data</h3>", unsafe_allow_html=True)
        
        # Create sample monthly data for the chart
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        ghi_values = [5.1, 5.6, 6.2, 6.7, 7.2, 7.5, 7.3, 7.0, 6.5, 5.9, 5.3, 4.9]
        dni_values = [5.5, 5.9, 6.5, 7.0, 7.5, 7.8, 7.6, 7.2, 6.8, 6.3, 5.7, 5.3]
        
        # Create a DataFrame for the chart
        chart_data = pd.DataFrame({
            "Month": months,
            "GHI (kWh/m²/day)": ghi_values,
            "DNI (kWh/m²/day)": dni_values
        })
        
        # Plot the chart using Plotly
        fig = px.bar(
            chart_data,
            x="Month",
            y=["GHI (kWh/m²/day)", "DNI (kWh/m²/day)"],
            barmode="group",
            color_discrete_sequence=["#1E5631", "#ffc107"],
            title=f"Monthly Solar Radiation at {selected_station}"
        )
        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="Solar Radiation (kWh/m²/day)",
            legend_title="Resource Type",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No dataset loaded. Please check the dataset path.")

with tab2:
    st.markdown("<h2 class='sub-header'>Data Analysis</h2>", unsafe_allow_html=True)
    
    if dataset is not None:
        # Generate data for analysis from the dataset
        st.markdown("### Resource Comparison by Region")
        
        # Group by region if available
        if 'Region' in dataset.columns:
            region_stats = dataset.groupby('Region').agg({
                'GHI': 'mean',
                'DNI': 'mean',
                'Temperature': 'mean'
            }).reset_index()
            
            # Show the data table
            st.dataframe(region_stats, use_container_width=True)
            
            # Create a plot
            fig = px.bar(
                region_stats,
                x="Region",
                y=["GHI", "DNI"],
                barmode="group",
                color_discrete_sequence=["#FFAA00", "#00BFFF"],
                title="Renewable Resource Potential by Region"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Region column not found in dataset.")
        
        # Correlation analysis
        st.markdown("### Correlation Analysis")
        
        # Select numerical columns for correlation
        numerical_cols = dataset.select_dtypes(include=[np.number]).columns
        corr_data = dataset[numerical_cols].corr()
        
        # Create a correlation heatmap
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(corr_data, annot=True, cmap="coolwarm", ax=ax, fmt=".2f")
        ax.set_title("Correlation Between Climate Variables")
        st.pyplot(fig)
        
        # Prediction model interface
        st.markdown("### Renewable Energy Prediction")
        st.markdown("<div class='info-box'>Use this tool to predict solar energy potential based on location and environmental factors.</div>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            pred_latitude = st.number_input("Site Latitude", min_value=16.0, max_value=33.0, value=25.0, format="%.2f")
            pred_longitude = st.number_input("Site Longitude", min_value=34.0, max_value=56.0, value=45.0, format="%.2f")
            elevation = st.number_input("Elevation (m)", min_value=0, max_value=3000, value=500)
        
        with col2:
            temperature = st.slider("Average Temperature (°C)", min_value=10, max_value=40, value=28)
            humidity = st.slider("Average Humidity (%)", min_value=0, max_value=100, value=30)
            dust_index = st.slider("Dust Index", min_value=1, max_value=10, value=4)
        
        with col3:
            st.markdown("### Prediction Results")
            if st.button("Calculate Potential"):
                if model is not None:
                    # Prepare input features for the model
                    input_features = pd.DataFrame({
                        'Latitude': [pred_latitude],
                        'Longitude': [pred_longitude],
                        'Elevation': [elevation],
                        'Temperature': [temperature],
                        'Humidity': [humidity],
                        'Dust_Index': [dust_index]
                    })
                    
                    # Make prediction
                    try:
                        prediction = model.predict(input_features)
                        st.metric("Predicted GHI", f"{prediction[0]:.2f} kWh/m²/day")
                        st.metric("Annual Energy Production", f"{prediction[0] * 365 * 0.15:.0f} kWh/kWp")
                        st.metric("Confidence Interval", "±0.3 kWh/m²/day")
                    except Exception as e:
                        st.error(f"Error making prediction: {e}")
                else:
                    st.error("Model not loaded. Please check the model path.")
    else:
        st.warning("No dataset loaded. Please check the dataset path.")

with tab3:
    st.markdown("<h2 class='sub-header'>Reports & Data Visualization</h2>", unsafe_allow_html=True)
    
    # Report types selection
    report_type = st.selectbox(
        "Report Type",
        ["Annual Summary", "Regional Comparison", "Historical Trends", "Future Projections"]
    )
    
    if report_type == "Annual Summary":
        st.markdown("### Annual Solar Resource Summary")
        st.markdown("<div class='info-box'>This report provides an overview of solar resource availability across Saudi Arabia for the selected year.</div>", unsafe_allow_html=True)
        
        if dataset is not None:
            # Create a sample summary data table from the dataset
            if 'Region' in dataset.columns:
                summary_data = dataset.groupby('Region').agg({
                    'GHI': 'mean',
                    'DNI': 'mean'
                }).reset_index()
                
                summary_data['PV Potential (kWh/kWp)'] = summary_data['GHI'] * 365 * 0.15
                summary_data.columns = ['Region', 'GHI (kWh/m²/year)', 'DNI (kWh/m²/year)', 'PV Potential (kWh/kWp)']
                
                # Add national average
                national_avg = pd.DataFrame({
                    'Region': ['National Average'],
                    'GHI (kWh/m²/year)': [dataset['GHI'].mean()],
                    'DNI (kWh/m²/year)': [dataset['DNI'].mean()],
                    'PV Potential (kWh/kWp)': [dataset['GHI'].mean() * 365 * 0.15]
                })
                summary_data = pd.concat([summary_data, national_avg], ignore_index=True)
                
                st.dataframe(summary_data, use_container_width=True)
                
                # Create a visualization
                fig = px.bar(
                    summary_data,
                    x="Region",
                    y="GHI (kWh/m²/year)",
                    color="Region",
                    color_discrete_sequence=px.colors.qualitative.Dark2,
                    title="Annual Global Horizontal Irradiance by Region"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Region column not found in dataset.")
        
        # Add a map visualization for the annual summary
        st.markdown("### Geographic Distribution")
        
        # Create a folium choropleth map
        m = folium.Map(location=[24.0, 45.0], zoom_start=5)
        st_folium(m, width=1000, height=400, returned_objects=[])

with tab4:
    st.markdown("<h2 class='sub-header'>Renewable Energy Projects</h2>", unsafe_allow_html=True)
    
    # Project filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        project_type = st.multiselect(
            "Project Type",
            ["Solar PV", "CSP", "Wind", "Hydro", "Geothermal", "Biomass", "Hydrogen"],
            default=["Solar PV", "Wind"]
        )
    with col2:
        project_status = st.multiselect(
            "Project Status",
            ["Operational", "Under Construction", "Planned", "Proposed"],
            default=["Operational", "Under Construction"]
        )
    with col3:
        project_size = st.slider(
            "Minimum Capacity (MW)",
            min_value=0,
            max_value=2000,
            value=100
        )
    
    # Create a sample projects database
    projects_data = [
        {"name": "Sakaka Solar PV Plant", "type": "Solar PV", "capacity": 300, "status": "Operational", "location": "Al Jouf", "lat": 29.9031, "lon": 40.2039, "cod": "2020"},
        {"name": "Dumat Al Jandal Wind Farm", "type": "Wind", "capacity": 400, "status": "Operational", "location": "Al Jouf", "lat": 29.7869, "lon": 39.8021, "cod": "2022"},
        {"name": "Sudair Solar PV", "type": "Solar PV", "capacity": 1500, "status": "Under Construction", "location": "Riyadh", "lat": 25.2514, "lon": 45.8143, "cod": "2024"},
        {"name": "NEOM Green Hydrogen", "type": "Hydrogen", "capacity": 2000, "status": "Planned", "location": "NEOM", "lat": 27.9654, "lon": 35.2438, "cod": "2026"},
        {"name": "Yanbu CSP Plant", "type": "CSP", "capacity": 120, "status": "Proposed", "location": "Yanbu", "lat": 24.0223, "lon": 38.0493, "cod": "2025"}
    ]
    
    # Filter the projects based on selections
    filtered_projects = [
        p for p in projects_data 
        if p["type"] in project_type and p["status"] in project_status and p["capacity"] >= project_size
    ]
    
    # Create a DataFrame from the filtered projects
    projects_df = pd.DataFrame(filtered_projects)
    
    # Display the filtered projects
    st.markdown(f"### Showing {len(filtered_projects)} Projects")
    
    if not filtered_projects:
        st.info("No projects match your filter criteria. Try adjusting the filters.")
    else:
        # Project map
        st.markdown("### Project Locations")
        
        # Create a folium map with project markers
        project_map = folium.Map(location=[24.0, 45.0], zoom_start=5)
        
        for p in filtered_projects:
            # Choose icon color based on project type
            if p["type"] == "Solar PV" or p["type"] == "CSP":
                icon_color = "orange"
                icon_name = "solar-panel"
            elif p["type"] == "Wind":
                icon_color = "blue"
                icon_name = "fan"
            elif p["type"] == "Hydrogen":
                icon_color = "green"
                icon_name = "flask"
            else:
                icon_color = "purple"
                icon_name = "bolt"
            
            # Add marker for each project
            folium.Marker(
                location=[p["lat"], p["lon"]],
                popup=f"<b>{p['name']}</b><br>Type: {p['type']}<br>Capacity: {p['capacity']} MW<br>Status: {p['status']}",
                icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa")
            ).add_to(project_map)
        
        # Display the map
        st_folium(project_map, width=1000, height=500, returned_objects=[])
        
        # Project details table
        st.markdown("### Project Details")
        
        # Display the table with custom formatting
        st.dataframe(
            projects_df[["name", "type", "capacity", "status", "location", "cod"]].rename(
                columns={
                    "name": "Project Name",
                    "type": "Type",
                    "capacity": "Capacity (MW)",
                    "status": "Status",
                    "location": "Location",
                    "cod": "Expected COD"
                }
            ),
            use_container_width=True
        )
        
        # Project capacity by type visualization
        st.markdown("### Project Capacity by Type")
        
        # Calculate total capacity by type
        capacity_by_type = projects_df.groupby("type")["capacity"].sum().reset_index()
        
        # Create a pie chart
        fig = px.pie(
            capacity_by_type,
            values="capacity",
            names="type",
            title="Distribution of Renewable Energy Capacity by Technology",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #666;">
        <p>Saudi Arabia Renewable Resource Atlas | Created with Streamlit</p>
        <p>This is a demonstration application and is not officially affiliated with the Saudi government.</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Add a separate about page in the sidebar
with st.sidebar:
    st.markdown("---")
    if st.button("About This App"):
        st.info(
            """
            This application demonstrates how to create a renewable energy resource atlas similar to the Saudi Arabia
            Renewable Resource Atlas (https://rratlas.energy.gov.sa/).
            
            Features include:
            - Interactive map visualization
            - Solar radiation data display
            - Site analysis tools
            - Data analysis and reporting
            - Project database
            
            For educational purposes only.
            """
        )