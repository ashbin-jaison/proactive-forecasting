# Proactive Forecast Visualisations, Wind Power & Shipping Route Forecasting

This project provides an interactive platform for exploring wind power forecasts at user-specified wind park locations **and along shipping routes**.  
It **streams the latest forecast data from GFS and MEPS** (directly from MET Norway’s THREDDS servers) and makes interactive visualizations for decision making.

## Features

- **🚀 Live Forecast Data** 
Always fetches the latest GFS and MEPS forecasts, therefore no manual downloads needed.

- **🌪️ Weather Visualizations from GFS & MEPS** 
Interactive maps of wind speed, precipitation, and cloud cover for each forecast time step.

- **🗺️ Wind Power Potential Maps** 
Animated spatial maps of wind power potential across the Nordic region, with time navigation and country borders.

- **⚡ Custom Wind Park Forecasts** 
Upload wind park coordinates and turbine specs. The app extracts and visualizes wind speed & power output forecasts for each site.

- **⛴️ Shipping Route Forecasts** 
Upload shipping routes (waypoints). View wind speed, wind direction, and other weather variables along the path at each forecast timestep.

- **📊 Time Series Visualization** 
Generate time series plots of wind speed, turbine output, and weather conditions along routes.

- **⚙️ Flexible Turbine Parameters** 
Supports hub height, rotor radius, rated power, cut-in/rated/cutoff wind speeds, wind shear exponent, and efficiency.

- **📏 Automatic Hub-Height Adjustment** 
Wind speeds at 10 m are scaled to turbine hub height using the power law.


## Example Input Files
Sample input data is given is **sample_app_upload_data/**
### Wind Parks

| Longitude | Latitude | RotorRadius_m | RatedPower_kW | CutInWind_mps | RatedWind_mps | CutoffWind_mps | TurbineHeight | WindShear | Efficiency |
|-----------|----------|---------------|---------------|---------------|---------------|----------------|---------------|-----------|------------|
| 10.0      | 60.0     | 50            | 3000          | 3.5           | 12.0          | 25.0           | 100           | 0.14      | 0.45       |
| 11.5      | 61.2     | 60            | 3500          | 3.0           | 11.5          | 25.0           | 120           | 0.16      | 0.44       |

### Shipping Routes

| Longitude | Latitude | Time |
|-----------|----------|------|
| 5.0       | 60.0     | 0    |
| 10.0      | 62.0     | 1    |
| 15.0      | 64.0     | 3    |
| 7.0       | 58.0     | 7    |
| 12.0      | 59.5     | 31   |

**Required columns for wind parks:**  
- `Longitude`, `Latitude`, `RotorRadius_m`, `RatedPower_kW`, `CutInWind_mps`, `RatedWind_mps`, `CutoffWind_mps`  
**Optional columns:**  
- `TurbineHeight`, `WindShear`, `Efficiency` (defaults will be used if omitted)

**Required columns for shipping routes:**  
- `RouteName`, `Longitude`, `Latitude`

## How to Run

1. **Install requirements:**  
   ```
   pip install -r requirements.txt
   ```

2. **run the Streamlit app and visualisations:**  
   ```
   streamlit run scripts/app_windpower.py #for windpower potential forecasts
   streamlit run scripts/app_shipping_route.py #for weather forecast in shipping routes

   python scripts/gfs_atmos_animations.py # To visualise atmospheric variables (wind, precipitation, cloud cover) from GFS
   python scripts/gfs_ocean_wave.py # To visualise oceanic variables (wind, significant wave height) from GFS
   python scripts/meps_atmos_animations.py # To visualise atmospheric variables (wind, precipitation, cloud cover) from MEPS
   ```

3. **Upload your wind park and/or shipping route files** and explore the forecasts. 

## Data Sources

- Regional forecast data: [MET Norway THREDDS](https://thredds.met.no/thredds/catalog.html)  
  Postprocessed MEPS hourly forecasts which is updated every hour. Data contains forecasts of 15 key variables and gives forecasts for t+58h
- Global forecast data: [GFS](https://nomads.ncep.noaa.gov/). 3-hour time stepped forecasts, initiated 4 times a day. Forecasts more than 200 atmospheric variables with 16-day lead time.
- Country borders: [Natural Earth](https://www.naturalearthdata.com/)

## Project Structure

```
scripts/
    app_windpower.py         # Streamlit app for windpower estimation (uses MEPS forecast for fine resolution forecasts of atmospheric variables)
    app_shipping_route.py    # Streamlit app for weather forecast along shipping routes (uses GFS for longer forecast times and spatial coverage) 
    gfs_atmos_animations.py  # GFS plots for atmoshpheric variables
    gfs_ocean_wave.py        # GFS plots for ocean variables, mainly significant wave height
    meps_atmos_animations.py # MEPS plots for atmospheric variables
utils/
    data.py                  # Data access utilities
    plot.py                  # Plotting utilities
    geo.py                   # Geospatial utilities
```

## Acknowledgements
- [NOAA](https://nomads.ncep.noaa.gov/)
- [MET Norway](https://www.met.no/)
- [Natural Earth](https://www.naturalearthdata.com/)

---

