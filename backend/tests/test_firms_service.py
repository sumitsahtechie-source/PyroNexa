"""PyroNexa 26 - Test Suite: NASA FIRMS Service
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from backend.services.firms_service import FIRMSService


class TestFIRMSService:
    def test_unconfigured_service(self):
        service = FIRMSService(map_key="")
        assert service.is_configured is False
        status = service.check_api_status()
        assert status["configured"] is False
        assert status["mode"] == "sample"
        assert "Operating in scientific sample data mode" in status["message"]

    def test_configured_service_mocked_success(self):
        service = FIRMSService(map_key="abcdef1234567890abcdef1234567890")
        assert service.is_configured is True

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n37.5,-119.5,330.0,0.4,0.4,2024-08-10,1330,N20,VIIRS,n,2.0NRT,295.0,15.2,D"

        with patch("requests.get", return_value=mock_resp):
            status = service.check_api_status()
            assert status["operational"] is True
            assert status["configured"] is True

    def test_configured_service_mocked_invalid_key(self):
        service = FIRMSService(map_key="abcdef1234567890abcdef1234567890")
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "Invalid MAP_KEY"

        with patch("requests.get", return_value=mock_resp):
            status = service.check_api_status()
            assert status["operational"] is False
            assert "Invalid MAP_KEY" in status["message"]

    def test_fetch_live_fire_data_mocked(self):
        service = FIRMSService(map_key="abcdef1234567890abcdef1234567890")
        mock_csv = "latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_ti5,frp,daynight\n37.5,-119.5,330.0,0.4,0.4,2024-08-10,1330,N20,VIIRS,n,2.0NRT,295.0,15.2,D"

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = mock_csv
        mock_resp.raise_for_status = MagicMock()

        with patch("requests.get", return_value=mock_resp):
            df = service.fetch_live_fire_data(
                source="VIIRS_NOAA20_NRT",
                bbox=(-120.0, 37.0, -119.0, 38.0),
                day_range=1
            )
            assert not df.empty
            assert len(df) == 1
            assert df.iloc[0]["latitude"] == 37.5

    def test_sample_dataset_loading(self):
        service = FIRMSService(map_key="")
        df, metadata = service.get_fire_data(
            bbox=(-125.0, 32.0, -114.0, 42.5),
            sensor="ALL"
        )
        assert not df.empty
        assert metadata["is_sample_data"] is True
        assert "NASA FIRMS" in metadata["attribution"]
