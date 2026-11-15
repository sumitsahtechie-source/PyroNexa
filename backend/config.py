"""PyroNexa 26 - Configuration Module

Provides centralized configuration for the PyroNexa satellite fire intelligence platform,
including NASA FIRMS API endpoints, sensor characteristics, caching parameters,
and geographic preset regions.
"""

from dataclasses import dataclass
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SAMPLE_DIR = DATA_DIR / "sample"
PROCESSED_DIR = DATA_DIR / "processed"
CACHE_DIR = DATA_DIR / "cache"

# Ensure runtime directories exist
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class SensorSpec:
    sensor_id: str
    display_name: str
    instrument: str
    platform: str
    nominal_resolution_m: int
    confidence_type: str  # 'percent' or 'categorical'
    firms_source_nrt: str
    firms_source_sp: str
    active: bool
    notes: str


# Official NASA FIRMS Supported Sensors
SENSOR_REGISTRY = {
    "MODIS_TERRA": SensorSpec(
        sensor_id="MODIS_TERRA",
        display_name="MODIS Terra",
        instrument="MODIS",
        platform="Terra",
        nominal_resolution_m=1000,
        confidence_type="percent",
        firms_source_nrt="MODIS_NRT",
        firms_source_sp="MODIS_SP",
        active=True,
        notes="1km resolution, AM/PM overpass, continuous record since 2000"
    ),
    "MODIS_AQUA": SensorSpec(
        sensor_id="MODIS_AQUA",
        display_name="MODIS Aqua",
        instrument="MODIS",
        platform="Aqua",
        nominal_resolution_m=1000,
        confidence_type="percent",
        firms_source_nrt="MODIS_NRT",
        firms_source_sp="MODIS_SP",
        active=True,
        notes="1km resolution, afternoon overpass (~13:30), continuous record since 2002"
    ),
    "VIIRS_NOAA20": SensorSpec(
        sensor_id="VIIRS_NOAA20",
        display_name="VIIRS NOAA-20 (JPSS-1)",
        instrument="VIIRS",
        platform="NOAA-20",
        nominal_resolution_m=375,
        confidence_type="categorical",
        firms_source_nrt="VIIRS_NOAA20_NRT",
        firms_source_sp="VIIRS_NOAA20_SP",
        active=True,
        notes="375m I-band resolution, operational continuity series launched Nov 2017"
    ),
    "VIIRS_NOAA21": SensorSpec(
        sensor_id="VIIRS_NOAA21",
        display_name="VIIRS NOAA-21 (JPSS-2)",
        instrument="VIIRS",
        platform="NOAA-21",
        nominal_resolution_m=375,
        confidence_type="categorical",
        firms_source_nrt="VIIRS_NOAA21_NRT",
        firms_source_sp="VIIRS_NOAA21_SP",
        active=True,
        notes="375m I-band resolution, operational continuity series launched Nov 2022"
    ),
    "VIIRS_SNPP": SensorSpec(
        sensor_id="VIIRS_SNPP",
        display_name="VIIRS Suomi NPP",
        instrument="VIIRS",
        platform="Suomi-NPP",
        nominal_resolution_m=375,
        confidence_type="categorical",
        firms_source_nrt="VIIRS_SNPP_NRT",
        firms_source_sp="VIIRS_SNPP_SP",
        active=True,
        notes="375m resolution; note 2026 Suomi NPP lifecycle transition"
    )
}

# Geographic presets for rapid regional filtering
PRESET_REGIONS = {
    "california": {
        "name": "California & Western US",
        "bbox": [-125.0, 32.0, -114.0, 42.5],  # min_lon, min_lat, max_lon, max_lat
        "center": [37.2, -119.5],
        "default_zoom": 6,
        "description": "High seasonal wildfire region with significant MODIS and VIIRS records."
    },
    "amazon": {
        "name": "Amazon Basin (South America)",
        "bbox": [-75.0, -15.0, -45.0, 2.0],
        "center": [-6.5, -60.0],
        "default_zoom": 5,
        "description": "Tropical deforestation and agricultural burn corridor with intense fire peaks."
    },
    "mediterranean": {
        "name": "Mediterranean Basin (Southern Europe)",
        "bbox": [-10.0, 35.0, 30.0, 45.0],
        "center": [40.0, 15.0],
        "default_zoom": 5,
        "description": "Summer drought fire-prone biome across Spain, Portugal, Greece, Italy."
    },
    "australia": {
        "name": "Southeast Australia",
        "bbox": [140.0, -39.0, 154.0, -28.0],
        "center": [-33.5, 147.0],
        "default_zoom": 6,
        "description": "Bushfire ecosystems with extreme seasonal fire weather."
    },
    "southeast_asia": {
        "name": "Southeast Asia / Indonesia",
        "bbox": [95.0, -10.0, 120.0, 10.0],
        "center": [0.0, 107.5],
        "default_zoom": 5,
        "description": "Peatland and agricultural burning zone with severe haze events."
    }
}


class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "pyronexa-2026-space-apps-challenge-secret")
    FIRMS_MAP_KEY = os.environ.get("FIRMS_MAP_KEY", "").strip()
    FIRMS_BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
    FIRMS_AVAILABILITY_URL = "https://firms.modaps.eosdis.nasa.gov/api/data_availability/csv"
    
    # Request limits & timeouts
    FIRMS_REQUEST_TIMEOUT = int(os.environ.get("FIRMS_REQUEST_TIMEOUT", "15"))  # seconds
    CACHE_TTL_SECONDS = int(os.environ.get("FIRMS_CACHE_TTL", "3600"))  # 1 hour
    MAX_DAYS_PER_QUERY = 10  # NASA FIRMS API restricts area queries to 10 days
    MAX_HISTORICAL_DAYS_QUERY = 30
    
    # Harmonization Settings
    SPATIAL_GRID_DEG = float(os.environ.get("SPATIAL_GRID_DEG", "0.25"))  # ~25km x 25km grid
    DUPLICATE_TIME_WINDOW_MINUTES = 60  # Detections within 60 mins considered coincident
    DUPLICATE_DISTANCE_KM = 1.5  # Cluster distance threshold
    
    # Paths
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR
    SAMPLE_DIR = SAMPLE_DIR
    PROCESSED_DIR = PROCESSED_DIR
    CACHE_DIR = CACHE_DIR

    # Default preset
    DEFAULT_REGION = os.environ.get("DEFAULT_REGION", "california")
    
    @classmethod
    def has_firms_key(cls) -> bool:
        """Returns True only if a non-placeholder FIRMS_MAP_KEY is provided."""
        return bool(cls.FIRMS_MAP_KEY and len(cls.FIRMS_MAP_KEY) >= 16)


class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    FIRMS_MAP_KEY = "test_firms_api_key_12345678"
    CACHE_TTL_SECONDS = 0


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": ProductionConfig
}
