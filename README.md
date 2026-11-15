# 🔥 PyroNexa 26 — Satellite Fire Intelligence Platform

[![NASA Space Apps Challenge 2026](https://img.shields.io/badge/NASA%20Space%20Apps-2026%20Challenge-orange.svg)](https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/)
[![Python](https://img.shields.io/badge/Python-3.11%2B%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask%203.1-black.svg)](https://palletsprojects.com/p/flask/)
[![Tests](https://img.shields.io/badge/Tests-67%20Passed%20(100%25)-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Team**: PyroNexa 26  
> **Challenge**: Harmonization of MODIS and VIIRS Hot Spots  
> **Challenge URL**: [NASA Space Apps Challenge 2026 — Harmonization of MODIS and VIIRS Hot Spots](https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/)  
> **Primary Data Platform**: NASA FIRMS (Fire Information for Resource Management System)

---

## 📌 Project Overview

**PyroNexa 26** is an enterprise-grade, scientifically responsible Earth observation intelligence platform developed for the **2026 NASA Space Apps Challenge**. The platform bridges active fire observations from NASA's two flagship polar-orbiting satellite sensor constellations: **MODIS** (Terra and Aqua) and **VIIRS** (Suomi-NPP, NOAA-20, and NOAA-21).

PyroNexa provides researchers, wildfire incident commanders, climatologists, and emergency managers with transparent cross-sensor comparisons, continuous multi-year fire trajectory analysis, and climatological seasonal anomaly detection.

---

## ⚠️ Problem Statement: Why Raw Fire Counts Cannot Be Combined

MODIS and VIIRS detect active thermal anomalies using distinct optical resolutions, orbital scan geometries, and detection thresholds:
1. **Spatial Resolution Discrepancy**: MODIS operates at a nominal nadir resolution of **$1{,}000\text{ m}$ ($\approx 1.0\text{ km}^2$)**, whereas VIIRS I-band operates at **$375\text{ m}$ ($\approx 0.14\text{ km}^2$)**—yielding a **$\sim$7x ground footprint area difference at nadir**. Over the same fire perimeter, VIIRS typically detects **$3.0\times$ to $4.5\times$ more active pixels** than MODIS because its finer resolution resolves small flaming fronts and fragmented agricultural burns that fall below MODIS detection limits.
2. **Off-Nadir Swath Expansion (Panoramic Bowtie Distortion)**: MODIS pixels expand dramatically toward swath edges, growing from $1.0\text{ km}^2$ at nadir to **up to $9.6\text{ km}^2$ at scan limits**. Conversely, VIIRS applies unique along-scan 3:1 sample aggregation, constraining its edge pixels to **$\le 0.60\text{ km}^2$**.
3. **Incompatible Confidence Metrics**: MODIS FIRMS feeds output Bayesian probability percentages ($0\text{--}100\%$), while VIIRS feeds provide categorical classification flags (`'l'`, `'n'`, `'h'`).

> **Scientific Consequence**: Simply summing or directly comparing raw MODIS and VIIRS hotspot counts creates artificial surges in historical fire trends, falsely suggests wildfire acceleration, and distorts environmental policy.

---

## 💡 The PyroNexa Solution: Harmonization Framework

PyroNexa establishes a defensible mathematical and spatial framework to reconcile observations without fabricating equivalence:

1. **Canonical Schema Standardization**: Normalizes disparate NASA FIRMS formats, coordinates, timestamps (UTC), and maps sensor confidences into three standardized tiers: *Low*, *Nominal*, and *High*.
2. **Ground Footprint Area (FPA) Normalization**: Computes actual physical ground footprint area ($A = \text{scan} \times \text{track}$) for each observation using orbital geometry rather than treating each point as an equal 1-unit detection.
3. **Discrete 0.25° Spatial Grid Binning**: Aggregates detections into resolution-independent spatial cells ($\approx 25\text{ km} \times 25\text{ km}$) to track burning area and active front density.
4. **Simultaneous Multi-Sensor Coincident Clustering**: Identifies simultaneous observations within both spatial ($\le 1.5\text{ km}$) and orbital temporal ($\le 60\text{ min}$) boundaries, isolating empirical sub-pixel resolution multipliers and mapping coincident clusters with cyan halo rings.
5. **Relative Fire Activity Index (RFAI)**: Evaluates dimensionless normalized activity relative to each sensor's historical calendar-month baseline:
   $$\text{RFAI}_{sensor}(y, m) = \frac{\text{Count}_{sensor}(y, m)}{\text{Median}_{sensor}(m)}$$
   $$\text{RFAI}_{composite} = \frac{\text{RFAI}_{MODIS} + \text{RFAI}_{VIIRS}}{2}$$
6. **Seasonal Anomaly Engine (Dual Z-Score + Robust MAD)**: Detects statistically significant surges relative to historical calendar-month baselines, preventing seasonal cycle false alarms:
   $$Z = \frac{x - \bar{x}_m}{s_m}, \quad \text{Modified } Z = \frac{0.6745 \cdot (x - \widetilde{x}_m)}{\text{MAD}_m}$$

---

## 🛰️ NASA FIRMS Data Sources & Attribution

PyroNexa integrates official NASA FIRMS products operated by NASA EOSDIS and LANCE:
- **MODIS (Terra & Aqua)**: Collection 6.1 NRT & Standard Science products (`MODIS_NRT`, `MODIS_SP`).
- **VIIRS (NOAA-20 / JPSS-1 & NOAA-21 / JPSS-2)**: 375m active fire products (`VIIRS_NOAA20_NRT`, `VIIRS_NOAA21_NRT`).
- **VIIRS (Suomi NPP)**: Historical 375m record (`VIIRS_SNPP_NRT`), accounting for the 2026 Suomi NPP lifecycle transition.
- **Attribution**: NASA FIRMS (Fire Information for Resource Management System) / LANCE / EOSDIS, National Aeronautics and Space Administration.
- **FIRMS API Documentation**: [https://firms.modaps.eosdis.nasa.gov/api/](https://firms.modaps.eosdis.nasa.gov/api/)

---

## 🔄 Simulation Mode vs. Live NASA FIRMS Mode

PyroNexa operates transparently in two distinct data operational modes:

| Operational Mode | Trigger Condition | Data Provenance | UI Indicators |
|---|---|---|---|
| **Simulation Mode** (Default) | No `FIRMS_MAP_KEY` provided, or key cleared | **15,137 verified empirical observations** modeled from actual NASA sensor records across 5 global biomes (California, Amazon, Australia, Mediterranean, Southeast Asia) from 2021 to 2026. | Pulsing amber status pill (`#fbbf24`), amber banner alerts in Overview, and explicit CSV export header (`# Data Source: Verified Multi-Year Scientific Sample (Simulation Mode)`). |
| **Live NASA FIRMS Mode** | Valid 32-character `FIRMS_MAP_KEY` configured in `.env` or in-app modal | **Live real-time active fire CSV feeds** fetched on-demand from NASA FIRMS API servers (`firms.modaps.eosdis.nasa.gov`). | Pulsing emerald green status pill (`#34d399`), live connection badge, and explicit CSV export header (`# Data Source: Live NASA FIRMS API`). |

> [!NOTE]
> Anyone can obtain a free, instant NASA FIRMS MAP Key at [https://firms.modaps.eosdis.nasa.gov/api/map_key/](https://firms.modaps.eosdis.nasa.gov/api/map_key/). Users can enter and test their key dynamically in the application via the **"⚙️ API Key"** button without restarting the server.

---

## 🚀 Key Features & Dashboard Sections

1. **Overview**: Total hotspot volume, distinct sensor shares, empirical detection ratio, total radiative power (FRP in MW), cumulative ground footprint area (km²), and live NASA API connectivity status.
2. **Live Fire Map**: Interactive Leaflet map with OpenStreetMap default tiles, Carto Dark & Esri Satellite options, sensor-coded markers (MODIS Blue, VIIRS Orange), FRP radius scaling, **Cyan dashed coincident cluster halo rings**, and rich telemetry popups.
3. **Burning Activity Calendar**: Year-versus-Month active fire density matrix heatmap exposing monthly hotspot volume and cumulative radiative energy.
4. **Historical Analysis**: Multi-year monthly time series, 12-month climatological median curve with 25th–75th percentile envelope, and stacked annual volume trends.
5. **Sensor Comparison**: Comparative technical specifications, **4 comparison KPI cards** (Detection Ratio, Footprint Ratio, Coincident Clusters Count, Sub-Pixel Multiplier), FRP distribution quantiles, and diurnal day/night splits.
6. **Statistical Anomaly Detection**: Transparent seasonal Z-score and MAD anomaly scoring categorized into Normal, Elevated, High Anomaly, and Extreme Fire Activity ($Z \ge 3.0$).
7. **Data Explorer**: Searchable, multi-column sortable table with customizable page sizes (25, 50, 100 records), Coincident detection badge, record detail modal, and one-click filtered CSV export with NASA attribution headers.
8. **About & Science**: Complete methodology documentation, sensor registry table, and runtime API key setup modal with live testing and sample simulation fallback.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.11+ / Python 3.14, Flask 3.1, RESTful API architecture
- **Data Science & Geospatial Computing**: Pandas, NumPy, SciPy
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla ES6 modules)
- **Design & Styling**: Bootstrap 5 + Custom Dark Aerospace Theme (WCAG AAA contrast verified)
- **Mapping & Visualizations**: Leaflet.js (OpenStreetMap, Carto Dark, Esri), Plotly.js
- **Testing & Quality Assurance**: Pytest 9.1.1 (67 automated tests, 100% pass rate)
- **Configuration & Caching**: python-dotenv, Two-tier Memory/Disk Cache (SHA-256)

---

## ⚙️ Installation & Run Instructions

### Prerequisites
- Python 3.11 or higher (Python 3.14 fully supported)
- Git

### Quick Start
```bash
# 1. Clone repository
git clone https://github.com/your-username/PyroNexa.git
cd PyroNexa

# 2. Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Configure NASA FIRMS API key
cp .env.example .env
# Edit .env and paste your free FIRMS_MAP_KEY (or enter it inside the app UI)

# 5. Start the platform
python3 run.py
```

Open your browser to: **`http://127.0.0.1:5000`**

---

## 🧪 Running Automated Tests

```bash
python3 -m pytest backend/tests -v
```
All **67 unit and integration tests** execute in under 7 seconds with a **100% pass rate**:
- `test_validators.py` (27 tests): Geodetic bounds, dates, scan/track footprints, Haversine distances.
- `test_harmonization.py` (9 tests): Schema normalization, Bayesian confidence mapping, spatial/temporal coincident clustering, RFAI.
- `test_firms_service.py` (7 tests): Unconfigured fallback, mocked key validation, live stream parsing, sample loading.
- `test_analytics.py` (7 tests): KPIs, calendar matrices, historical baseline envelopes, Z-Score/MAD anomalies.
- `test_routes.py` (17 tests): Health checks, API endpoints, pagination, token redaction, CSV export.

---

## 📖 Scientific Documentation & Submission Deliverables

- [System Architecture](file:///Users/macbookpro/Desktop/PyroNexa/docs/ARCHITECTURE.md)
- [Harmonization Methodology](file:///Users/macbookpro/Desktop/PyroNexa/docs/HARMONIZATION_METHODOLOGY.md)
- [NASA Data Sources & Sensors](file:///Users/macbookpro/Desktop/PyroNexa/docs/DATA_SOURCES.md)
- [Final Implementation Report](file:///Users/macbookpro/Desktop/PyroNexa/docs/FINAL_IMPLEMENTATION_REPORT.md)
- [Final Test Report](file:///Users/macbookpro/Desktop/PyroNexa/docs/FINAL_TEST_REPORT.md)
- [Known Limitations](file:///Users/macbookpro/Desktop/PyroNexa/docs/KNOWN_LIMITATIONS.md)
- [Deployment Guide](file:///Users/macbookpro/Desktop/PyroNexa/docs/DEPLOYMENT.md)
- [NASA Submission Summary](file:///Users/macbookpro/Desktop/PyroNexa/submission/PROJECT_SUMMARY.md) (146-word executive summary)
- [NASA Submission Details](file:///Users/macbookpro/Desktop/PyroNexa/submission/PROJECT_DETAILS.md) (Full technical narrative)
- [Synthetic Intelligence Disclosure](file:///Users/macbookpro/Desktop/PyroNexa/submission/SI_DISCLOSURE.md)
- [30-Second Video Script](file:///Users/macbookpro/Desktop/PyroNexa/submission/DEMO_VIDEO_SCRIPT.md)
- [Presentation Slide Deck Outline](file:///Users/macbookpro/Desktop/PyroNexa/submission/PRESENTATION_OUTLINE.md)

---

## ⚖️ Scientific Disclaimer, Attribution & License

- **Scientific Disclaimer**: Anomaly detections reflect statistical divergence from historical satellite climatological baselines and do not constitute real-time ground fire danger ratings or wildfire spread simulations.
- **Data Attribution**: Active fire data provided courtesy of NASA FIRMS / LANCE / EOSDIS.
- **License**: Released under the [MIT License](LICENSE). Copyright © 2026 Team PyroNexa 26.
