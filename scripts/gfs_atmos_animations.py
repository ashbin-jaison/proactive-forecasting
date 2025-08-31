import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.data import open_opendap_dataset, get_gfs_opendap_url, get_latest_gfs_cycle
from utils.plot import create_plots, add_country_borders
from utils.geo import load_country_borders
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
import numpy as np
from datetime import datetime

# sourcing data
cycle, yyyymmdd = get_latest_gfs_cycle() # There are 4 cycles of GFS data per day, get the latest cycle
NUM_TIMESTEPS = 20  # Set number of time steps ahead here, t+1 to t+NUM_TIMESTEPS
opendap_url = get_gfs_opendap_url(yyyymmdd, cycle) # Get the OPeNDAP URL for the latest cycle
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

# ANIMATION FRAMES (WIND + CLOUD + PRECIP)
frames = []
for t in range(NUM_TIMESTEPS):
    # Extract data for each time step
    ds_t = ds.isel(time=t)
    wind = np.sqrt(ds_t["ugrd10m"]**2 + ds_t["vgrd10m"]**2).values
    cloud = ds_t["tcdcclm"].values
    precip = ds_t["apcpsfc"].values
    pwat = ds_t["pwatclm"].values
    if sort_idx is not None:
        wind = wind[:, sort_idx]
        cloud = cloud[:, sort_idx]
        precip = precip[:, sort_idx]
        pwat = pwat[:, sort_idx]
    # Create traces for each subplot
    frame_data = [
        create_plots(wind, lon, lat, colorscale='RdYlBu_r', colorbar_x=1.0, colorbar_y= 7/8, colorbar_len = .2, zmin=0, zmax=35,text='m/s', hover_label='Wind'),
        create_plots(cloud, lon, lat, colorscale='Blues',colorbar_x=1.0, colorbar_y=5/8, colorbar_len=0.2, zmin=0, zmax=1,text='%', hover_label='Cloud'),
        create_plots(precip, lon, lat, colorscale='PuBuGn',colorbar_x=1.0, colorbar_y=3/8, colorbar_len=0.2, zmin=0, zmax=25,text='mm', hover_label='Precipitation'),
        create_plots(pwat, lon, lat, colorscale='rainbow',colorbar_x=1.0, colorbar_y=1/8, colorbar_len=0.2, zmin=0, zmax=70,text='mm', hover_label='Precipitable Water')
    ]
    # Add time label to frame name and layout
    frame_label = time_labels[t]
    frames.append(go.Frame(
        data=frame_data,
        name=frame_label,
        layout=go.Layout(
            title_text=f"Wind Speed, Cloud Cover, Precipitation and Precipitable Water - {frame_label}"
        )
    ))

# Data for first frame
init_wind = np.sqrt(ds.isel(time=0)["ugrd10m"]**2 + ds.isel(time=0)["vgrd10m"]**2).values
init_cloud = ds.isel(time=0)["tcdcclm"].values
init_precip = ds.isel(time=0)["apcpsfc"].values
init_pwat = ds.isel(time=0)["pwatclm"].values

if sort_idx is not None:
    init_wind = init_wind[:, sort_idx]
    init_cloud = init_cloud[:, sort_idx]
    init_precip = init_precip[:, sort_idx]
    init_pwat = init_pwat[:, sort_idx]

init_time_label = time_labels[0]

# make subplots
fig = make_subplots(
    rows=4, cols=1,
    shared_xaxes=True, shared_yaxes=True,
    vertical_spacing=0.03,
    subplot_titles=(
        "Wind Speed at 10m (m/s)",
        "Total Cloud Cover (%)",
        "Surface Total Precipitation (kg/m²)",
        "Precipitable Water (mm)"
    )
)

# Add initial traces for each subplot
fig.add_trace(create_plots(init_wind, lon, lat, colorscale='RdYlBu_r', colorbar_x=1.0, colorbar_y=7/8, colorbar_len=0.20, zmin=0, zmax=35,text='m/s', hover_label='Wind'), row=1, col=1)
fig.add_trace(create_plots(init_cloud, lon, lat, colorscale='Blues', colorbar_x=1.0, colorbar_y=5/8, colorbar_len=0.20, text='%', hover_label='Cloud'), row=2, col=1)
fig.add_trace(create_plots(init_precip, lon, lat, colorscale='PuBuGn',colorbar_x=1.0, colorbar_y=3/8, colorbar_len=0.20, zmin=0, zmax=25,text='mm', hover_label='Precipitation'), row=3, col=1)
fig.add_trace(create_plots(init_pwat, lon, lat, colorscale='rainbow',colorbar_x=1.0, colorbar_y=1/8, colorbar_len=0.20, zmin=0, zmax=70,text='mm', hover_label='Precipitable Water'), row=4, col=1)
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
    title=f"Wind Speed, Cloud Cover, Precipitation and Precipitable Water - {init_time_label}",
    width=1000,
    height=1800,
    xaxis=dict(range=[lon.min(), lon.max()], tickvals=xticks, ticktext=[f"{v:.1f}" for v in xticks]),
    yaxis=dict(range=[lat.min(), lat.max()], tickvals=yticks, ticktext=[f"{v:.1f}" for v in yticks]),
    xaxis2=dict(range=[lon.min(), lon.max()], tickvals=xticks, ticktext=[f"{v:.1f}" for v in xticks]),
    yaxis2=dict(range=[lat.min(), lat.max()], tickvals=yticks, ticktext=[f"{v:.1f}" for v in yticks]),
    xaxis3=dict(range=[lon.min(), lon.max()], tickvals=xticks, ticktext=[f"{v:.1f}" for v in xticks]),
    yaxis3=dict(range=[lat.min(), lat.max()], tickvals=yticks, ticktext=[f"{v:.1f}" for v in yticks]),
    xaxis4=dict(range=[lon.min(), lon.max()], tickvals=xticks, ticktext=[f"{v:.1f}" for v in xticks]),
    yaxis4=dict(range=[lat.min(), lat.max()], tickvals=yticks, ticktext=[f"{v:.1f}" for v in yticks]),
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
add_country_borders(fig, world, row=3, col=1)
add_country_borders(fig, world, row=4, col=1)

# show and save the plot
pio.renderers.default = "browser"
fig.show()
fig.write_html("wind_speed_and_cloud_cover.html")
