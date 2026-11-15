"""PyroNexa 26 - Test Suite: Analytics and Anomaly Detection
"""

import pytest
import pandas as pd
import numpy as np
from backend.services.analytics_service import AnalyticsService
from backend.services.harmonization_service import HarmonizationService


class TestAnalyticsService:
    @pytest.fixture
    def harmonized_df(self):
        records = []
        # Create multi-year seasonal data across 5 years
        for yr in [2020, 2021, 2022, 2023, 2024]:
            for m in range(1, 13):
                # Peak in August (month 8)
                count = 40 if m == 8 else (5 if m in (1, 2, 12) else 15)
                # In 2023, create an extreme surge in August (180 hotspots)
                if yr == 2023 and m == 8:
                    count = 180

                for i in range(count):
                    records.append({
                        "latitude": 37.0 + (i * 0.01),
                        "longitude": -119.0 - (i * 0.01),
                        "brightness": 320.0 + (i % 30),
                        "scan": 1.0 if (i % 2 == 0) else 0.4,
                        "track": 1.0 if (i % 2 == 0) else 0.4,
                        "acq_date": f"{yr}-{m:02d}-15",
                        "acq_time": "1330",
                        "satellite": "Aqua" if (i % 2 == 0) else "NOAA-20",
                        "instrument": "MODIS" if (i % 2 == 0) else "VIIRS",
                        "confidence_raw": "80" if (i % 2 == 0) else "h",
                        "confidence_cat": "high",
                        "confidence_pct": 85.0 if (i % 2 == 0) else 92.0,
                        "version": "6.1NRT",
                        "bright_t31": 300.0,
                        "frp": 25.0 if (i % 2 == 0) else 10.0,
                        "daynight": "D",
                        "footprint_area_km2": 1.0 if (i % 2 == 0) else 0.16,
                        "grid_cell_id": "cell_+37.00_-119.00",
                        "is_duplicate": False,
                        "year": yr,
                        "month": m,
                        "day": 15
                    })
        return pd.DataFrame(records)

    def test_filter_data(self, harmonized_df):
        service = AnalyticsService()
        
        # Filter by sensor
        modis_only = service.filter_data(harmonized_df, sensor="MODIS")
        assert (modis_only["instrument"] == "MODIS").all()

        # Filter by date range
        date_filtered = service.filter_data(harmonized_df, start_date="2023-01-01", end_date="2023-12-31")
        assert (date_filtered["year"] == 2023).all()

        # Filter by confidence
        conf_filtered = service.filter_data(harmonized_df, confidence="high")
        assert (conf_filtered["confidence_cat"] == "high").all()

        # Filter by FRP range
        frp_filtered = service.filter_data(harmonized_df, min_frp=20.0, max_frp=30.0)
        assert (frp_filtered["frp"] >= 20.0).all()
        assert (frp_filtered["frp"] <= 30.0).all()

        # Filter by specific satellite
        sat_filtered = service.filter_data(harmonized_df, satellite="Aqua")
        assert (sat_filtered["satellite"] == "Aqua").all()

        # Filter by daynight
        dn_filtered = service.filter_data(harmonized_df, daynight="D")
        assert (dn_filtered["daynight"] == "D").all()

    def test_empty_dataframe_handling(self):
        service = AnalyticsService()
        empty_df = pd.DataFrame()
        metadata = {"bbox": [-120.0, 35.0, -115.0, 40.0]}

        kpis = service.get_overview_kpis(empty_df, metadata)
        assert kpis["total_detections"] == 0
        assert kpis["aoi_surface_area_km2"] is not None
        assert kpis["aoi_surface_area_km2"] > 0

        cal = service.get_burning_activity_calendar(empty_df)
        assert cal["matrix"] == []

        hist = service.get_historical_analysis(empty_df)
        assert hist["monthly_series"] == []

        comp = service.get_sensor_comparison(empty_df)
        assert comp["modis_stats"] == {}

        anom = service.detect_anomalies(empty_df)
        assert anom["monthly_anomalies"] == []

    def test_overview_kpis(self, harmonized_df):
        service = AnalyticsService()
        metadata = {"source": "test"}
        kpis = service.get_overview_kpis(harmonized_df, metadata)

        assert kpis["total_detections"] == len(harmonized_df)
        assert kpis["modis_detections"] > 0
        assert kpis["viirs_detections"] > 0
        assert kpis["total_frp_mw"] > 0
        assert kpis["total_footprint_km2"] > 0
        assert "high" in kpis["confidence_breakdown"]

    def test_burning_activity_calendar(self, harmonized_df):
        service = AnalyticsService()
        calendar = service.get_burning_activity_calendar(harmonized_df)

        assert "matrix" in calendar
        assert len(calendar["years"]) == 5
        assert len(calendar["months"]) == 12
        assert calendar["max_count"] >= 180  # Peak surge in 2023-08

        # Check row structure
        first_row = calendar["matrix"][0]
        assert "year" in first_row
        assert len(first_row["months"]) == 12

    def test_historical_analysis(self, harmonized_df):
        service = AnalyticsService()
        hist = service.get_historical_analysis(harmonized_df)

        assert "monthly_series" in hist
        assert "seasonal_baseline" in hist
        assert "yearly_trends" in hist
        assert len(hist["seasonal_baseline"]) == 12
        # August must be recognized as peak month
        assert "Aug" in hist["peak_months"]

    def test_sensor_comparison(self, harmonized_df):
        service = AnalyticsService()
        comp = service.get_sensor_comparison(harmonized_df)

        assert "modis_stats" in comp
        assert "viirs_stats" in comp
        assert "frp_quantiles" in comp
        assert "scientific_comparison_notes" in comp
        assert comp["modis_stats"]["count"] > 0
        assert comp["viirs_stats"]["count"] > 0

    def test_anomaly_detection_identifies_extreme_event(self, harmonized_df):
        service = AnalyticsService()
        anomalies = service.detect_anomalies(harmonized_df)

        assert "monthly_anomalies" in anomalies
        assert anomalies["extreme_months_count"] >= 1

        # August 2023 had 160 points vs ~50 baseline -> must be detected as Extreme
        aug_2023 = [a for a in anomalies["monthly_anomalies"] if a["year_month"] == "2023-08"][0]
        assert aug_2023["severity"] in ("extreme", "high")
        assert aug_2023["z_score"] > 1.5
        assert aug_2023["pct_of_baseline"] > 200.0
