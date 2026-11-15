"""PyroNexa 26 - Test Suite: Scientific Harmonization Service
"""

import pytest
import pandas as pd
import numpy as np
from backend.services.harmonization_service import HarmonizationService


class TestHarmonizationService:
    @pytest.fixture
    def sample_raw_df(self):
        """Create a synthetic DataFrame mimicking raw heterogeneous FIRMS data."""
        return pd.DataFrame({
            "LATITUDE": [37.5, 37.51, 38.0, 38.02],
            "LONGITUDE": [-119.5, -119.51, -120.0, -120.01],
            "BRIGHTNESS": [325.4, 340.1, 310.0, 315.5],
            "SCAN": [1.2, 0.4, 1.5, 0.45],
            "TRACK": [1.1, 0.4, 1.2, 0.40],
            "ACQ_DATE": ["2024-08-10", "2024-08-10", "2024-08-11", "2024-08-11"],
            "ACQ_TIME": [1330, 1335, 1400, 1405],
            "SATELLITE": ["Aqua", "NOAA-20", "Terra", "NOAA-21"],
            "INSTRUMENT": ["MODIS", "VIIRS", "MODIS", "VIIRS"],
            "CONFIDENCE": ["85", "h", "45", "n"],
            "VERSION": ["6.1NRT", "2.0NRT", "6.1NRT", "2.0NRT"],
            "FRP": [45.2, 12.8, 30.0, 8.5],
            "DAYNIGHT": ["D", "D", "D", "D"]
        })

    def test_standardize_raw_dataframe(self, sample_raw_df):
        service = HarmonizationService(grid_size_deg=0.25)
        std_df = service.standardize_raw_dataframe(sample_raw_df)

        assert len(std_df) == 4
        # Verify standardized column names (lowercase)
        expected_cols = [
            "latitude", "longitude", "brightness", "scan", "track",
            "acq_date", "acq_time", "satellite", "instrument",
            "confidence_raw", "confidence_cat", "confidence_pct",
            "version", "bright_t31", "frp", "daynight",
            "footprint_area_km2", "grid_cell_id"
        ]
        for col in expected_cols:
            assert col in std_df.columns

        # Verify MODIS confidence mapping
        modis_row = std_df[std_df["satellite"] == "Aqua"].iloc[0]
        assert modis_row["confidence_cat"] == "high"
        assert modis_row["confidence_pct"] == 85.0
        assert modis_row["footprint_area_km2"] == round(1.2 * 1.1, 4)

        # Verify VIIRS confidence mapping
        viirs_row = std_df[std_df["satellite"] == "NOAA-20"].iloc[0]
        assert viirs_row["confidence_cat"] == "high"
        assert viirs_row["confidence_pct"] == 92.0
        assert viirs_row["footprint_area_km2"] == round(0.4 * 0.4, 4)

    def test_standardize_empty_dataframe(self):
        service = HarmonizationService()
        empty_df = pd.DataFrame()
        result = service.standardize_raw_dataframe(empty_df)
        assert result.empty
        assert "latitude" in result.columns

    def test_daily_aggregation(self, sample_raw_df):
        service = HarmonizationService()
        std_df = service.standardize_raw_dataframe(sample_raw_df)
        daily = service.compute_daily_aggregation(std_df)

        assert not daily.empty
        assert "acq_date" in daily.columns
        assert "instrument" in daily.columns
        assert "detection_count" in daily.columns
        assert "total_frp" in daily.columns
        assert "total_footprint_km2" in daily.columns

    def test_monthly_aggregation(self, sample_raw_df):
        service = HarmonizationService()
        std_df = service.standardize_raw_dataframe(sample_raw_df)
        monthly = service.compute_monthly_aggregation(std_df)

        assert not monthly.empty
        assert "year_month" in monthly.columns
        assert "high_confidence_pct" in monthly.columns

    def test_spatial_grid_summary(self, sample_raw_df):
        service = HarmonizationService(grid_size_deg=0.25)
        std_df = service.standardize_raw_dataframe(sample_raw_df)
        grid_summary = service.compute_spatial_grid_summary(std_df)

        assert isinstance(grid_summary, list)
        assert len(grid_summary) > 0
        first = grid_summary[0]
        assert "grid_cell_id" in first
        assert "modis_count" in first
        assert "viirs_count" in first
        assert "total_frp" in first

    def test_rfai_calculation(self, sample_raw_df):
        service = HarmonizationService()
        std_df = service.standardize_raw_dataframe(sample_raw_df)
        rfai = service.calculate_relative_fire_activity_index(std_df)

        assert "overall_ratio" in rfai
        assert "area_ratio" in rfai
        assert "modis_total" in rfai
        assert "viirs_total" in rfai
        assert "monthly_rfai" in rfai
        assert rfai["modis_total"] == 2
        assert rfai["viirs_total"] == 2

    def test_detect_coincident_clusters(self, sample_raw_df):
        service = HarmonizationService()
        std_df = service.standardize_raw_dataframe(sample_raw_df)
        clustered = service.detect_coincident_clusters(std_df, dist_threshold_km=2.0)

        assert "is_coincident" in clustered.columns
        # Points on 2024-08-10 at lat 37.5, lon -119.5 and lat 37.51, lon -119.51 are ~1.4 km apart
        aug10 = clustered[clustered["acq_date"] == "2024-08-10"]
        assert aug10["is_coincident"].any()
