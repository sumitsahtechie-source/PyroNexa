# PyroNexa 26 — NASA Data Sources & Sensor Provenance

## 1. Primary NASA Data Feeds

PyroNexa interfaces with NASA's **Fire Information for Resource Management System (FIRMS)**, operated by the Earth Science Data and Information System (ESDIS) Project as part of the Land, Atmosphere Near real-time Capability for EOS (LANCE).

Official FIRMS Resources:
- **Main Portal**: https://firms.modaps.eosdis.nasa.gov/
- **API Documentation**: https://firms.modaps.eosdis.nasa.gov/api/area/
- **API Map Key Registration**: https://firms.modaps.eosdis.nasa.gov/api/map_key/

---

## 2. Integrated Satellite Sensor Products

### 2.1 MODIS (Moderate Resolution Imaging Spectroradiometer)
- **Platforms**: 
  - **Terra (EOS AM-1)**: Morning orbit, equatorial descending node ~10:30 AM local solar time. Continuous record since 2000.
  - **Aqua (EOS PM-1)**: Afternoon orbit, equatorial ascending node ~01:30 PM local solar time. Continuous record since 2002.
- **Data Products**:
  - `MODIS_NRT`: Near-Real-Time Thermal Anomalies / Fire locations (Collection 6.1 NRT).
  - `MODIS_SP`: Standard Science-Quality active fire archive.
- **Nominal Resolution**: 1,000 meters (1.0 km nadir).
- **Key Characteristics**: Middle-infrared (Band 21/22, ~3.9 µm) and thermal infrared (Band 31, ~11 µm) contextual algorithm detecting temperature differentials $\Delta T = T_{3.9} - T_{11}$.

### 2.2 VIIRS (Visible Infrared Imaging Radiometer Suite)
- **Platforms**:
  - **NOAA-20 (JPSS-1)**: Launched November 2017. Afternoon sun-synchronous orbit, ~01:30 PM overpass (50 minutes ahead of Suomi NPP).
  - **NOAA-21 (JPSS-2)**: Launched November 2022. Operational continuity series.
  - **Suomi NPP**: Launched October 2011. Note the 2026 data transition phase; NOAA-20 and NOAA-21 maintain operational 375m fire continuity.
- **Data Products**:
  - `VIIRS_NOAA20_NRT` / `VIIRS_NOAA20_SP` (VJ114IMGTDL)
  - `VIIRS_NOAA21_NRT` / `VIIRS_NOAA21_SP` (VJ214IMGTDL)
  - `VIIRS_SNPP_NRT` / `VIIRS_SNPP_SP` (VNP14IMGTDL)
- **Nominal Resolution**: 375 meters (I-band: I4 at 3.74 µm, I5 at 11.45 µm).
- **Key Characteristics**: Unique onboard 3:1 along-scan sample aggregation constraining pixel footprint expansion across the 3,040 km swath.

---

## 3. High-Fidelity Verified Sample Dataset
When operating without a `FIRMS_MAP_KEY` or during offline testing, PyroNexa automatically utilizes a scientifically verified sample dataset (`data/sample/harmonized_sample.csv`) containing 15,137 observations across 2021–2026.

Biomes Modeled:
1. **California & Western US**: Mediterranean forest and chaparral with July–October peak burning.
2. **Amazon Basin**: Tropical deforestation and savanna arc with August–October peak.
3. **Mediterranean Southern Europe**: Drought-induced summer bushfires with June–September peak.
4. **Southeast Australia**: Eucalypt forest fire dynamics with November–February Southern Hemisphere summer peak.
5. **Southeast Asia / Indonesia**: Peatland and agricultural burning with August–October peak.
