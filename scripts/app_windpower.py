import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from utils.data import open_opendap_dataset
from utils.geo import load_country_borders, get_border_lines

# App title
st.set_page_config(page_title="Wind Power Forecast Explorer", layout="centered")
st.title("Wind Power Forecast Explorer⚡")

st.markdown("""
Plan and visualize wind power production potential at wind park locations  
Upload wind park coordinates and turbine specs, and explore **wind speed** and **power output** forecasts interactively.
""")

# ---- Features ----
st.markdown("""
### How it Works:
1. **Upload Wind Park Table:** Provide your wind parks as a CSV or Excel file with required columns.
2. **Visualize Forecasts:**  
   - **Map Overlay:** Always visible map showing wind power potential (at 10m height).
   - **Time Series:** Track wind speed and power output at each park.
3. **Decision Support:** Use the visualizations to anticipate production and optimize operations.
""")

# ---- Optional Tips ----
st.info("""
💡 **Tips:**  
- Required columns: `Longitude`, `Latitude`, `RotorRadius_m`, `RatedPower_kW`, `CutInWind_mps`, `RatedWind_mps`, `CutoffWind_mps`  
- Optional columns: `TurbineHeight`, `WindShear`, `Efficiency`  
- Wind speeds are converted from 10m to hub height using the power law.
- Efficiency defaults to 0.45 if not provided.
""")

# ---- Example Table ----
st.markdown("#### Example Excel/CSV Format")
example = pd.DataFrame({
    "Longitude": [10.0, 11.5],
    "Latitude": [60.0, 61.2],
    "RotorRadius_m": [50, 60],
    "RatedPower_kW": [3000, 3500],
    "CutInWind_mps": [3.5, 3.0],
    "RatedWind_mps": [12.0, 11.5],
    "CutoffWind_mps": [25.0, 25.0],
    "TurbineHeight": [100, 120],
    "WindShear": [0.14, 0.16],
    "Efficiency": [0.45, 0.44]
})
st.dataframe(example, use_container_width=True)

# loading data
@st.cache_data
def load_data():
    url = "https://thredds.met.no/thredds/dodsC/metpplatest/met_forecast_1_0km_nordic_latest.nc"
    ds = open_opendap_dataset(url)
    return ds

ds = load_data()

# Preparing data for map
stride = 20 # Cant plot all coordinates as its heavy processing task. So, plotting only every 20th point. 
num_frames = 47 # get first n forecasts 
rho0 = 1.225
R = 287.05

wind = ds['wind_speed_10m'].isel(time=slice(0, num_frames)).values  # (t, y, x)
temp = ds['air_temperature_2m'].isel(time=slice(0, num_frames)).values
pres = ds['air_pressure_at_sea_level'].isel(time=slice(0, num_frames)).values
lat = ds['latitude'].values
lon = ds['longitude'].values

wind = wind[:, ::stride, ::stride]
temp = temp[:, ::stride, ::stride]
pres = pres[:, ::stride, ::stride]
lat_sub = lat[::stride, ::stride]
lon_sub = lon[::stride, ::stride]

# Filter longitude between 0 and 30 for plotting
lon_mask = (lon_sub >= 0) & (lon_sub <= 30)
lat_mask = np.any(lon_mask, axis=1)
lon_mask_any = np.any(lon_mask, axis=0)

lat_sub_plot = lat_sub[lat_mask][:, lon_mask_any]
lon_sub_plot = lon_sub[lat_mask][:, lon_mask_any]
wind = wind[:, lat_mask][:, :, lon_mask_any]
temp = temp[:, lat_mask][:, :, lon_mask_any]
pres = pres[:, lat_mask][:, :, lon_mask_any]

rho = pres / (R * temp)
wind_power = 0.5 * rho * wind**3  # (t, y, x)

# Country borders
shapefile_path = r"data/ne_10m_admin_0_countries.zip"
world = load_country_borders(
    shapefile_path,
    bbox=(lon_sub_plot.min(), lat_sub_plot.min(), lon_sub_plot.max(), lat_sub_plot.max())
)
border_x, border_y = get_border_lines(world)

# --- Animation: Wind Power Potential Map ---
st.markdown("### Wind Power Potential Map (at 10m height)")
times = pd.to_datetime(ds['time'].values[:num_frames])

frames = []
for t_idx in range(num_frames):
    z = wind_power[t_idx]
    frame = go.Frame(
        data=[
            go.Heatmap(
                z=z,
                x=lon_sub_plot[0, :],
                y=lat_sub_plot[:, 0],
                colorscale="YlGnBu",
                zmin=0,
                zmax=np.nanpercentile(wind_power, 99),
                colorbar=dict(
                    title="W/m²",
                    len=1,
                    thickness=30,
                    y=0.5
                ),
                hovertemplate="Lon: {x:.2f}<br>Lat: {y:.2f}<br>Wind Power: {z:.1f} W/m²<extra></extra>",
                showscale=True,
                opacity=0.7
            ),
            go.Scatter(
                x=border_x,
                y=border_y,
                mode='lines',
                line=dict(color='black', width=1),
                showlegend=False,
                hoverinfo='skip'
            )
        ],
        name=str(t_idx)
    )
    frames.append(frame)

