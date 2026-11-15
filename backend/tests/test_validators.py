"""PyroNexa 26 - Test Suite: Validators and Geospatial Utilities
"""

import pytest
from datetime import date
from backend.utils.validators import (
    validate_coordinates,
    validate_bbox,
    parse_date_safely,
    validate_date_range,
    validate_sensor_filter,
    validate_confidence_filter,
    parse_query_params,
    ValidationError
)
from backend.utils.geo_utils import (
    haversine_distance_km,
    get_grid_cell,
    estimate_pixel_footprint_km2,
    is_within_bbox
)


class TestValidators:
    def test_validate_coordinates_valid(self):
        lat, lon = validate_coordinates(37.7749, -122.4194)
        assert lat == 37.7749
        assert lon == -122.4194

    def test_validate_coordinates_invalid_latitude(self):
        with pytest.raises(ValidationError, match="Latitude must be between -90.0 and 90.0"):
            validate_coordinates(95.0, 0.0)

        with pytest.raises(ValidationError, match="Latitude must be between -90.0 and 90.0"):
            validate_coordinates(-90.1, 0.0)

    def test_validate_coordinates_invalid_longitude(self):
        with pytest.raises(ValidationError, match="Longitude must be between -180.0 and 180.0"):
            validate_coordinates(0.0, 185.0)

        with pytest.raises(ValidationError, match="Longitude must be between -180.0 and 180.0"):
            validate_coordinates(0.0, -181.0)

    def test_validate_coordinates_non_numeric(self):
        with pytest.raises(ValidationError, match="Invalid coordinate format"):
            validate_coordinates("invalid", 10.0)

    def test_validate_bbox_valid(self):
        bbox = validate_bbox(-120.0, 35.0, -115.0, 40.0)
        assert bbox == (-120.0, 35.0, -115.0, 40.0)

    def test_validate_bbox_inverted_lon(self):
        with pytest.raises(ValidationError, match="min_lon .* cannot be greater than max_lon"):
            validate_bbox(-110.0, 35.0, -120.0, 40.0)

    def test_validate_bbox_inverted_lat(self):
        with pytest.raises(ValidationError, match="min_lat .* cannot be greater than max_lat"):
            validate_bbox(-120.0, 42.0, -115.0, 35.0)

    def test_validate_bbox_zero_area(self):
        with pytest.raises(ValidationError, match="Bounding box must have non-zero area"):
            validate_bbox(-120.0, 35.0, -120.0, 35.0)

    def test_parse_date_safely_valid(self):
        d = parse_date_safely("2024-08-15")
        assert d == date(2024, 8, 15)

    def test_parse_date_safely_invalid_format(self):
        with pytest.raises(ValidationError, match="Invalid date format"):
            parse_date_safely("15-08-2024")

    def test_parse_date_safely_invalid_calendar_day(self):
        with pytest.raises(ValidationError, match="Invalid calendar date"):
            parse_date_safely("2024-02-31")

    def test_parse_date_safely_out_of_satellite_era(self):
        with pytest.raises(ValidationError, match="outside supported satellite observation era"):
            parse_date_safely("1985-05-01")

    def test_validate_date_range_valid(self):
        s, e = validate_date_range("2024-01-01", "2024-01-10", max_days=10)
        assert s == date(2024, 1, 1)
        assert e == date(2024, 1, 10)

    def test_validate_date_range_start_after_end(self):
        with pytest.raises(ValidationError, match="start_date .* cannot be after end_date"):
            validate_date_range("2024-05-10", "2024-05-01")

    def test_validate_date_range_exceeds_max_days(self):
        with pytest.raises(ValidationError, match="exceeds maximum allowed limit"):
            validate_date_range("2024-01-01", "2024-01-20", max_days=10)

    def test_validate_sensor_filter(self):
        assert validate_sensor_filter("all") == "ALL"
        assert validate_sensor_filter("modis") == "MODIS"
        assert validate_sensor_filter("viirs") == "VIIRS"
        assert validate_sensor_filter("VIIRS_NOAA20") == "VIIRS_NOAA20"

        with pytest.raises(ValidationError, match="Unknown sensor"):
            validate_sensor_filter("INVALID_SENSOR")

    def test_validate_confidence_filter(self):
        assert validate_confidence_filter("all") == "all"
        assert validate_confidence_filter("HIGH") == "high"
        assert validate_confidence_filter("nominal") == "nominal"
        assert validate_confidence_filter("low") == "low"

        with pytest.raises(ValidationError, match="Invalid confidence category"):
            validate_confidence_filter("invalid_conf")

    def test_parse_query_params_preset(self):
        params = {"region": "california", "sensor": "VIIRS", "page": "2", "per_page": "100"}
        parsed = parse_query_params(params)
        assert parsed["region"] == "california"
        assert parsed["sensor"] == "VIIRS"
        assert parsed["page"] == 2
        assert parsed["per_page"] == 100
        assert parsed["bbox"] == [-125.0, 32.0, -114.0, 42.5]


class TestGeoUtils:
    def test_haversine_distance(self):
        # Distance between San Francisco and Los Angeles (~559 km)
        d = haversine_distance_km(37.7749, -122.4194, 34.0522, -118.2437)
        assert 550.0 < d < 570.0

    def test_haversine_distance_zero(self):
        d = haversine_distance_km(37.0, -120.0, 37.0, -120.0)
        assert d == 0.0

    def test_get_grid_cell(self):
        lat, lon, cell_id = get_grid_cell(37.33, -119.67, grid_size_deg=0.25)
        assert lat == 37.25
        assert lon == -119.75
        assert "cell_" in cell_id

    def test_estimate_pixel_footprint_km2_modis(self):
        # At nadir (scan=1.0, track=1.0)
        area_nadir = estimate_pixel_footprint_km2("MODIS", 1.0, 1.0)
        assert area_nadir == 1.0

        # Off-nadir edge of scan (scan=4.8, track=2.0) -> ~9.6 km2
        area_edge = estimate_pixel_footprint_km2("MODIS", 4.8, 2.0)
        assert area_edge == 9.6

    def test_estimate_pixel_footprint_km2_viirs(self):
        # VIIRS nadir (~0.14 km2)
        area_nadir = estimate_pixel_footprint_km2("VIIRS", 0.375, 0.375)
        assert 0.14 <= area_nadir <= 0.15

        # VIIRS edge with 3:1 aggregation maintains area <= 0.6 km2
        area_edge = estimate_pixel_footprint_km2("VIIRS", 0.75, 0.55)
        assert area_edge <= 0.6

    def test_is_within_bbox(self):
        bbox = (-125.0, 32.0, -114.0, 42.0)
        assert is_within_bbox(37.0, -120.0, bbox) is True
        assert is_within_bbox(50.0, -120.0, bbox) is False
        assert is_within_bbox(37.0, -100.0, bbox) is False
