# PyroNexa 26 — Scientific MODIS–VIIRS Harmonization Methodology

## 1. The Core Scientific Challenge

NASA's active fire observation systems rely on two distinct sensor generations:
1. **MODIS (Moderate Resolution Imaging Spectroradiometer)**: Flying on **Terra** (launched 1999) and **Aqua** (launched 2002).
2. **VIIRS (Visible Infrared Imaging Radiometer Suite)**: Flying on **Suomi NPP** (launched 2011), **NOAA-20 / JPSS-1** (launched 2017), and **NOAA-21 / JPSS-2** (launched 2022).

While both instruments detect middle-infrared and thermal infrared emissions from burning biomass, they differ fundamentally across every key physical and radiometric parameter:

| Attribute | MODIS (Terra / Aqua) | VIIRS (NOAA-20 / NOAA-21 / S-NPP) | Scientific Implication |
|---|---|---|---|
| **Nominal Spatial Resolution** | 1,000 meters (1.0 km at nadir) | 375 meters (I-band active fire product) | VIIRS pixel area is ~7.1x smaller at nadir than MODIS. |
| **Minimum Fire Detection Size** | ~100–1,000 m² sub-pixel flaming area | ~10–50 m² sub-pixel flaming area | VIIRS detects small, cooler, or fragmented fires invisible to MODIS. |
| **Swath Width** | 2,330 km | 3,040 km | VIIRS leaves no equatorial orbit gaps. |
| **Off-Nadir Pixel Distortion** | Bowtie effect: 1.0 km² at nadir &rarr; ~9.6 km² at swath edge ($\pm 55^\circ$) | 3:1 along-scan sample aggregation: 0.14 km² &rarr; $\le 0.6\text{ km}^2$ at edge ($\pm 56^\circ$) | MODIS pixel counts drastically under-sample edge fires while overstating pixel area. |
| **Overpass Schedules** | Terra: 10:30 AM/PM; Aqua: 01:30 PM/AM | NOAA-20/21/S-NPP: ~01:30 PM/AM (50-min separation) | VIIRS aligns closely with Aqua solar peak, but Terra observes morning fires. |
| **Confidence Metric** | Percentage (0–100%) Bayesian probability | Categorical classes: 'low' (`l`), 'nominal' (`n`), 'high' (`h`) | Cannot be compared directly without standardization. |

> [!IMPORTANT]
> **Fundamental Harmonization Rule**: Raw hotspot counts from MODIS and VIIRS **must never be summed together** or treated as equivalent measurements. Doing so introduces severe artificial temporal trends (e.g. falsely concluding fire activity tripled when VIIRS launched).

---

## 2. PyroNexa Harmonization Framework

PyroNexa implements a multi-step analytical harmonization framework that enables rigorous historical comparisons without inventing arbitrary calibration coefficients.

```
       [Raw MODIS Records]                      [Raw VIIRS Records]
                │                                        │
                ▼                                        ▼
   ┌──────────────────────────┐             ┌──────────────────────────┐
   │ Confidence Standardization│            │Confidence Standardization│
   │ 0-100% -> low/nominal/high│            │ 'l'/'n'/'h' -> canonical │
   └────────────┬─────────────┘             └────────────┬─────────────┘
                │                                        │
                ▼                                        ▼
   ┌──────────────────────────┐             ┌──────────────────────────┐
   │ Ground Footprint Area    │             │ Ground Footprint Area    │
   │ A = scan * track (km²)   │             │ Constrained aggregation  │
   └────────────┬─────────────┘             └────────────┬─────────────┘
                │                                        │
                └───────────────────┬────────────────────┘
                                    ▼
                     ┌─────────────────────────────┐
                     │ 0.25° Spatial Grid Binning  │
                     │ cell_lat, cell_lon, cell_id │
                     └──────────────┬──────────────┘
                                    │
                                    ▼
                     ┌─────────────────────────────┐
                     │ Dimensionless Harmonization │
                     │ Relative Fire Activity Index│
                     │ RFAI = Count / Median_month │
                     └─────────────────────────────┘
```

### 2.1 Standardized Schema Normalization
Both sensor streams are parsed into a unified canonical schema:
- `latitude`, `longitude`: WGS84 coordinates rounded to 5 decimal places (~1.1m precision).
- `acq_date`, `acq_time`: ISO-8601 calendar date (`YYYY-MM-DD`) and UTC acquisition time (`HHMM`).
- `satellite`: Specific platform provenance (`Terra`, `Aqua`, `NOAA-20`, `NOAA-21`, `Suomi-NPP`).
- `instrument`: Sensor family (`MODIS` or `VIIRS`).
- `frp`: Fire Radiative Power in Megawatts (MW).
- `brightness`: 4-micron thermal brightness temperature in Kelvin.
- `footprint_area_km2`: Ground pixel area calculated from `scan` and `track`.

