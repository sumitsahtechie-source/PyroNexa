# Project Details — PyroNexa 26

**Project Title:** PyroNexa – Satellite Fire Intelligence Platform  
**Challenge:** 2026 NASA Space Apps Challenge — Harmonization of MODIS and VIIRS Hot Spots  
**Team Name:** PyroNexa 26  

---

## 1. Problem Description

Active fire observations from space are vital for wildfire suppression, ecological monitoring, atmospheric emissions modeling, and climate research. For over two decades, the Moderate Resolution Imaging Spectroradiometer (MODIS) onboard NASA's Terra and Aqua satellites provided the foundational global fire record. The Visible Infrared Imaging Radiometer Suite (VIIRS)—flying on Suomi NPP, NOAA-20, and NOAA-21—represents the modern operational continuity series, offering a much finer nominal resolution of 375 meters.

However, researchers and operational land managers encounter a major dilemma when attempting to conduct multi-decadal historical fire analysis across both sensor regimes:
- **Spatial Resolution Mismatch**: VIIRS pixels cover $\sim 0.14\text{ km}^2$ at nadir, whereas MODIS pixels cover $1.0\text{ km}^2$. Over identical fire perimeters, VIIRS detects 3.0x to 4.5x more hotspot pixels than MODIS.
- **Off-Nadir Distortion**: MODIS suffers from panoramic bowtie distortion where pixels expand up to $\sim 9.6\text{ km}^2$ at edge of scan. VIIRS applies onboard 3:1 sample aggregation, constraining edge pixels to $\le 0.6\text{ km}^2$.
- **Detection Sensitivity**: VIIRS resolves small burning fronts ($\sim 10\text{--}50\text{ m}^2$) that fail to trigger the MODIS sub-pixel detection threshold.
- **Incompatible Confidence Indicators**: MODIS provides a Bayesian percentage probability ($0\text{--}100\%$), while VIIRS outputs algorithmic threshold classes (`low`, `nominal`, `high`).
- **Suomi NPP 2026 Transition**: As Suomi NPP transitions its operational lifecycle, seamless data continuity must be sustained via NOAA-20 and NOAA-21.

Simply summing raw counts creates false historical trends—making fire activity falsely appear to explode with the launch of VIIRS.

---

## 2. Our Solution: PyroNexa

PyroNexa delivers an end-to-end, scientifically defensible platform that bridges MODIS and VIIRS observations into a harmonized fire intelligence environment without fabricating uncalibrated equivalence equations.

### Key Pillars:
1. **Canonical Schema Normalization**: Translates raw FIRMS CSV records from Terra, Aqua, NOAA-20, NOAA-21, and Suomi NPP into a unified schema with validated coordinates, timestamps, and standardized confidence ratings.
2. **Ground Footprint Area (FPA) Normalization**: Computes physical ground footprint area ($A = \text{scan} \times \text{track}$) for every hotspot, directly compensating for MODIS edge-of-scan bowtie pixel expansion.
3. **Discrete Spatial Grid Binning (0.25° × 0.25°)**: Bins continuous coordinates into regular spatial cells ($\sim 25\text{ km}$), tracking both detection count and unique occupied cells to provide resolution-independent fire spread metrics.
4. **Dimensionless Relative Fire Activity Index (RFAI)**: Evaluates monthly observations against each sensor's independent historical seasonal median ($RFAI = \text{Count} / \widetilde{\text{Count}}_{month}$), allowing apples-to-apples trend comparison.
5. **Seasonal Anomaly Engine**: Implements calendar-month stratified parametric Z-Score and robust Median Absolute Deviation (MAD) anomaly detection, classifying departures into Normal, Elevated, High Anomaly, and Extreme Fire Activity.
6. **Multi-Scale Interactive Dashboard**:
   - **Overview**: Real-time KPIs, sensor distribution donut charts, day/night breakdowns, and satellite provenance.
   - **Live Fire Map**: Leaflet interactive map with sensor color coding (MODIS blue vs VIIRS orange), FRP radius scaling, and telemetry popups.
   - **Burning Activity Calendar**: Year-vs-Month heatmap matrix revealing multi-year climate cycles and peak burning months.
   - **Historical Analysis**: Multi-year monthly timeline, 12-month climatological median curve with interquartile band, and annual stacked volume.
   - **Sensor Comparison**: Direct side-by-side technical evaluation, empirical detection ratio, and FRP quantiles.
   - **Data Explorer**: Searchable, multi-column sortable table with client-side pagination and one-click filtered CSV exports.
   - **NASA FIRMS Integration**: Native live API connectivity with transparent fallback to multi-year scientific sample data.

---

## 3. Technology & Architecture

- **Backend**: Python 3.11+ / Python 3.14, Flask REST API, Pandas, NumPy, SciPy.
- **Frontend**: Vanilla ES6 modules, HTML5, CSS3 with dark navy aerospace palette, Bootstrap 5.
- **Visualization**: Leaflet.js (CartoDB dark basemap, OSM Standard, Esri Imagery), Plotly.js.
- **Verification**: 60 automated Pytest unit and integration tests (100% pass rate).
- **Deployment**: Production WSGI callable (`run.py`), containerized `Dockerfile`, and `docker-compose.yml`.

---

## 4. Intended Impact & Creativity

PyroNexa transforms opaque remote sensing telemetry into actionable, transparent environmental intelligence:
- **Emergency Responders**: Gain immediate sub-pixel perimeter situational awareness via VIIRS 375m observations alongside multi-decadal MODIS fire history.
- **Climate Scientists**: Access normalized multi-decadal time series (RFAI) devoid of sensor transition artifacts.
- **Land Managers**: Pinpoint historical seasonal burning windows using the Burning Activity Calendar and detect emerging climate extremes via robust Z-score/MAD anomaly scoring.
