"""PyroNexa 26 - Input Validation and Sanitization Utilities

Validates geographical bounding boxes, coordinates, date intervals,
satellite identifiers, and confidence categories to protect against
malformed requests and injection vulnerabilities.
"""

from datetime import datetime, date
from typing import Dict, Any, Tuple, Optional, List
import re

from backend.config import SENSOR_REGISTRY, PRESET_REGIONS


class ValidationError(ValueError):
    """Custom exception raised when input validation fails."""
    pass


def validate_coordinates(lat: float, lon: float) -> Tuple[float, float]:
    """Validate latitude and longitude ranges.
    
    Returns:
        (lat, lon) as floats
    Raises:
        ValidationError: if coordinates are out of valid bounds.
    """
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        raise ValidationError(f"Invalid coordinate format: lat={lat}, lon={lon}")

    if not (-90.0 <= lat <= 90.0):
        raise ValidationError(f"Latitude must be between -90.0 and 90.0 (got {lat})")
    if not (-180.0 <= lon <= 180.0):
        raise ValidationError(f"Longitude must be between -180.0 and 180.0 (got {lon})")

    return round(lat, 6), round(lon, 6)


def validate_bbox(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float
) -> Tuple[float, float, float, float]:
    """Validate a bounding box [min_lon, min_lat, max_lon, max_lat].
    
    Raises:
        ValidationError: if coordinates are invalid or inverted.
    """
    try:
        min_lon = float(min_lon)
        min_lat = float(min_lat)
        max_lon = float(max_lon)
        max_lat = float(max_lat)
    except (TypeError, ValueError):
        raise ValidationError(
            f"Bounding box coordinates must be numeric: [{min_lon}, {min_lat}, {max_lon}, {max_lat}]"
        )

    if not (-180.0 <= min_lon <= 180.0) or not (-180.0 <= max_lon <= 180.0):
        raise ValidationError("Longitude must be between -180.0 and 180.0")
    if not (-90.0 <= min_lat <= 90.0) or not (-90.0 <= max_lat <= 90.0):
        raise ValidationError("Latitude must be between -90.0 and 90.0")

    if min_lon > max_lon:
        raise ValidationError(f"min_lon ({min_lon}) cannot be greater than max_lon ({max_lon})")
    if min_lat > max_lat:
        raise ValidationError(f"min_lat ({min_lat}) cannot be greater than max_lat ({max_lat})")

    # Guard against zero-area bounding boxes
    if min_lon == max_lon or min_lat == max_lat:
        raise ValidationError("Bounding box must have non-zero area (min and max cannot be identical)")

    return round(min_lon, 4), round(min_lat, 4), round(max_lon, 4), round(max_lat, 4)


