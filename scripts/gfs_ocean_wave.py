import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.data import open_opendap_dataset, get_gfs_wave_opendap_url, get_latest_gfs_cycle
from utils.plot import create_plots, add_country_borders
from utils.geo import load_country_borders
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import numpy as np
from datetime import datetime

# sourcing data
cycle, yyyymmdd = get_latest_gfs_cycle() # There are 4 cycles of GFS data per day, get the latest cycle
NUM_TIMESTEPS = 17  # Set number of time steps here, t+1 to t+NUM_TIMESTEPS
opendap_url = get_gfs_wave_opendap_url(yyyymmdd, cycle) # Get the OPeNDAP URL for the latest cycle
print(f"Using GFS OPeNDAP URL: {opendap_url}")

# Loading data
ds = open_opendap_dataset(opendap_url)
if ds is None:
    print("Failed to open GFS dataset.")
    sys.exit(1)

# Extract latitude and longitude arrays
lat = ds["lat"].values
lon = ds["lon"].values

# Prepare time labels for animation frames
time_values = ds["time"].values[:NUM_TIMESTEPS]
time_labels = [str(np.datetime64(t, 's'))[:16].replace('T', ' ') for t in time_values]

# Shift longitude if needed (for -180 to 180 range)
if np.any(lon > 180):
    lon_shifted = np.where(lon > 180, lon - 360, lon)
    sort_idx = np.argsort(lon_shifted)
    lon = lon_shifted[sort_idx]
else:
    sort_idx = None

# ANIMATION FRAMES (WIND + WAVE)
frames = []
for t in range(NUM_TIMESTEPS):
    # Extract data for each time step
    ds_t = ds.isel(time=t)
    wind = ds_t["windsfc"].values
    wave = ds_t["htsgwsfc"].values

    if sort_idx is not None:
        wind = wind[:, sort_idx]
        wave = wave[:, sort_idx]
    # Create traces for each subplot
    frame_data = [
        create_plots(wind, lon, lat, colorscale='RdYlBu_r', colorbar_x=1.0, colorbar_y=.75, colorbar_len=0.5, zmin=0, zmax=40,text='m/s', hover_label='Wind'),
        create_plots(wave, lon, lat, colorscale='Blues',colorbar_x=1.0, colorbar_y=0.25, colorbar_len=0.5, zmin=0, zmax=20,text='m', hover_label='Wave'),
    ]
    frame_label = time_labels[t]
    frames.append(go.Frame(
        data=frame_data,
        name=frame_label,
        layout=go.Layout(
            title_text=f"Wind Speed and significant wave height - Forecast Animation - {frame_label}"
        )
    ))

# Data for first frame
init_wind = ds.isel(time=0)["windsfc"].values
init_wave = ds.isel(time=0)["htsgwsfc"].values

if sort_idx is not None:
    init_wind = init_wind[:, sort_idx]
    init_wave = init_wave[:, sort_idx]

init_time_label = time_labels[0]

# Subplots
fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True, shared_yaxes=True,
    vertical_spacing=0.04,
    subplot_titles=(
        "Wind Speed at 10m (m/s)",
        "Significant wave height (m)",
    )
)

# Add initial traces for each subplot
fig.add_trace(create_plots(init_wind, lon, lat, colorscale='RdYlBu_r', colorbar_x=1.0, colorbar_y=.75, colorbar_len=0.5, zmin=0, zmax=35,text='m/s', hover_label='Wind'), row=1, col=1)
fig.add_trace(create_plots(init_wave, lon, lat, colorscale='Blues', colorbar_x=1.0, colorbar_y=0.25, colorbar_len=0.5, zmin=0, zmax=20,text='m', hover_label='Wave'), row=2, col=1)

# Attach animation frames
for frame in frames:
    for trace in frame.data:
        if isinstance(trace, go.Heatmap):
            trace.showscale = True
fig.frames = frames

# Set axis ticks
xticks = np.linspace(-180, 180, 7)
yticks = np.linspace(lat.min(), lat.max(), 7)

# Update layout for appearance and animation controls
fig.update_layout(
    title=f"Wind Speed and Significant wave height - Forecast Animation - {init_time_label}",
    width=800,
    height=800,
    xaxis=dict(range=[lon.min(), lon.max()], tickvals=xticks, ticktext=[f"{v:.1f}" for v in xticks]),
    yaxis=dict(range=[lat.min(), lat.max()], tickvals=yticks, ticktext=[f"{v:.1f}" for v in yticks]),
    xaxis2=dict(range=[lon.min(), lon.max()], tickvals=xticks, ticktext=[f"{v:.1f}" for v in xticks]),
    yaxis2=dict(range=[lat.min(), lat.max()], tickvals=yticks, ticktext=[f"{v:.1f}" for v in yticks]),
    plot_bgcolor="rgb(230,230,230)",
    updatemenus=[dict(type="buttons", showactive=False, buttons=[
        dict(label="Play", method="animate", args=[time_labels[:NUM_TIMESTEPS], {"frame": {"duration": 500, "redraw": True}, "fromcurrent": True}]),
        dict(label="Pause", method="animate", args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate", "transition": {"duration": 0}}])
    ])]
)

# Overlay country borders on all subplots
world = load_country_borders('data/ne_110m_admin_0_countries.zip')
add_country_borders(fig, world, row=1, col=1)
add_country_borders(fig, world, row=2, col=1)

# show and save figure
pio.renderers.default = "browser"
fig.show()
fig.write_html("wind_speed_and_cloud_cover.html")