### 2.2 Confidence Interpretation
- **MODIS**: Bayesian percentage confidence values are mapped:
  - Low: $0\% \le \text{conf} < 30\%$
  - Nominal: $30\% \le \text{conf} < 80\%$
  - High: $\text{conf} \ge 80\%$
- **VIIRS**: Threshold algorithm flags are normalized:
  - `l` &rarr; Low (nominal benchmark 25%)
  - `n` &rarr; Nominal (nominal benchmark 65%)
  - `h` &rarr; High (nominal benchmark 92%)

### 2.3 Fire Pixel Footprint Area (FPA) Normalization
Because a single MODIS pixel at swath edge covers up to ~9.6 km² while a VIIRS pixel covers $\le 0.6\text{ km}^2$, PyroNexa evaluates the cumulative **Ground Footprint Area ($km^2$)**:
$$\text{Area}_{\text{pixel}} = \text{scan} \times \text{track}$$
$$\text{FPA}_{\text{total}} = \sum_{i=1}^{N} \text{Area}_i$$
Comparing cumulative footprint area narrows the apparent discrepancy between the sensors from $\sim 3.8\times$ in raw counts to $< 1.3\times$ in physical burning ground area.

### 2.4 Discrete Spatial Grid Binning (0.25° × 0.25°)
To resolve sub-pixel clustering, PyroNexa bins continuous points into discrete geographical cells ($\sim 25\text{ km} \times 25\text{ km}$ at the equator):
$$\text{Cell}_{\text{lat}} = \lfloor \text{lat} / 0.25 \rfloor \times 0.25$$
$$\text{Cell}_{\text{lon}} = \lfloor \text{lon} / 0.25 \rfloor \times 0.25$$
Within each cell, we track both raw detection count and the number of distinct occupied grid cells, providing a resolution-independent metric of spatial fire spread.

### 2.5 Dimensionless Relative Fire Activity Index (RFAI)
To compare long-term historical records across the 2000–present MODIS era and the 2012–present VIIRS era without fabricating unvalidated regression formulas, PyroNexa establishes **independent sensor baselines**:
1. For each sensor $s \in \{\text{MODIS}, \text{VIIRS}\}$ and calendar month $m \in \{1..12\}$, compute the historical climatological median:
   $$\widetilde{C}_{s, m} = \text{median}(\{C_{s, y, m} \mid y \in \text{historical years}\})$$
2. For any observed month, calculate the dimensionless Relative Fire Activity Index:
   $$\text{RFAI}_{s}(y, m) = \frac{C_{s, y, m}}{\widetilde{C}_{s, m}}$$
3. The composite harmonized fire index is:
   $$\text{RFAI}_{\text{harmonized}}(y, m) = \frac{\text{RFAI}_{\text{MODIS}}(y, m) + \text{RFAI}_{\text{VIIRS}}(y, m)}{2}$$

An RFAI of 1.0 represents exact normal seasonal fire activity, 2.0 indicates twice the climatological normal, and 0.5 indicates half the normal burning activity.

---

## 3. Anomaly Detection Methodology

Active fire occurrences exhibit intense seasonal periodicity. Evaluating anomaly scores across an entire year without seasonal decomposition produces false positives every summer and false negatives every winter.

PyroNexa solves this by computing **calendar-month stratified baselines**:
1. **Parametric Z-Score**:
   $$Z(y, m) = \frac{C(y, m) - \mu_m}{\sigma_m}$$
2. **Robust Modified Z-Score (Median Absolute Deviation / MAD)**:
   $$\text{MAD}_m = \text{median}(|C(y, m) - \widetilde{C}_m|)$$
   $$Z_{\text{mad}}(y, m) = \frac{0.6745 \times (C(y, m) - \widetilde{C}_m)}{\max(\text{MAD}_m, 1.0)}$$

### Severity Classification:
- **Extreme Fire Activity ($Z \ge 3.0$ or $\ge 300\%$ of baseline)**: Deviations in the top 0.3% of historical conditions.
- **High Anomaly ($2.0 \le Z < 3.0$ or $\ge 200\%$ of baseline)**: Severe departures from seasonal median.
- **Elevated Activity ($1.0 \le Z < 2.0$ or $\ge 140\%$ of baseline)**: Moderate fire weather surge.
- **Normal Seasonal Level ($Z < 1.0$)**: Within expected variability.

---

## 4. Known Scientific Limitations
1. **Cloud and Smoke Obscuration**: Thick cloud cover and dense pyrocumulonimbus plumes prevent optical/thermal detection by both sensors.
2. **Temporal Sampling Discrepancies**: Terra flies at 10:30 AM/PM, whereas Aqua and VIIRS fly at ~01:30 PM/AM. Fast-moving grass fires burning between overpasses may be detected by only one sensor.
3. **No Ground Truth Equivalency**: PyroNexa provides comparative and normalized analytical harmonization. It does not claim to convert VIIRS hotspots into exact MODIS-equivalent counts or ground burned area hectares without local land cover validation.
