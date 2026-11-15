# Project Summary — PyroNexa 26

**Project Title:** PyroNexa – Satellite Fire Intelligence Platform  
**Challenge:** 2026 NASA Space Apps Challenge — Harmonization of MODIS and VIIRS Hot Spots  
**Team Name:** PyroNexa 26  

---

### Executive Summary (146 words)

PyroNexa is an open-source satellite fire intelligence platform built for the 2026 NASA Space Apps Challenge to resolve the critical scientific challenge of harmonizing NASA MODIS and VIIRS active fire observations. 

Because MODIS (1 km) and VIIRS (375 m) differ ~7-fold in nadir pixel footprint, experience different off-nadir bowtie distortions, and employ distinct confidence metrics, raw hotspot counts cannot be combined without creating artificial fire trends. 

PyroNexa provides a transparent, scientifically responsible harmonization framework: standardized schema mapping, ground footprint area (FPA) normalization, 0.25° spatial grid binning, a dimensionless Relative Fire Activity Index (RFAI) calibrated against independent sensor baselines, and dual parametric/robust (Z-Score and MAD) seasonal anomaly detection. 

Featuring an interactive dark-navy dashboard with live Leaflet mapping, a Year-versus-Month burning activity calendar heatmap, multi-year historical trendlines, sensor comparison metrics, and filtered CSV exports, PyroNexa empowers researchers, land managers, and emergency responders with consistent, trustworthy fire intelligence.
