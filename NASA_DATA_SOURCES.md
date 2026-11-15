# NASA Data Sources — PyroNexa 26

**Project:** PyroNexa – Satellite Fire Intelligence Platform  
**Challenge:** 2026 NASA Space Apps Challenge — Harmonization of MODIS and VIIRS Hot Spots  

---

## 1. Official NASA Data Platforms

PyroNexa utilizes the following official NASA Earth Science resources:

### 1.1 NASA FIRMS (Fire Information for Resource Management System)
- **Host Organization**: NASA Earth Science Data and Information System (ESDIS) Project / LANCE (Land, Atmosphere Near real-time Capability for EOS).
- **Portal URL**: https://firms.modaps.eosdis.nasa.gov/
- **API Documentation**: https://firms.modaps.eosdis.nasa.gov/api/
- **Area API Endpoint**: `https://firms.modaps.eosdis.nasa.gov/api/area/csv/[MAP_KEY]/[SOURCE]/[AREA_COORDINATES]/[DAY_RANGE]/[DATE]`
- **Data Availability Endpoint**: `https://firms.modaps.eosdis.nasa.gov/api/data_availability/`

---

## 2. Satellite Sensors & Products Referenced

### 2.1 MODIS Active Fire Products
- **Satellites**: Terra (EOS AM-1) & Aqua (EOS PM-1)
- **Product Identifiers**:
  - `MODIS_NRT` (Collection 6.1 Near-Real-Time Thermal Anomalies / Fire locations)
  - `MODIS_SP` (Collection 6.1 Standard Science Quality product)
- **Spectral Bands**: Middle-infrared (4 µm, Band 21/22) and thermal infrared (11 µm, Band 31).
- **Nominal Resolution**: 1 km at nadir.
- **Reference**: Giglio, L., Schroeder, W., & Justice, C. O. (2016). *The collection 6 MODIS active fire detection algorithm and fire products.* Remote Sensing of Environment, 178, 31-41.

### 2.2 VIIRS 375m Active Fire Products
- **Satellites**:
  - **NOAA-20 / JPSS-1** (`VIIRS_NOAA20_NRT`, `VIIRS_NOAA20_SP`, VJ114IMGTDL)
  - **NOAA-21 / JPSS-2** (`VIIRS_NOAA21_NRT`, `VIIRS_NOAA21_SP`, VJ214IMGTDL)
  - **Suomi NPP** (`VIIRS_SNPP_NRT`, `VIIRS_SNPP_SP`, VNP14IMGTDL)
- **Spectral Bands**: I-band I4 (3.74 µm) and I5 (11.45 µm).
- **Nominal Resolution**: 375 meters across the entire 3,040 km swath with 3:1 sample aggregation.
- **Reference**: Schroeder, W., Oliva, P., Giglio, L., & Csiszar, I. A. (2014). *The New VIIRS 375 m active fire detection data product: Algorithm description and initial assessment.* Remote Sensing of Environment, 143, 85-96.
