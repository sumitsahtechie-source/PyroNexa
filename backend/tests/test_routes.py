"""PyroNexa 26 - Test Suite: Flask Routes and REST Endpoints
"""

import pytest
import io
import pandas as pd
from backend.app import create_app


@pytest.fixture
def client():
    app = create_app("testing")
    with app.test_client() as client:
        yield client


class TestFlaskRoutes:
    def test_health_endpoint(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"
        assert "PyroNexa 26" in data["platform"]
        assert "nasa_firms" in data

    def test_data_availability_endpoint(self, client):
        resp = client.get("/api/data-availability")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "sensors" in data
        assert "presets" in data
        assert "california" in data["presets"]

    def test_index_view(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"PYRONEXA" in resp.data
        assert b"Satellite Fire Intelligence" in resp.data

    def test_get_fires_endpoint(self, client):
        resp = client.get("/api/fires?region=california&page=1&per_page=10")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "pagination" in data
        assert "data" in data
        assert len(data["data"]) <= 10

    def test_get_fires_invalid_bbox_returns_400(self, client):
        # min_lat > max_lat
        resp = client.get("/api/fires?min_lon=-120&min_lat=45&max_lon=-115&max_lat=35")
        assert resp.status_code == 400
        data = resp.get_json()
        assert data["success"] is False
        assert "Validation Error" in data["error"]

    def test_analytics_overview_endpoint(self, client):
        resp = client.get("/api/analytics/overview?region=california")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "total_detections" in data["data"]
        assert "modis_detections" in data["data"]
        assert "viirs_detections" in data["data"]

    def test_analytics_monthly_endpoint(self, client):
        resp = client.get("/api/analytics/monthly?region=california")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_analytics_yearly_endpoint(self, client):
        resp = client.get("/api/analytics/yearly?region=california")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)

    def test_analytics_calendar_endpoint(self, client):
        resp = client.get("/api/analytics/calendar?region=california")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "matrix" in data["data"]
        assert "years" in data["data"]
        assert "months" in data["data"]

    def test_analytics_historical_endpoint(self, client):
        resp = client.get("/api/analytics/historical?region=california")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "seasonal_baseline" in data["data"]
        assert "monthly_series" in data["data"]

    def test_analytics_comparison_endpoint(self, client):
        resp = client.get("/api/analytics/comparison?region=california")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "modis_stats" in data["data"]
        assert "viirs_stats" in data["data"]
        assert "rfai_analysis" in data["data"]

    def test_analytics_anomalies_endpoint(self, client):
        resp = client.get("/api/analytics/anomalies?region=california")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "monthly_anomalies" in data["data"]
        assert "methodology_explanation" in data["data"]

    def test_export_csv_endpoint(self, client):
        resp = client.get("/api/export/csv?region=california&satellite=Aqua&min_frp=15.0")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["Content-Type"]
        assert "attachment" in resp.headers["Content-Disposition"]
        
        # Verify content can be parsed as CSV
        csv_text = resp.data.decode("utf-8")
        assert "latitude" in csv_text
        assert "longitude" in csv_text
        assert "instrument" in csv_text
        assert "confidence_cat" in csv_text
        assert "# NASA FIRMS Attribution" in csv_text
        assert "# Satellite Filter: Aqua" in csv_text
        assert "# FRP Filter: min=15.0" in csv_text

    def test_get_fires_with_frp_and_satellite_filters(self, client):
        resp = client.get("/api/fires?region=california&satellite=Terra&daynight=D&min_frp=10.0&max_frp=200.0")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        for pt in data["data"]:
            assert pt["satellite"] == "Terra"
            assert pt["daynight"] == "D"
            assert pt["frp"] >= 10.0
            assert pt["frp"] <= 200.0
