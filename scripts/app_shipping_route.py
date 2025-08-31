import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import xarray as xr
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.data import open_opendap_dataset, get_gfs_wave_opendap_url,get_latest_gfs_cycle

# Headers
st.set_page_config(page_title="Voyage Weather & Wave Planner", layout="centered")
st.title("Voyage Weather & Wave Planner⛴️ 🌊 ")

# Short Description
st.markdown("""
Plan and visualize environmental conditions along your shipping route!  
Upload your route, set the voyage start time, and explore **wind speed** and **significant wave height** forecasts interactively.
""")

# Features
st.markdown("""
### How it Works:
1. **Upload Route Table:** Provide your voyage as a CSV or table of latitude and longitude points.
2. **Set Departure Time:** Choose the start time of your voyage to align forecasts along the route.
3. **Visualize Forecasts:**  
   - **Map Overlay:** Interactive map showing wind speed and significant wave height along your route.  
   - **Time Series:** Track conditions at each point throughout the voyage.
4. **Decision Support:** Use the visualizations to anticipate challenging conditions and optimize route planning.
""")

# ---- Optional Tips ----
st.info("""
💡 Tips and directions:  
- Ensure your table has columns: `Longitude`, `Latitude`, `Time` (hours from start).  
- Departure time should be in UTC for accurate forecast alignment.  
- You can hover on map points to see time-specific forecasts.
""")

# Loads the latest GFS Wave Data
cycle = get_latest_gfs_cycle()
opendap_url = get_gfs_wave_opendap_url(datetime.utcnow(), cycle) # Get the OPeNDAP URL for the latest cycle
print(f"Using GFS OPeNDAP URL: {opendap_url}")
# Loading data
ds = open_opendap_dataset(opendap_url) 

# Upload Excel File with Waypoints
st.markdown("#### 1. Upload Route Table")
uploaded_file = st.file_uploader("Upload Excel file with columns: Longitude, Latitude, Time (hours from start)", type=["xlsx"])

if uploaded_file is not None:
    df_waypoints = pd.read_excel(uploaded_file)
    st.success("Route uploaded successfully!")
    st.write("Preview of uploaded waypoints:")
    st.dataframe(df_waypoints.head(), use_container_width=True)

    # Select starting time from forecast times
    forecast_times = pd.to_datetime(ds['time'].values)
    st.markdown("#### 2. Set Departure Time")
    st.markdown("Select the UTC starting time for your voyage:")
    forecast_time_options = forecast_times[:10]
    selected_start_time = st.selectbox(
        "Departure time (UTC):",
        forecast_time_options,
        format_func=lambda t: t.strftime("%Y-%m-%d %H:%M")
    )

    # Compute absolute times for each waypoint
    abs_times = [
        selected_start_time + pd.Timedelta(hours=float(h))
        for h in df_waypoints["Time"]
    ]
    df_waypoints["AbsTime"] = abs_times
    waypoints = df_waypoints.to_dict(orient="records")
else:
    st.warning("Please upload an Excel file with columns: Longitude, Latitude, Time (hours from start)")
    # Show example table
    example = pd.DataFrame({
        "Longitude": [60.1699, 59.8, 59.4, 59, 58.5, 53.5511],
        "Latitude": [24.9384, 25.2, 25.5, 26, 26.5, 9.9937],
        "Time": [0, 2, 4, 6, 8, 42]
    })
    st.write("**Example format:**")
    st.dataframe(example, use_container_width=True)
    waypoints = []

# Extract Data for each checkpoint
results = []
for wp in waypoints:
    try:
        t_idx = np.argmin(np.abs(ds['time'].values - np.datetime64(wp['AbsTime'])))
        lat_idx = np.argmin(np.abs(ds['lat'].values - wp['Latitude']))
        lon_idx = np.argmin(np.abs(ds['lon'].values - wp['Longitude']))
        wind = float(ds['windsfc'].isel(time=t_idx, lat=lat_idx, lon=lon_idx).values)
        wave = float(ds['htsgwsfc'].isel(time=t_idx, lat=lat_idx, lon=lon_idx).values)
        results.append({
            "Longitude": wp['Longitude'],
            "Latitude": wp['Latitude'],
            "Arrival Time": wp['AbsTime'],
            "Wind Speed (m/s)": wind,
            "Wave Height (m)": wave
        })
    except Exception as e:
        results.append({
            "Longitude": wp.get('Longitude', 'N/A'),
            "Latitude": wp.get('Latitude', 'N/A'),
            "Arrival Time": wp.get('AbsTime', 'N/A'),
            "Wind Speed (m/s)": "N/A",
            "Wave Height (m)": "N/A"
        })

