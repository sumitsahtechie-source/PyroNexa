# 🔥 PyroNexa 26 — Satellite Fire Intelligence Platform

[![NASA Space Apps Challenge 2026](https://img.shields.io/badge/NASA%20Space%20Apps-2026%20Challenge-orange.svg)](https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/)
[![Python](https://img.shields.io/badge/Python-3.11%2B%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask%203.1-black.svg)](https://palletsprojects.com/p/flask/)
[![Tests](https://img.shields.io/badge/Tests-55%20Passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Team**: PyroNexa 26  
> **Challenge**: Harmonization of MODIS and VIIRS Hot Spots  
> **Data Platform**: NASA FIRMS (Fire Information for Resource Management System)

---

## 📌 Executive Summary

**PyroNexa** is an Earth observation intelligence platform engineered for the **2026 NASA Space Apps Challenge**. It provides a scientifically responsible, interactive web application that bridges NASA's flagship active fire sensors: **MODIS** (Terra & Aqua) and **VIIRS** (NOAA-20, NOAA-21, and Suomi NPP).

Due to structural differences in spatial resolution (1 km vs 375 m, ~7x area discrepancy at nadir), scan geometry (MODIS panoramic bowtie distortion vs VIIRS 3:1 along-scan aggregation), and confidence metrics (Bayesian percentage vs algorithmic classes), **raw hotspot counts cannot simply be summed or treated as equivalent**.

PyroNexa delivers a transparent harmonization framework featuring:
- **Canonical Schema Standardization** across all NASA FIRMS feeds.
- **Ground Footprint Area (FPA)** normalization accounting for pixel expansion.
- **0.25° Discrete Spatial Grid Binning** to track physical burning area.
- **Dimensionless Relative Fire Activity Index (RFAI)** comparing observations against independent multi-year historical seasonal medians.
- **Calendar-Month Stratified Anomaly Engine** (Parametric Z-Score + Robust Median Absolute Deviation / MAD).

---

## 🚀 Key Features & Dashboard Sections

1. **Overview**: Total detections, distinct MODIS vs VIIRS counts, empirical detection ratio, total Fire Radiative Power (MW), ground footprint area (km²), satellite provenance, and NASA API connectivity status.
2. **Live Fire Map**: Interactive Leaflet map with dark satellite tiles, sensor-specific color coding (Blue: MODIS 1km; Orange: VIIRS 375m), FRP-scaled radius markers, and rich NASA telemetry popups.
3. **Burning Activity Calendar**: Year-versus-Month active fire density heatmap matrix with interactive hover tooltips exposing monthly hotspot volume and cumulative radiative power.
4. **Historical Analysis**: Multi-year monthly timeline, 12-month climatological median curve with 25th–75th percentile envelope, and annual stacked volume trends.
5. **Sensor Comparison**: Side-by-side technical specs, empirical detection ratio ($VIIRS/MODIS$), pixel ground area ratio, FRP distribution quantiles, and diurnal overpass proportions.
6. **Statistical Anomaly Detection**: Transparent seasonal Z-score and MAD anomaly scoring categorized into Normal, Elevated, High Anomaly, and Extreme Fire Activity.
7. **Data Explorer**: Searchable, multi-column sortable table with client-side pagination and one-click filtered CSV export.
8. **About & Science**: In-depth scientific documentation, NASA FIRMS reference, methodology derivation, and API key setup modal.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.11+ / Python 3.14, Flask, REST API
- **Data Science & Geospatial**: Pandas, NumPy, SciPy
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla ES6 modules)
- **Styling**: Bootstrap 5 + Custom Dark Navy Aerospace Theme
- **Mapping & Visualizations**: Leaflet.js (CartoDB Dark Basemap), Plotly.js
- **Testing**: Pytest (55 automated tests, 100% pass rate), Flask Test Client
- **Configuration & Caching**: python-dotenv, Two-tiered Memory/Disk Cache

---

## 🛰️ NASA FIRMS Data Sources

- **MODIS (Terra & Aqua)**: Collection 6.1 NRT & Standard Science products (`MODIS_NRT`, `MODIS_SP`).
- **VIIRS (NOAA-20 / JPSS-1 & NOAA-21 / JPSS-2)**: 375m active fire products (`VIIRS_NOAA20_NRT`, `VIIRS_NOAA21_NRT`).
- **VIIRS (Suomi NPP)**: Historical 375m record (`VIIRS_SNPP_NRT`), accounting for the 2026 Suomi NPP lifecycle transition.
- **API Documentation**: https://firms.modaps.eosdis.nasa.gov/api/area/

---

## ⚙️ Installation & Quick Start

```bash
# 1. Clone repository
git clone https://github.com/your-org/PyroNexa.git
cd PyroNexa

# 2. Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Configure NASA FIRMS API key
cp .env.example .env
# Edit .env and insert your free FIRMS_MAP_KEY

# 5. Start the platform
python3 run.py
```
Open **`http://127.0.0.1:5000`** in your browser.

> [!NOTE]
> If `FIRMS_MAP_KEY` is not provided, PyroNexa automatically runs in **Simulation Mode** using a verified multi-year scientific sample dataset (15,137 observations across 5 global biomes from 2021 to 2026).

---

## 🧪 Running Automated Tests

```bash
python3 -m pytest backend/tests -v
```
All **55 unit and integration tests** execute in under 4 seconds with 100% pass rate.

---

## 📖 Scientific Documentation

Detailed technical documentation is available in the `docs/` directory:
- [System Architecture](file:///Users/macbookpro/Desktop/PyroNexa/docs/ARCHITECTURE.md)
- [Harmonization Methodology](file:///Users/macbookpro/Desktop/PyroNexa/docs/HARMONIZATION_METHODOLOGY.md)
- [NASA Data Sources & Sensors](file:///Users/macbookpro/Desktop/PyroNexa/docs/DATA_SOURCES.md)
- [Implementation Status](file:///Users/macbookpro/Desktop/PyroNexa/docs/IMPLEMENTATION_STATUS.md)
- [Test Report](file:///Users/macbookpro/Desktop/PyroNexa/docs/TEST_REPORT.md)
- [Deployment Guide](file:///Users/macbookpro/Desktop/PyroNexa/docs/DEPLOYMENT.md)

---

## 📄 NASA Space Apps Challenge Submission Materials

The following official submission artifacts are prepared in the repository root:
- [`PROJECT_SUMMARY.md`](file:///Users/macbookpro/Desktop/PyroNexa/PROJECT_SUMMARY.md) (50–200 word summary)
- [`PROJECT_DETAILS.md`](file:///Users/macbookpro/Desktop/PyroNexa/PROJECT_DETAILS.md) (Full technical description)
- [`SI_DISCLOSURE.md`](file:///Users/macbookpro/Desktop/PyroNexa/SI_DISCLOSURE.md) (Synthetic Intelligence disclosure)
- [`NASA_DATA_SOURCES.md`](file:///Users/macbookpro/Desktop/PyroNexa/NASA_DATA_SOURCES.md) (NASA EOSDIS / FIRMS links)
- [`OTHER_RESOURCES.md`](file:///Users/macbookpro/Desktop/PyroNexa/OTHER_RESOURCES.md) (Software and open-source credits)
- [`DEMO_VIDEO_SCRIPT.md`](file:///Users/macbookpro/Desktop/PyroNexa/DEMO_VIDEO_SCRIPT.md) (30-second video storyboard)
- [`PRESENTATION_OUTLINE.md`](file:///Users/macbookpro/Desktop/PyroNexa/PRESENTATION_OUTLINE.md) (7-slide presentation deck outline)

---

## ⚖️ Scientific Disclaimer & License

- **Scientific Notice**: Anomaly scores reflect statistical variations from historical satellite detection baselines and do not constitute real-time ground fire danger ratings or predictive wildfire behavior simulations.
- **License**: Released under the MIT License. Copyright © 2026 Team PyroNexa 26.
