# PyroNexa 26 — System Architecture

## 1. High-Level Overview

**PyroNexa** is an Earth observation intelligence platform engineered for the **2026 NASA Space Apps Challenge: Harmonization of MODIS and VIIRS Hot Spots**. It provides a scientifically responsible pipeline that ingests, cleans, harmonizes, analyzes, and visualizes thermal active fire observations from NASA's flagship satellites:
- **MODIS**: Terra (EOS AM-1) & Aqua (EOS PM-1)
- **VIIRS**: Suomi NPP, NOAA-20 (JPSS-1), NOAA-21 (JPSS-2)

```
┌────────────────────────────────────────────────────────────────────────┐
│                        NASA FIRMS API / LANCE                          │
│     (MODIS MOD14/MYD14 & VIIRS VNP14IMGTDL/VJ114IMGTDL/VJ214IMGTDL)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ CSV Stream (Live Key / Sample Fallback)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        Backend Services (Flask)                        │
│                                                                        │
│  ┌───────────────────────┐        ┌──────────────────────────────────┐ │
│  │   FIRMSService        │        │   HarmonizationService           │ │
│  │   - Area queries      │───────>│   - Common schema standardization│ │
│  │   - Cache layer (TTL) │        │   - Footprint area calculation   │ │
│  │   - Rate limiting     │        │   - 0.25° Spatial grid binning   │ │
│  │   - Fallback engine   │        │   - Coincident cluster detection │ │
│  └───────────────────────┘        │   - Relative Fire Activity Index │ │
│                                   └────────────────┬─────────────────┘ │
│                                                    │                   │
│                                                    ▼                   │
│                                   ┌──────────────────────────────────┐ │
│                                   │   AnalyticsService               │ │
│                                   │   - KPI rollups & summaries      │ │
│                                   │   - Year-vs-Month Matrix Heatmap │ │
│                                   │   - Seasonal baseline curves     │ │
│                                   │   - Z-Score & MAD Anomaly Engine │ │
│                                   │   - Sensor comparisons & FRP     │ │
│                                   └────────────────┬─────────────────┘ │
└────────────────────────────────────────────────────┼───────────────────┘
                                                     │ JSON REST Endpoints
                                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 Frontend User Interface (SPA)                          │
│                                                                        │
│  ┌─────────────────────────┐  ┌──────────────────────────────────────┐ │
│  │  Interactive Leaflet    │  │  Scientific Visualizations (Plotly)  │ │
│  │  Fire Map               │  │  - Burning Activity Calendar        │ │
│  │  - Sensor color coding  │  │  - Historical timeline & baseline    │ │
│  │  - FRP-scaled markers   │  │  - Sensor comparison & RFAI lines    │ │
│  │  - Telemetry popups     │  │  - Anomaly severity classification   │ │
│  └─────────────────────────┘  └──────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  Data Explorer: Searchable, sortable, paginated table & CSV export│ │
│  └───────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Structure

### 2.1 Backend Modules (`backend/`)
- **`app.py`**: Application factory (`create_app`), Blueprint registration, security headers (`nosniff`, `SAMEORIGIN`, `XSS Protection`).
- **`config.py`**: Centralized configuration, sensor registry (`SENSOR_REGISTRY`), preset region bounding boxes (`PRESET_REGIONS`), caching thresholds.
- **`routes/api.py`**: REST API endpoints implementing standard error handling, query validation, and JSON responses.
- **`routes/views.py`**: Dashboard view controller delivering single-page application context.
- **`services/firms_service.py`**: NASA FIRMS integration, MAP key authentication verification, timeout handling, and verified fallback to local multi-year sample datasets.
- **`services/harmonization_service.py`**: Scientific normalization engine translating disparate sensor measurements into canonical models.
- **`services/analytics_service.py`**: Multi-year monthly baselines, parametric and robust non-parametric anomaly detection.
- **`services/cache_service.py`**: Thread-safe memory and disk caching mechanism respecting NASA API limits.
- **`utils/validators.py`**: Coordinate range verification, bounding box integrity checks, date interval validation.
- **`utils/geo_utils.py`**: Haversine distance calculations, 0.25° grid cell assignment, ground pixel footprint area estimations.
- **`models/fire_point.py`**: Standardized dataclass representing unified fire observations.

### 2.2 Frontend Modules (`frontend/`)
- **`templates/index.html`**: Clean semantic single-page layout featuring 8 specialized operational sections.
- **`static/css/custom.css`**: Professional dark navy aerospace theme with accessible contrast, responsive breakpoints, and custom cards.
- **`static/js/main.js`**: Core state coordinator managing navigation, global filter synchronization, and asynchronous API calls.
- **`static/js/map.js`**: Leaflet map controller rendering dark basemaps, sensor-coded markers, and NASA telemetry popups.
- **`static/js/charts.js`**: Plotly.js chart renderer handling heatmaps, time-series curves, percentile bands, and histograms.
- **`static/js/analytics.js`**: Data Explorer table coordinator with live searching, multi-column sorting, and pagination.

---

## 3. Caching Strategy
NASA FIRMS enforces query restrictions to maintain server stability. PyroNexa addresses this through a two-tiered caching mechanism:
1. **In-Memory Cache**: Fast in-memory cache for repeated regional dashboard queries during active sessions.
2. **Disk-Backed Cache (`data/cache/`)**: SHA-256 hashed parameter JSON entries with configurable TTL (default 3600 seconds). Prevents redundant external HTTP calls for unchanged bounding boxes and date ranges.

---

## 4. REST API Specification

| Endpoint | Method | Parameters | Description |
|---|---|---|---|
| `/api/health` | GET | None | Diagnostic status of service, cache, and NASA connection. |
| `/api/data-availability` | GET | None | Lists supported sensors, preset regions, and FIRMS availability. |
| `/api/fires` | GET | `region`, `sensor`, `confidence`, `start_date`, `end_date`, `page`, `per_page` | Paginated fire points matching filter criteria. |
| `/api/analytics/overview` | GET | Same as `/api/fires` | High-level KPIs, sensor counts, FRP totals, and platform provenance. |
| `/api/analytics/monthly` | GET | Same as `/api/fires` | Monthly aggregated detection counts and footprint area. |
| `/api/analytics/yearly` | GET | Same as `/api/fires` | Annual fire totals stratified by sensor. |
| `/api/analytics/calendar` | GET | Same as `/api/fires` | Year-vs-Month density matrix for the burning calendar heatmap. |
| `/api/analytics/historical` | GET | Same as `/api/fires` | Multi-year monthly timeline, 12-month baseline, and peak months. |
| `/api/analytics/comparison` | GET | Same as `/api/fires` | Comparative sensor statistics, RFAI index, and FRP quantiles. |
| `/api/analytics/anomalies` | GET | Same as `/api/fires` | Z-score and MAD monthly anomaly evaluations and severity classes. |
| `/api/export/csv` | GET | Same as `/api/fires` | Downloadable CSV file of the harmonized dataset. |