df = pd.DataFrame(results)

# Visualization
if not df.empty:
    st.markdown("#### 3. Visualize Forecasts")

    # Map Overlay Option
    map_var = st.radio(
        "Select variable to visualize on the map:",
        options=["Wind Speed (m/s)", "Wave Height (m)"],
        index=0,
        horizontal=True
    )
    color_col = "Wind Speed (m/s)" if map_var == "Wind Speed (m/s)" else "Wave Height (m)"
    colorbar_title = "Wind (m/s)" if map_var == "Wind Speed (m/s)" else "Wave Height (m)"

    # --- Map Plot ---
    st.markdown(f"**Map Overlay:** {map_var} (color) and route points")
    fig = go.Figure()
    fig.add_trace(go.Scattergeo(
        lon=df["Longitude"], lat=df["Latitude"],
        mode='markers+text',
        marker=dict(
            size=12,
            color=df[color_col],
            colorscale='Viridis',
            colorbar=dict(
                title=colorbar_title,
                len=.9,
                thickness=30,
                y=0.5
            )
        ),
        text=[f"{w:.1f}" if isinstance(w, float) else "N/A" for w in df[color_col]],
        textposition="top center",
        showlegend=False
    ))
    fig.update_geos(
        projection_type="natural earth",
        showcoastlines=True, showland=True, showcountries=True,
        lataxis_range=[min(df["Latitude"])-5, max(df["Latitude"])+5],
        lonaxis_range=[min(df["Longitude"])-5, max(df["Longitude"])+5]
    )
    fig.update_layout(
        height=500, width=700, margin={"r":0,"t":0,"l":0,"b":0},
        plot_bgcolor="white"
    )
    st.plotly_chart(fig, use_container_width=False)

    # Time Series Plot
    st.markdown("**Time Series:** Wind speed and significant wave height along the route")
    fig_ts = go.Figure()
    fig_ts.add_trace(go.Scatter(
        x=df["Arrival Time"], y=df["Wind Speed (m/s)"],
        mode='lines+markers', name='Wind Speed (m/s)', line=dict(color='royalblue')
    ))
    fig_ts.add_trace(go.Scatter(
        x=df["Arrival Time"], y=df["Wave Height (m)"],
        mode='lines+markers', name='Wave Height (m)', line=dict(color='darkorange'), yaxis='y2'
    ))
    fig_ts.update_layout(
        #title="Time Series of Wind Speed and Significant Wave Height",
        xaxis_title="Arrival Time",
        yaxis=dict(
            title=dict(text="Wind Speed (m/s)", font=dict(color='royalblue')),
            tickfont=dict(color='royalblue'),
            linecolor='royalblue',
            linewidth=2
        ),
        yaxis2=dict(
            title=dict(text="Wave Height (m)", font=dict(color='darkorange')),
            tickfont=dict(color='darkorange'),
            linecolor='darkorange',
            linewidth=2,
            overlaying='y',
            side='right'
        ),
        legend=dict(
            x=1.02,
            y=1,
            xanchor="left",
            yanchor="top",
            orientation="v"
        ),
        height=350,
        margin={"r":80,"t":40,"l":0,"b":0},
        plot_bgcolor="white"
    )
    st.plotly_chart(fig_ts, use_container_width=True)

    st.markdown("#### 4. Wind and Wave Conditions Table")
    st.dataframe(df, use_container_width=True)

    # About Section
    st.markdown("---")
    st.subheader("About This Tool")
    st.markdown("""
This tool provides interactive visualizations of wind and wave conditions for maritime routes, using forecast data from the GFS model. There are several other
                enhancements possible such as, real-time shipping routes, additional environmental variables, route analysis and decision support for specific types of ships.
""")
    st.markdown("#### Data Sources:")
    st.markdown("""
- **GFS Wave Data:** Global Forecast System data for wind and wave forecasts.
- **NOAA NOMADS:** [NCEP Operational Model Archive and Distribution System](http://nomads.ncep.noaa.gov)
""")
    st.markdown("#### Acknowledgements:")
    st.markdown("""
- **Streamlit:** For the framework to build interactive web apps easily.
- **Plotly:** For the powerful graphing library to create interactive plots.
- **Xarray, Pandas, NumPy:** For the essential data handling and numerical computing capabilities.
""")
else:
    st.info("Upload your route data to get started!")



