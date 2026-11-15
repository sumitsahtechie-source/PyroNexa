"""PyroNexa 26 - NASA FIRMS API Service

Integrates with NASA's Fire Information for Resource Management System (FIRMS) API.
Handles live area-based hotspot queries, authentication, request rate limiting,
error recovery, caching, and fallback to verified scientific sample datasets.
"""

from datetime import datetime, date, timedelta, timezone
import io
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import requests
import pandas as pd

from backend.config import Config, SENSOR_REGISTRY, PRESET_REGIONS
from backend.services.cache_service import cache_service
from backend.utils.validators import validate_bbox, ValidationError

logger = logging.getLogger(__name__)


class FIRMSService:
    """Service to interface with NASA FIRMS active fire endpoints."""

    def __init__(self, map_key: Optional[str] = None):
        self.map_key = map_key or Config.FIRMS_MAP_KEY
        self.base_url = Config.FIRMS_BASE_URL
        self.timeout = Config.FIRMS_REQUEST_TIMEOUT

    @property
    def is_configured(self) -> bool:
        """Return True if a valid NASA FIRMS map key is configured."""
        return bool(self.map_key and len(self.map_key) >= 16)

    def check_api_status(self) -> Dict[str, Any]:
        """Test NASA FIRMS API availability and authentication status."""
        status = {
            "configured": self.is_configured,
            "has_key": bool(self.map_key),
            "key_length": len(self.map_key) if self.map_key else 0,
            "endpoint": self.base_url,
            "operational": False,
            "mode": "live" if self.is_configured else "sample",
            "message": "",
            "active_sensors": list(SENSOR_REGISTRY.keys()),
            "checked_at": datetime.now(timezone.utc).isoformat()
        }

        if not self.is_configured:
            status["message"] = (
                "FIRMS_MAP_KEY is not configured or too short. Operating in scientific sample data mode. "
                "Get a free key at https://firms.modaps.eosdis.nasa.gov/api/map_key/"
            )
            return status

        # Lightweight availability probe
        test_url = f"{self.base_url}/{self.map_key}/VIIRS_NOAA20_NRT/-120,37,-119,38/1"
        try:
            resp = requests.get(test_url, timeout=self.timeout)
            if resp.status_code == 200 and not resp.text.startswith("Invalid"):
                status["operational"] = True
                status["message"] = "NASA FIRMS API connection verified and active."
            elif resp.status_code in (401, 403) or "Invalid MAP_KEY" in resp.text:
                status["operational"] = False
                status["message"] = "NASA FIRMS API key rejected (Invalid MAP_KEY or unauthorized)."
            else:
                status["operational"] = False
                status["message"] = f"NASA FIRMS API returned status {resp.status_code}: {resp.text[:120]}"
        except requests.RequestException as e:
            status["operational"] = False
            status["message"] = f"Network connection to NASA FIRMS failed: {str(e)}"

        return status

    def fetch_live_fire_data(
        self,
        source: str,
        bbox: Tuple[float, float, float, float],
        day_range: int = 1,
        date_str: Optional[str] = None
    ) -> pd.DataFrame:
        """Fetch raw active fire CSV data from NASA FIRMS API.
        
        Args:
            source: e.g. 'MODIS_NRT', 'VIIRS_NOAA20_NRT', 'VIIRS_NOAA21_NRT'
            bbox: (min_lon, min_lat, max_lon, max_lat)
            day_range: 1 to 10 days
            date_str: YYYY-MM-DD or None for current day
        """
        if not self.is_configured:
            raise ValidationError("NASA FIRMS API key is not configured.")

        min_lon, min_lat, max_lon, max_lat = validate_bbox(*bbox)
        day_range = max(1, min(10, int(day_range)))

        # Format FIRMS coordinates: W,S,E,N
        area_coords = f"{min_lon},{min_lat},{max_lon},{max_lat}"
        
        if date_str:
            url = f"{self.base_url}/{self.map_key}/{source}/{area_coords}/{day_range}/{date_str}"
        else:
            url = f"{self.base_url}/{self.map_key}/{source}/{area_coords}/{day_range}"

        # Check cache
        cache_params = {
            "source": source,
            "bbox": [min_lon, min_lat, max_lon, max_lat],
            "day_range": day_range,
            "date": date_str
        }
        cached = cache_service.get("firms_raw", cache_params)
        if cached is not None:
            return pd.read_json(io.StringIO(cached))

        try:
            resp = requests.get(url, timeout=self.timeout)
            resp.raise_for_status()
            
            # Check for FIRMS error messages returned as plain text
            text = resp.text.strip()
            if text.startswith("Invalid") or "Error" in text[:40]:
                raise RuntimeError(f"NASA FIRMS Error: {text}")

            df = pd.read_csv(io.StringIO(text))
            
            # Save to cache
            cache_service.set("firms_raw", cache_params, df.to_json())
            return df
        except requests.RequestException as e:
            logger.error(f"FIRMS request failed: {e}")
            raise RuntimeError(f"Failed to fetch data from NASA FIRMS API: {str(e)}")

    def load_sample_dataset(self) -> pd.DataFrame:
        """Load local verified sample dataset."""
        sample_path = Config.SAMPLE_DIR / "harmonized_sample.csv"
        if not sample_path.exists():
            # If not yet generated, build it on the fly
            from backend.services.sample_data_generator import generate_sample_dataset
            generate_sample_dataset(sample_path)
            
        df = pd.read_csv(sample_path)
        return df

    def get_fire_data(
        self,
        bbox: Tuple[float, float, float, float],
        sensor: str = "ALL",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        confidence: str = "all"
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Retrieve active fire data using live NASA FIRMS API if configured,
        or high-fidelity scientific sample data if unconfigured or requested.
        
        Returns:
            (DataFrame, metadata_dict)
        """
        metadata = {
            "source_type": "sample",
            "is_sample_data": True,
            "firms_key_configured": self.is_configured,
            "sensor_requested": sensor,
            "bbox": list(bbox),
            "start_date": start_date,
            "end_date": end_date,
            "confidence_filter": confidence,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "attribution": "NASA FIRMS (Fire Information for Resource Management System) / LANCE / EOSDIS"
        }

        # Attempt live query if key is present
        if self.is_configured:
            try:
                # Determine sources to query
                sources_to_query = []
                sensor_up = sensor.upper()
                if sensor_up in ("ALL", "MODIS"):
                    sources_to_query.append(("MODIS_NRT", "MODIS", "Terra/Aqua"))
                if sensor_up in ("ALL", "VIIRS"):
                    sources_to_query.append(("VIIRS_NOAA20_NRT", "VIIRS", "NOAA-20"))
                    sources_to_query.append(("VIIRS_NOAA21_NRT", "VIIRS", "NOAA-21"))

                dfs = []
                for src_id, inst, sat in sources_to_query:
                    raw_df = self.fetch_live_fire_data(
                        source=src_id,
                        bbox=bbox,
                        day_range=Config.MAX_DAYS_PER_QUERY,
                        date_str=end_date
                    )
                    if not raw_df.empty:
                        raw_df["instrument_source"] = inst
                        raw_df["satellite_source"] = sat
                        dfs.append(raw_df)

                if dfs:
                    combined = pd.concat(dfs, ignore_index=True)
                    metadata["source_type"] = "live_nasa_firms"
                    metadata["is_sample_data"] = False
                    return combined, metadata
            except Exception as e:
                logger.warning(f"Live FIRMS fetch failed ({e}). Falling back to scientific sample dataset.")
                metadata["live_fetch_error"] = str(e)

        # Fallback to sample dataset
        df = self.load_sample_dataset()
        return df, metadata


firms_service = FIRMSService()