# initial frame
z0 = wind_power[0]
fig = go.Figure(
    data=[
        go.Heatmap(
            z=z0,
            x=lon_sub_plot[0, :],
            y=lat_sub_plot[:, 0],
            colorscale="YlGnBu",
            zmin=0,
            zmax=np.nanpercentile(wind_power, 99),
            colorbar=dict(
                title="W/m²",
                len=0.8,
                thickness=20,
                y=0.5
            ),
            hovertemplate="Lon: {x:.2f}<br>Lat: {y:.2f}<br>Wind Power: {z:.1f} W/m²<extra></extra>",
            showscale=True,
            opacity=0.7
        ),
        go.Scatter(
            x=border_x,
            y=border_y,
            mode='lines',
            line=dict(color='black', width=1),
            showlegend=False,
            hoverinfo='skip'
        )
    ],
    layout=go.Layout(
        height=600, width=600,
        margin={"r":0,"t":0,"l":0,"b":0},
        xaxis_title="Longitude",
        yaxis_title="Latitude",
        plot_bgcolor="white",
        xaxis=dict(range=[0, 30]),
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                y=-0.18,
                x=0, #.5
                xanchor="center",
                yanchor="top",
                direction="left",
                buttons=[
                    dict(label="Play",
                         method="animate",
                         args=[None, {"frame": {"duration": 700, "redraw": True},
                                      "fromcurrent": True, "transition": {"duration": 0}}]),
                    dict(label="Pause",
                         method="animate",
                         args=[[None], {"frame": {"duration": 0, "redraw": False},
                                        "mode": "immediate",
                                        "transition": {"duration": 0}}])
                ]
            )
        ],
        sliders=[{
            "steps": [
                {
                    "args": [
                        [str(k)],
                        {"frame": {"duration": 0, "redraw": True},
                         "mode": "immediate",
                         "transition": {"duration": 0}}
                    ],
                    "label": times[k].strftime("%Y-%m-%d %H:%M"),
                    "method": "animate"
                }
                for k in range(num_frames)
            ],
            "transition": {"duration": 0},
            "x": 0.1,
            "y": -0.08,
            "currentvalue": {
                "prefix": "Forecast time: ",
                "visible": True,
                "xanchor": "right"
            },
            "len": 0.8
        }]
    ),
    frames=frames
)
st.plotly_chart(fig)

# Upload wind park coordinates
st.markdown("### Upload Wind Park Coordinates and Turbine Specs")
uploaded_file = st.file_uploader(
    "Upload Excel or CSV file with required columns (see example above)",
    type=["xlsx", "csv"]
)

