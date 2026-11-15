# Presentation Slide Deck Outline — PyroNexa 26

**Competition:** 2026 NASA Space Apps Challenge  
**Challenge:** Harmonization of MODIS and VIIRS Hot Spots  
**Team:** PyroNexa 26  
**Format:** 7 Slides Maximum (NASA Guidelines)  

---

### Slide 1: Title & Vision
- **Header**: **PYRONEXA** — Satellite Fire Intelligence Platform
- **Sub-header**: Harmonizing NASA MODIS and VIIRS Active Fire Feeds for Historical Climate Resilience
- **Team**: PyroNexa 26 | 2026 NASA Space Apps Challenge
- **Visual**: High-contrast dark aerospace UI hero graphic with Earth satellite orbital tracks and active thermal fire points.

---

### Slide 2: The Scientific Dilemma
- **Header**: Why Raw Satellite Fire Counts Cannot Be Combined
- **Key Points**:
  - **Resolution Gap**: VIIRS 375m pixels have ~7x smaller nadir area than MODIS 1km, detecting 3.0x to 4.5x more active pixels over the identical fire perimeter.
  - **Bowtie Distortion**: MODIS pixels expand to ~9.6 km² at swath edge; VIIRS uses 3:1 along-scan aggregation to stay $\le 0.6\text{ km}^2$.
  - **The Risk**: Simply summing hotspot counts fabricates false climate trends and misguides emergency policy.
- **Visual**: Side-by-side footprint diagram comparing a single MODIS 1km pixel with clustered VIIRS 375m pixels.

---

### Slide 3: The PyroNexa Harmonization Framework
- **Header**: Transparent, Scientifically Defensible Normalization
- **Core Methodology**:
  - **Ground Footprint Area (FPA)**: Physical ground area calculation ($A = \text{scan} \times \text{track}$) replacing raw pixel counts.
  - **0.25° Spatial Grid Binning**: Resolution-independent tracking of occupied burning cells.
  - **Relative Fire Activity Index (RFAI)**: Dimensionless normalization against independent sensor seasonal medians ($RFAI = \text{Count} / \widetilde{\text{Count}}_{month}$).
- **Visual**: Architecture flow diagram from raw NASA FIRMS CSV feeds to the normalized analytical index.

---

### Slide 4: Interactive Live Fire Map & Telemetry
- **Header**: Spatial Situational Awareness Across Sensors
- **Key Features**:
  - Real-time Leaflet mapping with sensor color coding (MODIS Blue vs VIIRS Orange).
  - Radiative power (FRP) proportional marker sizing.
  - Detailed telemetry popups: Exact coordinates, acquisition time (UTC), sensor confidence, FRP in MW, and brightness temperature.
- **Visual**: Screenshot of California wildfire cluster plotted on the live PyroNexa interactive map.

---

### Slide 5: Burning Activity Calendar & Historical Baselines
- **Header**: Decadal Seasonal Climatology & Climate Surges
- **Key Features**:
  - **Year-versus-Month Heatmap Matrix**: Immediate visual diagnosis of regional burning seasons (e.g. Jul–Oct California; Nov–Feb Australia).
  - **Historical Baseline Curves**: 12-month median climatology with 25th–75th percentile interquartile envelope.
  - Hover telemetry exposing monthly hotspot count, total FRP, and baseline variance.
- **Visual**: The interactive Burning Activity Calendar heatmap matrix showing 2021–2026 seasonal patterns.

---

### Slide 6: Seasonal Anomaly Detection Engine
- **Header**: Detecting Statistical Deviations, Not Wildfire Predictions
- **Statistical Rigor**:
  - Dual-metric evaluation: Parametric Z-Score + Robust Median Absolute Deviation (MAD).
  - Evaluated on calendar-month subsets to eliminate seasonal cycle false alarms.
  - Transparent classification: Normal, Elevated, High Anomaly, and Extreme Fire Activity ($Z \ge 3.0$).
- **Visual**: Anomaly timeline bar chart with severity color coding and baseline threshold lines.

---

### Slide 7: Impact, Open Source, and NASA Alignment
- **Header**: Empowering Researchers, Firefighters, and Land Managers
- **Key Takeaways**:
  - Fully functional, test-verified platform with 55 passing automated tests.
  - Connects to live NASA FIRMS API or operates in verified multi-year simulation mode.
  - Open source MIT license, containerized deployment, and full CSV export capabilities.
  - **Repository & Demo**: Live on GitHub and accessible for global climate resilience.
- **Visual**: Summary graphic of team, technology stack, and NASA LANCE/FIRMS attribution.