def parse_date_safely(date_str: str) -> date:
    """Parse a date string in YYYY-MM-DD format."""
    if not isinstance(date_str, str):
        raise ValidationError(f"Expected date string, got {type(date_str).__name__}")
    
    clean_str = date_str.strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", clean_str):
        raise ValidationError(f"Invalid date format '{date_str}'. Expected YYYY-MM-DD.")

    try:
        parsed = datetime.strptime(clean_str, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValidationError(f"Invalid calendar date '{date_str}': {e}")

    # Check realistic year range for MODIS/VIIRS satellite era (2000 to 2030)
    if parsed.year < 2000 or parsed.year > 2030:
        raise ValidationError(f"Date {parsed} is outside supported satellite observation era (2000-2030)")

    return parsed


def validate_date_range(
    start_date: str,
    end_date: str,
    max_days: Optional[int] = None
) -> Tuple[date, date]:
    """Validate that start_date <= end_date and optionally checks max span."""
    d_start = parse_date_safely(start_date)
    d_end = parse_date_safely(end_date)

    if d_start > d_end:
        raise ValidationError(f"start_date ({d_start}) cannot be after end_date ({d_end})")

    span_days = (d_end - d_start).days + 1
    if max_days and span_days > max_days:
        raise ValidationError(
            f"Requested date range ({span_days} days) exceeds maximum allowed limit of {max_days} days"
        )

    return d_start, d_end


def validate_sensor_filter(sensor: Optional[str]) -> str:
    """Validate sensor selection: 'all', 'MODIS', 'VIIRS', or specific sensor key."""
    if not sensor:
        return "all"
    
    sensor_clean = sensor.strip().upper()
    valid_sensors = {"ALL", "MODIS", "VIIRS"} | set(SENSOR_REGISTRY.keys())
    
    if sensor_clean not in valid_sensors:
        raise ValidationError(
            f"Unknown sensor '{sensor}'. Valid options are: {sorted(list(valid_sensors))}"
        )
    return sensor_clean


def validate_confidence_filter(confidence: Optional[str]) -> str:
    """Validate confidence filter: 'all', 'low', 'nominal', 'high'."""
    if not confidence:
        return "all"
    
    conf_clean = confidence.strip().lower()
    valid_confidences = {"all", "low", "nominal", "high"}
    
    if conf_clean not in valid_confidences:
        raise ValidationError(
            f"Invalid confidence category '{confidence}'. Expected one of: {sorted(list(valid_confidences))}"
        )
    return conf_clean


def validate_daynight_filter(daynight: Optional[str]) -> str:
    """Validate day/night overpass filter: 'all', 'D', 'N'."""
    if not daynight:
        return "all"
    dn_clean = daynight.strip().lower()
    if dn_clean == "all":
        return "all"
    if dn_clean in ("d", "day"):
        return "D"
    if dn_clean in ("n", "night"):
        return "N"
    raise ValidationError(f"Invalid daynight filter '{daynight}'. Expected 'all', 'D', or 'N'")


def validate_satellite_filter(satellite: Optional[str]) -> str:
    """Validate specific satellite platform filter."""
    if not satellite:
        return "all"
    sat_clean = satellite.strip()
    valid_sats = {"all", "Terra", "Aqua", "NOAA-20", "NOAA-21", "Suomi-NPP"}
    # Case-insensitive lookup
    sat_map = {s.lower(): s for s in valid_sats}
    if sat_clean.lower() not in sat_map:
        raise ValidationError(f"Invalid satellite '{satellite}'. Expected one of: {sorted(list(valid_sats))}")
    return sat_map[sat_clean.lower()]


def validate_frp_range(
    min_frp: Optional[Any],
    max_frp: Optional[Any]
) -> Tuple[Optional[float], Optional[float]]:
    """Validate minimum and maximum Fire Radiative Power (MW)."""
    parsed_min = None
    parsed_max = None

    if min_frp is not None and str(min_frp).strip() != "":
        try:
            parsed_min = float(min_frp)
        except (ValueError, TypeError):
            raise ValidationError(f"min_frp must be numeric (got '{min_frp}')")
        if parsed_min < 0:
            raise ValidationError(f"min_frp must be non-negative (got {parsed_min})")

    if max_frp is not None and str(max_frp).strip() != "":
        try:
            parsed_max = float(max_frp)
        except (ValueError, TypeError):
            raise ValidationError(f"max_frp must be numeric (got '{max_frp}')")
        if parsed_max < 0:
            raise ValidationError(f"max_frp must be non-negative (got {parsed_max})")

    if parsed_min is not None and parsed_max is not None and parsed_min > parsed_max:
        raise ValidationError(f"min_frp ({parsed_min}) cannot exceed max_frp ({parsed_max})")

    return parsed_min, parsed_max


def parse_query_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Extract and validate all standard query parameters from Flask request.args."""
    validated: Dict[str, Any] = {}

    # Region preset or custom bbox
    region = params.get("region", "").strip().lower()
    if region and region in PRESET_REGIONS:
        validated["region"] = region
        validated["bbox"] = PRESET_REGIONS[region]["bbox"]
    elif all(k in params for k in ("min_lon", "min_lat", "max_lon", "max_lat")):
        validated["bbox"] = validate_bbox(
            params["min_lon"], params["min_lat"], params["max_lon"], params["max_lat"]
        )
        validated["region"] = "custom"
    else:
        # Default region
        validated["region"] = "california"
        validated["bbox"] = PRESET_REGIONS["california"]["bbox"]

    # Date range
    start_date = params.get("start_date")
    end_date = params.get("end_date")
    if start_date and end_date:
        d_start, d_end = validate_date_range(start_date, end_date)
        validated["start_date"] = d_start.isoformat()
        validated["end_date"] = d_end.isoformat()
    else:
        validated["start_date"] = None
        validated["end_date"] = None

    # Sensor & Satellite
    validated["sensor"] = validate_sensor_filter(params.get("sensor"))
    validated["satellite"] = validate_satellite_filter(params.get("satellite"))

    # Confidence & Day/Night
    validated["confidence"] = validate_confidence_filter(params.get("confidence"))
    validated["daynight"] = validate_daynight_filter(params.get("daynight"))

    # FRP range filtering
    min_frp, max_frp = validate_frp_range(params.get("min_frp"), params.get("max_frp"))
    validated["min_frp"] = min_frp
    validated["max_frp"] = max_frp

    # Pagination
    try:
        page = int(params.get("page", 1))
        per_page = int(params.get("per_page", 50))
        validated["page"] = max(1, page)
        validated["per_page"] = min(500, max(1, per_page))
    except (ValueError, TypeError):
        validated["page"] = 1
        validated["per_page"] = 50

    return validated
