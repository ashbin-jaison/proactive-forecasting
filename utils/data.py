import xarray as xr
import os
import zipfile
import numpy as np
from datetime import datetime, timedelta

def get_latest_gfs_cycle(buffer_hours=6):
    now = datetime.utcnow() - timedelta(hours=buffer_hours)
    yyyymmdd = now.strftime("%Y%m%d")
    print(yyyymmdd)
    hour = now.hour
    if hour >= 18:
        return "18",yyyymmdd
    elif hour >= 12:
        return "12",yyyymmdd
    elif hour >= 6:
        return "06",yyyymmdd
    else:
        return "00",yyyymmdd

def open_opendap_dataset(url):
    try:
        ds = xr.open_dataset(url)
        return ds
    except Exception as e:
        print(f"Error opening OPeNDAP dataset: {e}")
        return None
    
# --- GFS OPeNDAP URL GENERATOR ---
def get_gfs_opendap_url(yyyymmdd, cycle="00"):
    return f"http://nomads.ncep.noaa.gov:80/dods/gfs_0p25/gfs{yyyymmdd}/gfs_0p25_{cycle}z"

# --- GFS OPeNDAP URL GENERATOR ---
def get_gfs_wave_opendap_url(yyyymmdd, cycle="00"):
    return f"http://nomads.ncep.noaa.gov:80/dods/wave/gfswave/{yyyymmdd}/gfswave.global.0p25_{cycle}z"

def extract_shapefile(zip_path, extract_dir):
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    for file in os.listdir(extract_dir):
        if file.endswith('.shp'):
            return os.path.join(extract_dir, file)
    raise FileNotFoundError('No .shp file found in the extracted zip.')
