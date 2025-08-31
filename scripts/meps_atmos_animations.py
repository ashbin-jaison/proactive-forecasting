import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Imports ---
import plotly.graph_objects as go
import plotly.io as pio
import numpy as np
from skyfora.data import open_opendap_dataset
from skyfora.plot import create_scatter, add_country_borders
from skyfora.geo import load_country_borders


# data configuration
url = "https://thredds.met.no/thredds/dodsC/metpplatest/met_forecast_1_0km_nordic_latest.nc" # Link to the latest MEPS forecast
stride = 20  # Subsampling step for faster plotting
num_frames = 24  # Number of time steps to animate

# --- Data Loading ---
ds = open_opendap_dataset(url)
wind = ds['wind_speed_10m'].isel(time=slice(0, num_frames))
cloud = ds['cloud_area_fraction'].isel(time=slice(0, num_frames))
precip = ds['precipitation_amount'].isel(time=slice(0, num_frames))
times = wind['time'].values
lat = ds['latitude'].values
lon = ds['longitude'].values

# Subsample for plotting
z0 = wind.isel(time=0).values[::stride, ::stride]
cloud0 = cloud.isel(time=0).values[::stride, ::stride]
precip0 = precip.isel(time=0).values[::stride, ::stride]
lat_sub = lat[::stride, ::stride]
lon_sub = lon[::stride, ::stride]

# --- Animation Frames ---
frames = []
for t_idx in range(num_frames):
    # Subsample and flatten for scatter
    zf = wind.isel(time=t_idx).values[::stride, ::stride].flatten()
    cloudf = cloud.isel(time=t_idx).values[::stride, ::stride].flatten()
    precipf = precip.isel(time=t_idx).values[::stride, ::stride].flatten()
    latf = lat[::stride, ::stride].flatten()
    lonf = lon[::stride, ::stride].flatten()
    # Clean up values
    cloudf = np.clip(cloudf, 0, 1)
    precipf = np.where(~np.isfinite(precipf) | (precipf > 1e4), 0, precipf)

    wind_scatter = create_scatter(zf, lonf, latf, colorscale="RdYlBu_r", cmin=0, cmax=35, colorbar_x=1.01, colorbar_y=5/6, colorbar_len=1/3, text='m/s', hover_label='Wind')
    cloud_scatter = create_scatter(cloudf, lonf, latf, colorscale="Blues", cmin=0, cmax=1, colorbar_x=1.01, colorbar_y=0.5, colorbar_len=1/3, text='%', hover_label='Cloud cover')
    precip_scatter = create_scatter(precipf, lonf, latf, colorscale="PuBuGn", cmin=0, cmax=25, colorbar_x=1.01, colorbar_y=1/6, colorbar_len=1/3, text='mm', hover_label='Precipitation')

    # Add frame
    frame = go.Frame(
        data=[wind_scatter, cloud_scatter, precip_scatter],
        name=str(times[t_idx]),
        layout=go.Layout(title_text=f"MEPS Forecast: Wind, Cloud, Precip at {str(times[t_idx])}")
    )
    frames.append(frame)

# --- Initial Figure with Subplots ---
from plotly.subplots import make_subplots
fig_anim = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True, shared_yaxes=True,
    vertical_spacing=0.04,
    subplot_titles=(
        "10m Wind Speed (m/s)",
        "Cloud Area Fraction",
        "Precipitation Amount (mm)"
    )
)

# Row 1: Wind speed
z0 = z0.flatten()
lon_sub = lon_sub.flatten()
lat_sub = lat_sub.flatten()
wind_scatter = create_scatter(z0, lon_sub, lat_sub, colorscale="RdYlBu_r", cmin=0, cmax=35, colorbar_x=1.01, colorbar_y=5/6, colorbar_len=1/3, text='m/s', hover_label='Wind')
fig_anim.add_trace(wind_scatter, row=1, col=1)

# Row 2: Cloud area fraction
cloud0_clean = np.clip(cloud0.flatten(), 0, 1)
cloud_scatter = create_scatter(cloud0_clean, lon_sub, lat_sub, colorscale="Blues", cmin=0, cmax=1, colorbar_x=1.01, colorbar_y=0.5, colorbar_len=1/3, text='%', hover_label='Cloud cover')
fig_anim.add_trace(cloud_scatter, row=2, col=1)

# Row 3: Precipitation amount
precip0_clean = np.where(~np.isfinite(precip0.flatten()) | (precip0.flatten() > 1e4), 0, precip0.flatten())
precip_scatter = create_scatter(precip0_clean, lon_sub, lat_sub, colorscale="PuBuGn", cmin=0, cmax=25, colorbar_x=1.01, colorbar_y=1/6, colorbar_len=1/3, text='mm', hover_label='Precipitation')
fig_anim.add_trace(precip_scatter, row=3, col=1)

# --- Final Layout and Show ---
fig_anim.frames = frames
fig_anim.update_layout(
    title=f"MEPS Forecast: Wind, Cloud, Precip at {str(times[0])}",
    width=600,
    height=1200,
    updatemenus=[dict(type="buttons", showactive=False, y=1, x=-.1, xanchor="left", yanchor="top", pad=dict(t=0, r=10),
            buttons=[dict(label="Play",method="animate",args=[[f.name for f in frames],dict(frame=dict(duration=500, redraw=True),fromcurrent=True, mode="immediate")]),
                     dict(label="Pause",method="animate",args=[[None],dict(frame=dict(duration=0, redraw=False),mode="immediate")])
            ])]
)

# --- Country Borders ---
world = load_country_borders('data/ne_10m_admin_0_countries.zip', bbox=(lon_sub.min(), lat_sub.min(), lon_sub.max(), lat_sub.max()))
add_country_borders(fig_anim, world, row=1, col=1)
add_country_borders(fig_anim, world, row=2, col=1)
add_country_borders(fig_anim, world, row=3, col=1)

pio.renderers.default = "browser"
fig_anim.show()

