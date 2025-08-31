import plotly.graph_objects as go
import numpy as np

def create_plots(atms_variable, lon, lat, colorscale='Blues', colorbar_x=1.0, colorbar_y=.25, colorbar_len=1, zmin=0, zmax=35, text='.', hover_label='Cloud'):
    """
    Create a Plotly heatmap from GFS for variable of choice.
    Args:
        atms_variable: 2D array
        lon, lat: 1D arrays
        text: unit string (e.g. 'm/s', '%', 'mm')
        hover_label: variable name for hover
        ...
    Returns:
        go.Heatmap
    """
    return go.Heatmap(
        z=atms_variable,
        x=lon,
        y=lat,
        colorscale=colorscale,
        zmin=zmin,
        zmax=zmax,
        colorbar=dict(
            title=dict(text=text, side="right", font=dict(size=14)),
            x=colorbar_x, xanchor="left", y=colorbar_y, len=colorbar_len, yanchor="middle",
            tickfont=dict(size=12),
            tickangle=0
        ),
        showscale=True,
        hovertemplate=f"Lon: %{{x:.2f}}<br>Lat: %{{y:.2f}}<br>{hover_label}: %{{z:.1f}} {text}<extra></extra>",
    )

def create_scatter(atms_variable, lon, lat, colorscale="RdYlBu_r", cmin=0, cmax=35, colorbar_x=1.0, colorbar_y=0.5, colorbar_len=1, text='m/s', hover_label='Wind'):
    """
    Scatter plot for wind speed at given points.
    """
    return go.Scatter(
        x=lon,
        y=lat,
        mode='markers',
        marker=dict(
            color=atms_variable,
            colorscale=colorscale,
            cmin=cmin,
            cmax=cmax,
            colorbar=dict(
                title=dict(text=text, side="right", font=dict(size=14)),
                x=colorbar_x, xanchor="left", y=colorbar_y, len=colorbar_len, yanchor="middle",
                tickfont=dict(size=12), tickangle=0,
                tickvals=list(range(int(cmin), int(cmax)+1, 5))
            ),
            size=4,
            opacity=0.7,
            showscale=True
        ),
        text=[f"{val:.1f} {text}" for val in atms_variable],
        hovertemplate=f"Lat: %{{y:.2f}}<br>Lon: %{{x:.2f}}<br>{hover_label}: %{{text}}",
        name='',
        showlegend=False
    )

def add_country_borders(fig, world, lon_shift=True, row=None, col=None):
    import numpy as np
    for _, country in world.iterrows():
        geom = country.geometry
        def shift_lon(xx):
            xx = np.array(xx)
            xx = np.where(xx > 180, xx - 360, xx)
            return xx.tolist()
        def skip_polar(y):
            y = np.array(y)
            return np.all(y > 85) or np.all(y < -85)
        def skip_wraparound(x):
            x = np.array(x)
            return (x.max() - x.min()) > 350
        scatter_kwargs = dict(mode='lines', line=dict(color='black', width=1), showlegend=False, hoverinfo='skip')
        if row is not None and col is not None:
            scatter_kwargs['row'] = row
            scatter_kwargs['col'] = col
        if geom.geom_type == 'MultiPolygon':
            for poly in geom.geoms:
                x, y = poly.exterior.xy
                if skip_polar(y):
                    continue
                if lon_shift:
                    x = shift_lon(x)
                if skip_wraparound(x):
                    continue
                fig.add_scatter(x=x, y=list(y), **scatter_kwargs)
        elif geom.geom_type == 'Polygon':
            x, y = geom.exterior.xy
            if not skip_polar(y):
                if lon_shift:
                    x = shift_lon(x)
                if not skip_wraparound(x):
                    fig.add_scatter(x=x, y=list(y), **scatter_kwargs)



