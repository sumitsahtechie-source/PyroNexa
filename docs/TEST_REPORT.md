# PyroNexa 26 — Test Execution Report

## 1. Test Suite Summary

- **Test Framework**: `pytest 9.1.1`
- **Environment**: Python 3.14.6 (macOS Darwin arm64)
- **Total Tests Collected**: 67
- **Total Passed**: 67
- **Total Failed**: 0
- **Total Errors / Warnings**: 0
- **Execution Time**: ~6.95 seconds
- **Pass Rate**: **100%**

---

## 2. Test Breakdown by Module

### 2.1 Validators & Geospatial Utilities (`backend/tests/test_validators.py` - 27 tests)
- `test_validate_coordinates_valid`: Verified exact floating point coordinates. (PASSED)
- `test_validate_coordinates_invalid_latitude`: Checked [-90.0, 90.0] bounds. (PASSED)
- `test_validate_coordinates_invalid_longitude`: Checked [-180.0, 180.0] bounds. (PASSED)
- `test_validate_coordinates_non_numeric`: Checked exception on string input. (PASSED)
- `test_validate_bbox_valid`: Checked valid bounding box ordering. (PASSED)
- `test_validate_bbox_inverted_lon`: Caught min_lon > max_lon. (PASSED)
- `test_validate_bbox_inverted_lat`: Caught min_lat > max_lat. (PASSED)
- `test_validate_bbox_zero_area`: Caught zero-area bounding boxes. (PASSED)
- `test_parse_date_safely_valid`: Verified YYYY-MM-DD parsing. (PASSED)
- `test_parse_date_safely_invalid_format`: Caught DD-MM-YYYY format. (PASSED)
- `test_parse_date_safely_invalid_calendar_day`: Caught February 31st. (PASSED)
- `test_parse_date_safely_out_of_satellite_era`: Caught pre-2000 dates. (PASSED)
- `test_validate_date_range_valid`: Verified start <= end. (PASSED)
- `test_validate_date_range_start_after_end`: Caught start > end. (PASSED)
- `test_validate_date_range_exceeds_max_days`: Enforced 10-day query limit. (PASSED)
- `test_validate_sensor_filter`: Checked all/MODIS/VIIRS options. (PASSED)
- `test_validate_confidence_filter`: Checked low/nominal/high options. (PASSED)
- `test_validate_daynight_filter`: Checked day/night overpass validation. (PASSED)
- `test_validate_satellite_filter`: Checked platform name validation. (PASSED)
- `test_validate_frp_range`: Checked non-negative FRP bounds. (PASSED)
- `test_parse_query_params_preset`: Verified preset extraction and pagination defaults. (PASSED)
- `test_haversine_distance`: Checked great-circle calculation accuracy (~559km SF to LA). (PASSED)
- `test_haversine_distance_zero`: Verified 0.0 distance for identical coordinates. (PASSED)
- `test_get_grid_cell`: Checked discrete 0.25° binning logic. (PASSED)
- `test_estimate_pixel_footprint_km2_modis`: Verified nadir (1.0 km²) and edge (9.6 km²) bowtie expansion. (PASSED)
- `test_estimate_pixel_footprint_km2_viirs`: Verified VIIRS 3:1 aggregation constraint (<= 0.6 km²). (PASSED)
- `test_is_within_bbox`: Checked spatial containment logic. (PASSED)

### 2.2 Harmonization Service (`backend/tests/test_harmonization.py` - 9 tests)
- `test_standardize_raw_dataframe`: Verified column canonicalization, MODIS Bayesian % mapping, and VIIRS categorical conversion. (PASSED)
- `test_standardize_empty_dataframe`: Checked graceful handling of empty inputs. (PASSED)
- `test_daily_aggregation`: Verified daily grouped rollups. (PASSED)
- `test_monthly_aggregation`: Verified monthly multi-year rollups. (PASSED)
- `test_spatial_grid_summary`: Verified 0.25° grid aggregation. (PASSED)
- `test_rfai_calculation`: Verified Relative Fire Activity Index computation. (PASSED)
- `test_detect_coincident_clusters`: Identified overlapping MODIS and VIIRS detections within 1.5 km and 60 min. (PASSED)
- `test_detect_coincident_clusters_rejects_separated_time`: Verifies that detections occurring >60 min apart on the same date are rejected as coincident clusters. (PASSED)
- `test_detect_coincident_clusters_rejects_separated_distance`: Verifies that detections separated by >1.5 km are rejected. (PASSED)

