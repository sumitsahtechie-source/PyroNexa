"""PyroNexa 26 - Geospatial Computation Utilities

Provides spatial calculations including Haversine distance, grid binning,
pixel footprint ground area estimation, and spatial coincidence clustering
for MODIS and VIIRS sensor comparison.
"""

import math
from typing import Tuple, List, Dict, Any
import numpy as np


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth in kilometers.
    
    Uses Haversine formula with mean Earth radius R = 6371.0 km.
    """
    R = 6371.0  # Earth's mean radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def get_grid_cell(lat: float, lon: float, grid_size_deg: float = 0.25) -> Tuple[float, float, str]:
    """Bin continuous coordinates into a discrete spatial grid cell.
    
    Returns:
        (cell_lat, cell_lon, cell_id) where cell_lat and cell_lon are bottom-left
        or center coordinates, and cell_id is a unique string token.
    """
    cell_lat = round(math.floor(lat / grid_size_deg) * grid_size_deg, 4)
    cell_lon = round(math.floor(lon / grid_size_deg) * grid_size_deg, 4)
    cell_id = f"cell_{cell_lat:+.2f}_{cell_lon:+.2f}"
    return cell_lat, cell_lon, cell_id


def estimate_pixel_footprint_km2(
    instrument: str,
    scan: float = 1.0,
    track: float = 1.0
) -> float:
    """Calculate the estimated ground footprint area (km²) of an active fire pixel.
    
    MODIS:
      Nadir resolution: 1 km x 1 km (1.0 km²).
      Off-nadir pixel growth: reaches up to ~2 km (track) x ~4.8 km (scan) = ~9.6 km²
      at swath edge due to panoramic distortion. If scan and track dimensions
      are reported by FIRMS, area = scan * track; otherwise default nadir 1.0 km².
      
    VIIRS:
      Nadir resolution: 375 m x 375 m (~0.14 km²).
      VIIRS uses unique onboard sample aggregation (3:1 nadir, 2:1 mid-scan, 1:1 edge)
      which constrains pixel footprint growth to at most ~0.6 km² at edge of swath.
      If scan and track are provided, area = scan * track; otherwise default ~0.14 km².
    """
    inst = (instrument or "").upper()
    try:
        s = float(scan)
        t = float(track)
        if s > 0 and t > 0:
            return round(s * t, 4)
    except (ValueError, TypeError):
        pass

    if "VIIRS" in inst:
        return 0.1406  # 0.375 * 0.375 km
    else:
        return 1.0000  # 1.0 * 1.0 km


def is_within_bbox(
    lat: float,
    lon: float,
    bbox: Tuple[float, float, float, float]
) -> bool:
    """Check if a point (lat, lon) is inside [min_lon, min_lat, max_lon, max_lat]."""
    min_lon, min_lat, max_lon, max_lat = bbox
    return (min_lat <= lat <= max_lat) and (min_lon <= lon <= max_lon)
