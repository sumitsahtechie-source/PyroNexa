# Known Limitations & Scientific Boundaries — PyroNexa 26

**Project:** PyroNexa – Satellite Fire Intelligence Platform  
**Challenge:** 2026 NASA Space Apps Challenge — Harmonization of MODIS and VIIRS Hot Spots  
**Document Classification:** Scientific Integrity & Technical Transparency  

---

## 1. Executive Summary

PyroNexa is designed to provide scientifically defensible, transparent, and robust comparisons of NASA MODIS and VIIRS active fire observations. In adherence to NASA Earth Science standards, this document explicitly articulates the physical, sensor, orbital, atmospheric, and operational boundaries of satellite thermal anomaly observations and our harmonization framework.

---

## 2. Sensor & Physical Discrepancies

### 2.1 Spatial Resolution Gap & Non-Equivalence
- **The Physical Reality**: MODIS has a nominal nadir spatial resolution of 1,000 meters (1.0 km² ground pixel area), whereas the VIIRS I-band (I4/I5) has a nominal nadir resolution of 375 meters (0.14 km² ground pixel area).
- **Sub-Pixel Detection**: Active fire detection algorithms trigger on sub-pixel thermal radiation. A small flaming fire of approximately $100\text{ m}^2$ can saturate a 375m VIIRS pixel and trigger an active fire flag, while the same fire may not produce sufficient radiant flux to exceed background thermal noise within a 1,000m MODIS pixel.
- **Count Incompatibility**: A single large wildfire complex typically yields 3.0 to 4.5 times more active VIIRS pixels than MODIS pixels for the identical ground fire perimeter. **Raw pixel counts must never be treated as directly interchangeable.**

### 2.2 Off-Nadir Swath Geometry (The Bowtie Effect)
- **MODIS Panoramic Distortion**: As the scan angle increases away from nadir towards the edge of swath ($\pm 55^\circ$), MODIS pixels expand geometrically by a factor of ~5 in the scan direction and ~2 in the track direction, reaching ground footprints of up to $9.6\text{ km}^2$. Consecutive scan lines overlap significantly near the swath edges (the "bowtie effect"), occasionally causing duplicate thermal detections of the same fire.
- **VIIRS Sample Aggregation**: VIIRS mitigates panoramic distortion using onboard 3:1 along-scan sample aggregation, constraining pixel ground area growth to $\le 0.60\text{ km}^2$ even at the swath edge ($\pm 56^\circ$).
- **Harmonization Handling**: PyroNexa computes the physical ground footprint area ($A = \text{scan} \times \text{track}$) for each observation rather than treating each point as an identical unit area. However, sub-pixel fire geometry remains unresolved without high-resolution airborne hyperspectral imaging.

---

## 3. Orbital Geometry & Temporal Sampling

### 3.1 Overpass Times & Diurnal Fire Cycles
- **Orbital Phasing**:
  - **MODIS Terra**: Sun-synchronous descending equator crossing at ~10:30 AM local time / ascending at ~10:30 PM.
  - **MODIS Aqua**: Sun-synchronous ascending equator crossing at ~1:30 PM local time / descending at ~1:30 AM.
  - **VIIRS (Suomi-NPP, NOAA-20, NOAA-21)**: Sun-synchronous ascending equator crossing at ~1:30 PM local time / descending at ~1:30 AM.
- **Diurnal Burning Sensitivity**: Most vegetative wildfires exhibit pronounced diurnal cycles, peaking in convective intensity and spread rate during early-to-mid afternoon (14:00–16:00 local solar time) when relative humidity is lowest and wind speeds peak.
- **Consequence**: Aqua and VIIRS overpasses systematically detect higher Fire Radiative Power (FRP) and greater numbers of active pixels than Terra's morning overpass (10:30 AM), reflecting temporal fire behavior rather than sensor sensitivity alone.

---

## 4. Atmospheric & Environmental Obscuration

### 4.1 Cloud Cover & Rain Attenuation
- Satellite thermal radiometers operating in the mid-infrared (3.7–4.0 µm) and longwave thermal infrared (10.5–12.0 µm) wavelengths cannot penetrate thick cloud decks, deep marine stratus, or precipitation cells.
- A severe ground fire occurring beneath dense meteorological overcast will remain completely undetected by both MODIS and VIIRS until cloud dissipation occurs.

### 4.2 Dense Smoke & Pyrocumulonimbus (PyroCb) Obscuration
- While mid-infrared wavelengths penetrate moderate diffuse smoke veils far better than optical visible bands, extremely dense smoke plumes and pyrocumulonimbus cloud towers (containing condensed moisture and heavy ash) attenuate surface thermal radiance.
- Sub-pixel smoldering combustion beneath heavy smoke can be obscured or produce degraded FRP measurements.

---

## 5. Algorithmic & Analytical Boundaries

### 5.1 Active Fire Hotspots vs. Burnt Area
- **Important Distinction**: Active fire detections represent instantaneous thermal radiation observed at the exact moment of satellite overpass (a "snapshot" in time).
- **Not Ground Perimeter**: PyroNexa's hotspot points and footprint areas do not represent post-fire burnt area perimeters. Burned area mapping requires multispectral spectral reflectance differencing (e.g. Normalized Burn Ratio / dNBR from Landsat or Sentinel-2) acquired after fire containment.

### 5.2 Relative Fire Activity Index (RFAI) Context
- The RFAI normalizes fire activity by evaluating observed pixel counts against independent multi-year monthly medians for each sensor family ($RFAI = \text{Count} / \widetilde{\text{Count}}_{month}$).
- While RFAI successfully cancels out first-order sensor sensitivity discrepancies across different decades, it remains sensitive to local baseline duration: in regions with fewer historical observation years, baseline estimates have wider statistical confidence intervals.

### 5.3 Anomaly Detection Scope
- PyroNexa's statistical anomaly engine utilizes parametric Z-scores and non-parametric Median Absolute Deviation (MAD) to identify statistically significant fire activity spikes relative to historical monthly norms.
- **Not a Fire Hazard Forecast**: The anomaly detection engine measures historical and near-real-time observational deviation; it is not a predictive fire weather forecast model (such as the Canadian Forest Fire Danger Rating System or US NFDRS).

---

## 6. Operational & API Boundaries

### 6.1 NASA FIRMS Query Limits
- **Temporal Query Limit**: The NASA FIRMS Area API limits continuous requests to a maximum of 10 consecutive calendar days per query to protect server capacity.
- **Rate-Limiting**: High-volume queries are subject to NASA ESDIS throttling and IP rate-limiting.
- **PyroNexa Architecture**: PyroNexa implements strict client parameter validation, an intelligent two-tier caching architecture (in-memory LRU + persistent disk SHA-256 cache), and an automated fallback to empirical multi-year simulation datasets whenever an external API key is absent or rate-limited.
