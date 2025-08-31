"""
Geospatial helpers for Skyfora project.
"""
import geopandas as gpd
import numpy as np

def load_country_borders(shapefile_path, bbox=None):
    world = gpd.read_file(shapefile_path)
    if bbox is not None:
        from shapely.geometry import box as shapely_box
        min_lon, min_lat, max_lon, max_lat = bbox
        bbox_geom = shapely_box(min_lon, min_lat, max_lon, max_lat)
        world["geometry"] = world["geometry"].intersection(bbox_geom)
        world = world[~world.is_empty & world.geometry.notnull()]
    return world

def get_border_lines(world):
    from shapely.geometry import MultiLineString
    lines = []
    for _, country in world.iterrows():
        geom = country.geometry
        if geom is None or geom.is_empty:
            continue
        if geom.geom_type == 'Polygon':
            lines.append(geom.exterior)
        elif geom.geom_type == 'MultiPolygon':
            for poly in geom.geoms:
                if poly is None or poly.is_empty:
                    continue
                lines.append(poly.exterior)
    if lines:
        multilines = MultiLineString(lines)
        border_x = []
        border_y = []
        for line in multilines.geoms:
            x, y = line.xy
            border_x += list(x) + [None]
            border_y += list(y) + [None]
        return border_x, border_y
    return [], []