### 2.3 NASA FIRMS Service (`backend/tests/test_firms_service.py` - 7 tests)
- `test_unconfigured_service`: Verified graceful transition to sample mode when key is absent. (PASSED)
- `test_configured_service_mocked_success`: Verified operational live check with mock. (PASSED)
- `test_configured_service_mocked_invalid_key`: Verified rejection handling with mock. (PASSED)
- `test_fetch_live_fire_data_mocked`: Verified CSV stream parsing. (PASSED)
- `test_sample_dataset_loading`: Verified local verified sample dataset retrieval. (PASSED)
- `test_get_fire_data_live_mode_success`: Verified Live Mode querying and metadata tagging. (PASSED)
- `test_get_fire_data_live_mode_network_failure_falls_back_to_sample`: Verified network failure fallback. (PASSED)

### 2.4 Analytics & Anomaly Detection (`backend/tests/test_analytics.py` - 7 tests)
- `test_filter_data`: Verified combined spatial, sensor, and date filtering. (PASSED)
- `test_empty_dataframe_handling`: Checked graceful empty dataframe handling. (PASSED)
- `test_overview_kpis`: Verified overview summary calculations. (PASSED)
- `test_burning_activity_calendar`: Verified Year-vs-Month matrix generation. (PASSED)
- `test_historical_analysis`: Verified seasonal decomposition and peak month identification. (PASSED)
- `test_sensor_comparison`: Verified comparative ratios and FRP quantiles. (PASSED)
- `test_anomaly_detection_identifies_extreme_event`: Verified detection of seasonal fire surge via Z-score and MAD. (PASSED)

### 2.5 Flask Routes & REST Endpoints (`backend/tests/test_routes.py` - 17 tests)
- `test_health_endpoint`: HTTP 200 and system health JSON. (PASSED)
- `test_data_availability_endpoint`: HTTP 200 and sensor registry listing. (PASSED)
- `test_index_view`: HTTP 200 and HTML single-page dashboard rendering. (PASSED)
- `test_get_fires_endpoint`: HTTP 200, pagination metadata, and fire point payload. (PASSED)
- `test_get_fires_invalid_bbox_returns_400`: Caught invalid bounds with HTTP 400. (PASSED)
- `test_analytics_overview_endpoint`: HTTP 200 and KPI metrics. (PASSED)
- `test_analytics_monthly_endpoint`: HTTP 200 and monthly time series. (PASSED)
- `test_analytics_yearly_endpoint`: HTTP 200 and annual totals. (PASSED)
- `test_analytics_calendar_endpoint`: HTTP 200 and heatmap matrix. (PASSED)
- `test_analytics_historical_endpoint`: HTTP 200 and seasonal curves. (PASSED)
- `test_analytics_comparison_endpoint`: HTTP 200 and sensor stats. (PASSED)
- `test_analytics_anomalies_endpoint`: HTTP 200 and anomaly classifications. (PASSED)
- `test_export_csv_endpoint`: HTTP 200, `text/csv` header, and formatted CSV payload with NASA attribution. (PASSED)
- `test_get_fires_with_frp_and_satellite_filters`: HTTP 200 with complex combined filters. (PASSED)
- `test_get_fires_returns_coincident_fields`: HTTP 200 verifies `is_coincident` boolean and `cluster_id` string presence. (PASSED)
- `test_sensor_comparison_returns_coincident_summary`: HTTP 200 verifies `coincident_summary` dictionary in comparison payload. (PASSED)
- `test_configure_key_endpoint`: Verifies POST and DELETE operations for dynamic runtime NASA FIRMS key configuration. (PASSED)
