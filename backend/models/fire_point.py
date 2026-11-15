"""PyroNexa 26 - Standardized Fire Point Data Model

Defines the normalized schema representing an active fire observation
across MODIS and VIIRS satellite sensors.
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class FirePoint:
    """Harmonized active fire observation record."""
    latitude: float
    longitude: float
    brightness: float
    scan: float
    track: float
    acq_date: str  # YYYY-MM-DD
    acq_time: str  # HHMM string
    satellite: str  # Terra, Aqua, NOAA-20, NOAA-21, Suomi-NPP
    instrument: str  # MODIS, VIIRS
    confidence_raw: str  # Original value from FIRMS (e.g. "85" or "n")
    confidence_cat: str  # Harmonized category: 'low', 'nominal', 'high'
    confidence_pct: float  # Normalized percentage [0.0 - 100.0]
    version: str
    bright_t31: Optional[float]
    frp: float  # Fire Radiative Power (MW)
    daynight: str  # 'D' (Day) or 'N' (Night)
    footprint_area_km2: float  # Estimated ground pixel area
    grid_cell_id: str  # Spatial bin identifier (e.g. "cell_+37.25_-119.50")
    is_duplicate: bool = False  # Flag for coincident cluster detection

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to clean serializable dictionary."""
        d = asdict(self)
        # Round floating point values for compact JSON output
        d["latitude"] = round(self.latitude, 5)
        d["longitude"] = round(self.longitude, 5)
        d["brightness"] = round(self.brightness, 2)
        d["frp"] = round(self.frp, 2)
        d["footprint_area_km2"] = round(self.footprint_area_km2, 3)
        if self.bright_t31 is not None:
            d["bright_t31"] = round(self.bright_t31, 2)
        return d