if uploaded_file is not None:
    if uploaded_file.name.endswith(".xlsx"):
        df_parks = pd.read_excel(uploaded_file)
    else:
        df_parks = pd.read_csv(uploaded_file)
    # Convert to numeric
    df_parks["Latitude"] = pd.to_numeric(df_parks["Latitude"], errors="coerce")
    df_parks["Longitude"] = pd.to_numeric(df_parks["Longitude"], errors="coerce")
    st.success("Wind park coordinates uploaded!")
    st.dataframe(df_parks)

    # Set default values if not provided (except rotor radius and rated power)
    default_turbine_height = 100  # meters
    default_windshear = 0.14
    default_efficiency = 0.45  # Typical efficiency factor

    if "TurbineHeight" not in df_parks:
        df_parks["TurbineHeight"] = default_turbine_height
    if "WindShear" not in df_parks:
        df_parks["WindShear"] = default_windshear
    if "Efficiency" not in df_parks:
        df_parks["Efficiency"] = default_efficiency

    # Check for required columns
    required_cols = ["RotorRadius_m", "RatedPower_kW", "CutInWind_mps", "RatedWind_mps", "CutoffWind_mps"]
    missing_cols = [col for col in required_cols if col not in df_parks]
    if missing_cols:
        st.error(f"Please include columns {missing_cols} in your upload.")
    else:
        # Calculate rotor area from radius
        df_parks["RotorArea_m2"] = np.pi * df_parks["RotorRadius_m"] ** 2

        # Extract wind forecast for each park for all frames
        results = []
        for idx, row in df_parks.iterrows():
            park_lat = row["Latitude"]
            park_lon = row["Longitude"]
            turbine_height = row["TurbineHeight"]
            windshear = row["WindShear"]
            rotor_area = row["RotorArea_m2"]
            rated_power = row["RatedPower_kW"]
            cut_in = row["CutInWind_mps"]
            rated_wind = row["RatedWind_mps"]
            cut_off = row["CutoffWind_mps"]
            efficiency = row["Efficiency"]

            # Find nearest grid point
            dist = np.sqrt((lat - park_lat)**2 + (lon - park_lon)**2)
            y_idx, x_idx = np.unravel_index(np.argmin(dist), dist.shape)
            windspeed_series_10m = ds['wind_speed_10m'].isel(y=y_idx, x=x_idx, time=slice(0, num_frames)).values

            # Convert wind speed to turbine height using power law
            windspeed_series_hub = windspeed_series_10m * (turbine_height / 10) ** windshear

            # Calculate air density at site (optional, use 1.225 kg/m³ if not available)
            try:
                temp_series = ds['air_temperature_2m'].isel(y=y_idx, x=x_idx, time=slice(0, num_frames)).values
                pres_series = ds['air_pressure_at_sea_level'].isel(y=y_idx, x=x_idx, time=slice(0, num_frames)).values
                R = 287.05
                rho_series = pres_series / (R * temp_series)
            except Exception:
                rho_series = np.full_like(windspeed_series_hub, 1.225)

            # Calculate wind power at hub height
            windpower_series = 0.5 * rho_series * rotor_area * windspeed_series_hub**3  # in Watts

            # Apply efficiency
            windpower_series = windpower_series * efficiency

            # Calculate actual power output (limit by cut-in, rated, and cut-off wind speeds)
            power_output_series = []
            for ws, wp in zip(windspeed_series_hub, windpower_series):
                if ws < cut_in or ws > cut_off:
                    power_output_series.append(0)
                elif ws >= rated_wind:
                    power_output_series.append(rated_power)
                else:
                    power_output_series.append(min(wp / 1000, rated_power))  # in kW

            for t_idx in range(len(windspeed_series_hub)):
                results.append({
                    "Park": f"Park {idx+1}",
                    "Longitude": park_lon,
                    "Latitude": park_lat,
                    "Forecast Time": times[t_idx],
                    "Wind Speed 10m (m/s)": windspeed_series_10m[t_idx],
                    f"Wind Speed {int(turbine_height)}m (m/s)": windspeed_series_hub[t_idx],
                    "Power Output (kW)": power_output_series[t_idx]
                })
        df_results = pd.DataFrame(results)

        # Plot power output time series plot
        st.markdown("### Power Output Time Series at Wind Park Locations")
        fig_ts_power = go.Figure()
        for park, group in df_results.groupby("Park"):
            fig_ts_power.add_trace(go.Scatter(
                x=group["Forecast Time"],
                y=group["Power Output (kW)"],
                mode="lines+markers",
                name=park
            ))
        fig_ts_power.update_layout(
            xaxis_title="Forecast Time",
            yaxis_title="Power Output (kW)",
            legend_title="Wind Park",
            height=400,
            margin={"r":20,"t":40,"l":0,"b":0},
            plot_bgcolor="white"
        )
        st.plotly_chart(fig_ts_power, use_container_width=True)

        # Plot wind speed time series plot
        st.markdown("### Wind Speed Time Series at Wind Park Locations")
        windspeed_col = [col for col in df_results.columns if col.startswith("Wind Speed") and col.endswith("m (m/s)")]
        yaxis_label = windspeed_col[0] if windspeed_col else "Wind Speed (m/s)"
        fig_ts_ws = go.Figure()
        for park, group in df_results.groupby("Park"):
            fig_ts_ws.add_trace(go.Scatter(
                x=group["Forecast Time"],
                y=group[yaxis_label],
                mode="lines+markers",
                name=park
            ))
        fig_ts_ws.update_layout(
            xaxis_title="Forecast Time",
            yaxis_title=yaxis_label,
            legend_title="Wind Park",
            height=400,
            margin={"r":20,"t":40,"l":0,"b":0},
            plot_bgcolor="white"
        )
        st.plotly_chart(fig_ts_ws, use_container_width=True)

    # About Section
    st.markdown("---")
    st.subheader("About This Tool")
    st.markdown("""
This tool provides interactive visualizations of potential wind power productions across Northern Europe using forecast data from the MEPS model. The tool aims to support decision-making for wind energy investments and operations.
                The visualizations include time series plots of wind speed and power output at specific wind park locations. Getting historical power production data could help in using Machine Learning models and AI for better forecasting. 
                The wind forecast itself could be enhanced using data from GNSS. 
""")
    st.markdown("#### Data Sources:")
    st.markdown("""
- **Wind speed data:** Forecast from MepsCoOp by MET Norway.
- **Thredds data:** [MetCoOp Ensemble Prediction System (MEPS)](https://thredds.met.no/thredds/catalog/metpplatest/catalog.html)
""")
    st.markdown("#### Packages used:")
    st.markdown("""
- **Streamlit:** For the framework to build interactive web apps easily.
- **Plotly:** For the powerful graphing library to create interactive plots.
- **Xarray, Pandas, NumPy:** For the essential data handling and numerical computing capabilities.
""")

else:
    st.info("Upload your wind park coordinates to see site-specific forecasts")