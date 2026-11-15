"""PyroNexa 26 - Scientific MODIS–VIIRS Harmonization Service

Core harmonization engine addressing the NASA Space Apps Challenge:
"Harmonization of MODIS and VIIRS Hot Spots".

Implements:
1. Standardized Common Schema mapping.
2. Sensor-specific confidence interpretation (MODIS % vs VIIRS categorical).
3. Ground Footprint Area (FPA) normalization accounting for MODIS bowtie distortion vs VIIRS aggregation.
4. Spatial grid binning (0.25° / ~25km).
5. Temporal multi-scale aggregation (daily, monthly, yearly).
6. Coincident cluster / duplicate detection between overlapping overpasses.
7. Dimensionless Relative Fire Activity Index (RFAI) enabling mathematically valid
   cross-sensor comparison against independent sensor baselines.
"""

from datetime import datetime, date
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from backend.config import Config, SENSOR_REGISTRY
from backend.models.fire_point import FirePoint
from backend.utils.geo_utils import (
    get_grid_cell,
    estimate_pixel_footprint_km2,
    haversine_distance_km
)
from backend.utils.validators import validate_coordinates, parse_date_safely


class HarmonizationService:
    """Provides scientifically responsible harmonization of NASA MODIS and VIIRS active fire observations."""

    def __init__(self, grid_size_deg: float = 0.25):
        self.grid_size_deg = grid_size_deg

    def standardize_raw_dataframe(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """Convert heterogeneous raw FIRMS CSV records into a standardized canonical DataFrame."""
        if raw_df.empty:
            return pd.DataFrame(columns=[
                "latitude", "longitude", "brightness", "scan", "track",
                "acq_date", "acq_time", "satellite", "instrument",
                "confidence_raw", "confidence_cat", "confidence_pct",
                "version", "bright_t31", "frp", "daynight",
                "footprint_area_km2", "grid_cell_id", "is_duplicate"
            ])

        df = raw_df.copy()

        # Lowercase all column headers for robust field matching
        df.columns = [str(c).strip().lower() for c in df.columns]

        # 1. Standardize Coordinates
        lat_col = "latitude" if "latitude" in df.columns else "lat"
        lon_col = "longitude" if "longitude" in df.columns else "lon"
        df["latitude"] = pd.to_numeric(df[lat_col], errors="coerce")
        df["longitude"] = pd.to_numeric(df[lon_col], errors="coerce")
        df = df.dropna(subset=["latitude", "longitude"])
        df = df[(df["latitude"].between(-90, 90)) & (df["longitude"].between(-180, 180))]

        # 2. Standardize Instrument & Satellite
        if "instrument" not in df.columns:
            if "instrument_source" in df.columns:
                df["instrument"] = df["instrument_source"]
            else:
                # Infer from scan / bright_ti4 / version
                if "bright_ti4" in df.columns or "bright_ti5" in df.columns:
                    df["instrument"] = "VIIRS"
                else:
                    df["instrument"] = "MODIS"
        df["instrument"] = df["instrument"].astype(str).str.upper().str.strip()

        if "satellite" not in df.columns:
            if "satellite_source" in df.columns:
                df["satellite"] = df["satellite_source"]
            else:
                df["satellite"] = df["instrument"].map({
                    "MODIS": "Aqua",
                    "VIIRS": "NOAA-20"
                }).fillna("Unknown")

        # 3. Standardize Date and Time
        date_col = "acq_date" if "acq_date" in df.columns else "date"
        df["acq_date"] = df[date_col].astype(str).str.strip().str[:10]
        
        time_col = "acq_time" if "acq_time" in df.columns else "time"
        if time_col in df.columns:
            df["acq_time"] = df[time_col].astype(str).str.zfill(4).str[:4]
        else:
            df["acq_time"] = "1200"

        # 4. Standardize Confidence
        if "confidence" in df.columns:
            df["confidence_raw"] = df["confidence"].astype(str).str.strip().str.lower()
        elif "confidence_raw" in df.columns:
            df["confidence_raw"] = df["confidence_raw"].astype(str).str.strip().str.lower()
        elif "confidence_cat" in df.columns:
            df["confidence_raw"] = df["confidence_cat"].astype(str).str.strip().str.lower()
        elif "conf" in df.columns:
            df["confidence_raw"] = df["conf"].astype(str).str.strip().str.lower()
        else:
            df["confidence_raw"] = "nominal"

        # Categorize confidence scientifically:
        # MODIS: 0-100% -> low (<30), nominal (30-79), high (>=80)
        # VIIRS: 'l'/'low' -> low, 'n'/'nominal' -> nominal, 'h'/'high' -> high
        conf_cats = []
        conf_pcts = []
        for idx, row in df.iterrows():
            raw_c = str(row["confidence_raw"]).lower().strip()
            inst = row["instrument"]

            if inst == "MODIS":
                try:
                    pct_val = float(raw_c)
                    conf_pct = min(100.0, max(0.0, pct_val))
                    if conf_pct < 30.0:
                        cat = "low"
                    elif conf_pct < 80.0:
                        cat = "nominal"
                    else:
                        cat = "high"
                except ValueError:
                    cat = "nominal"
                    conf_pct = 60.0
            else:  # VIIRS
                if raw_c in ("h", "high"):
                    cat = "high"
                    conf_pct = 92.0
                elif raw_c in ("l", "low"):
                    cat = "low"
                    conf_pct = 25.0
                else:
                    cat = "nominal"
                    conf_pct = 65.0
            conf_cats.append(cat)
            conf_pcts.append(conf_pct)

        df["confidence_cat"] = conf_cats
        df["confidence_pct"] = conf_pcts

        # 5. Physical Radiometric Measurements
        # Brightness (Kelvin)
        b_col = "brightness" if "brightness" in df.columns else ("bright_ti4" if "bright_ti4" in df.columns else "bright")
        df["brightness"] = pd.to_numeric(df.get(b_col, 320.0), errors="coerce").fillna(320.0)

        # Brightness T31 / TI5
        t31_col = "bright_t31" if "bright_t31" in df.columns else "bright_ti5"
        df["bright_t31"] = pd.to_numeric(df.get(t31_col, np.nan), errors="coerce")

        # FRP (Fire Radiative Power, MW)
        df["frp"] = pd.to_numeric(df.get("frp", 15.0), errors="coerce").fillna(10.0)

        # Day / Night
        df["daynight"] = df.get("daynight", "D").astype(str).str.upper().str[:1]
        df["daynight"] = df["daynight"].map({"D": "D", "N": "N"}).fillna("D")

        # Version
        df["version"] = df.get("version", "NRT").astype(str)

        # Scan & Track
        df["scan"] = pd.to_numeric(df.get("scan", 1.0), errors="coerce").fillna(1.0)
        df["track"] = pd.to_numeric(df.get("track", 1.0), errors="coerce").fillna(1.0)

        # 6. Spatial Calculations: Ground Footprint Area and Spatial Grid Bin
        footprint_areas = []
        cell_ids = []
        for _, row in df.iterrows():
            area = estimate_pixel_footprint_km2(row["instrument"], row["scan"], row["track"])
            _, _, cell_id = get_grid_cell(row["latitude"], row["longitude"], self.grid_size_deg)
            footprint_areas.append(area)
            cell_ids.append(cell_id)

        df["footprint_area_km2"] = footprint_areas
        df["grid_cell_id"] = cell_ids
        if "is_duplicate" not in df.columns:
            df["is_duplicate"] = False

        # Add year, month, day columns for rapid aggregation
        df["year"] = pd.to_datetime(df["acq_date"]).dt.year
        df["month"] = pd.to_datetime(df["acq_date"]).dt.month
        df["day"] = pd.to_datetime(df["acq_date"]).dt.day

        return df

    def detect_coincident_clusters(
        self,
        df: pd.DataFrame,
        dist_threshold_km: float = 1.5,
        time_window_mins: int = 60
    ) -> pd.DataFrame:
        """Identify multi-sensor spatial coincidences between MODIS and VIIRS overpasses.
        
        When MODIS and VIIRS observe the same active fire perimeter within an overpass window
        (~13:30 local solar time), multiple VIIRS 375m pixels often cluster within a single
        MODIS 1km footprint. Identifying these links enables empirical ratio estimation.
        """
        if df.empty or len(df) < 2:
            return df

        df = df.copy()
        df["is_coincident"] = False
        df["cluster_id"] = ""

        # Only evaluate across same date
        dates = df["acq_date"].unique()
        for d in dates:
            sub = df[df["acq_date"] == d]
            modis_sub = sub[sub["instrument"] == "MODIS"]
            viirs_sub = sub[sub["instrument"] == "VIIRS"]

            if modis_sub.empty or viirs_sub.empty:
                continue

            for m_idx, m_row in modis_sub.iterrows():
                # Compare against VIIRS detections
                for v_idx, v_row in viirs_sub.iterrows():
                    dist = haversine_distance_km(
                        m_row["latitude"], m_row["longitude"],
                        v_row["latitude"], v_row["longitude"]
                    )
                    if dist <= dist_threshold_km:
                        cluster_tag = f"cluster_{d}_{m_row['grid_cell_id']}"
                        df.at[m_idx, "is_coincident"] = True
                        df.at[v_idx, "is_coincident"] = True
                        df.at[m_idx, "cluster_id"] = cluster_tag
                        df.at[v_idx, "cluster_id"] = cluster_tag

        return df

    def compute_daily_aggregation(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate observations on a daily basis stratified by sensor."""
        if df.empty:
            return pd.DataFrame()

        grouped = df.groupby(["acq_date", "instrument"]).agg(
            detection_count=("latitude", "count"),
            total_frp=("frp", "sum"),
            mean_frp=("frp", "mean"),
            total_footprint_km2=("footprint_area_km2", "sum"),
            unique_grid_cells=("grid_cell_id", "nunique"),
            mean_brightness=("brightness", "mean"),
            high_confidence_count=("confidence_cat", lambda s: (s == "high").sum()),
            nominal_confidence_count=("confidence_cat", lambda s: (s == "nominal").sum()),
            low_confidence_count=("confidence_cat", lambda s: (s == "low").sum())
        ).reset_index()

        grouped["acq_date"] = grouped["acq_date"].astype(str)
        return grouped

    def compute_monthly_aggregation(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate observations by year and month stratified by sensor."""
        if df.empty:
            return pd.DataFrame()

        df = df.copy()
        if "year" not in df.columns:
            df["year"] = pd.to_datetime(df["acq_date"]).dt.year
            df["month"] = pd.to_datetime(df["acq_date"]).dt.month

        grouped = df.groupby(["year", "month", "instrument"]).agg(
            detection_count=("latitude", "count"),
            total_frp=("frp", "sum"),
            mean_frp=("frp", "mean"),
            total_footprint_km2=("footprint_area_km2", "sum"),
            unique_grid_cells=("grid_cell_id", "nunique"),
            high_confidence_pct=("confidence_cat", lambda s: round((s == "high").mean() * 100, 1))
        ).reset_index()

        grouped["year_month"] = grouped.apply(lambda r: f"{int(r['year'])}-{int(r['month']):02d}", axis=1)
        return grouped

    def compute_yearly_aggregation(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate observations by year stratified by sensor."""
        if df.empty:
            return pd.DataFrame()

        df = df.copy()
        if "year" not in df.columns:
            df["year"] = pd.to_datetime(df["acq_date"]).dt.year

        grouped = df.groupby(["year", "instrument"]).agg(
            detection_count=("latitude", "count"),
            total_frp=("frp", "sum"),
            mean_frp=("frp", "mean"),
            total_footprint_km2=("footprint_area_km2", "sum"),
            unique_grid_cells=("grid_cell_id", "nunique")
        ).reset_index()

        return grouped

    def compute_spatial_grid_summary(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Aggregate observations into spatial grid cells (0.25° x 0.25°).
        
        Enables spatial density comparison between MODIS and VIIRS footprints.
        """
        if df.empty:
            return []

        grid_summary = []
        for cell_id, group in df.groupby("grid_cell_id"):
            modis_pts = group[group["instrument"] == "MODIS"]
            viirs_pts = group[group["instrument"] == "VIIRS"]

            center_lat = group["latitude"].mean()
            center_lon = group["longitude"].mean()
            
            grid_summary.append({
                "grid_cell_id": cell_id,
                "center_lat": round(float(center_lat), 4),
                "center_lon": round(float(center_lon), 4),
                "total_detections": len(group),
                "modis_count": len(modis_pts),
                "viirs_count": len(viirs_pts),
                "viirs_modis_ratio": round(len(viirs_pts) / max(1, len(modis_pts)), 2) if len(modis_pts) > 0 else None,
                "total_frp": round(float(group["frp"].sum()), 1),
                "total_footprint_km2": round(float(group["footprint_area_km2"].sum()), 2),
                "mean_confidence": round(float(group["confidence_pct"].mean()), 1)
            })

        return sorted(grid_summary, key=lambda x: x["total_detections"], reverse=True)

    def calculate_relative_fire_activity_index(
        self,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Compute the Relative Fire Activity Index (RFAI) and empirical sensor comparison metrics.
        
        SCIENTIFIC METHODOLOGY:
        Instead of treating 1 VIIRS pixel as equivalent to 1 MODIS pixel, we evaluate:
        1. Separate Sensor Baselines: Calculate the multi-year monthly median for MODIS and VIIRS separately.
        2. Dimensionless Harmonized Ratio:
           RFAI_m(year, month) = Monthly_Count_m / Historical_Median_m
           This normalizes the structural difference in sensor sensitivity while preserving physical trends.
        3. Fire Pixel Area (FPA) Ratio: Total VIIRS footprint area / Total MODIS footprint area.
        4. Empirical Detection Ratio (VIIRS/MODIS count).
        """
        if df.empty:
            return {
                "overall_ratio": None,
                "area_ratio": None,
                "modis_total": 0,
                "viirs_total": 0,
                "monthly_rfai": []
            }

        df = df.copy()
        if "year" not in df.columns:
            df["year"] = pd.to_datetime(df["acq_date"]).dt.year
            df["month"] = pd.to_datetime(df["acq_date"]).dt.month

        modis_df = df[df["instrument"] == "MODIS"]
        viirs_df = df[df["instrument"] == "VIIRS"]

        modis_total = len(modis_df)
        viirs_total = len(viirs_df)

        modis_area = float(modis_df["footprint_area_km2"].sum()) if not modis_df.empty else 0.0
        viirs_area = float(viirs_df["footprint_area_km2"].sum()) if not viirs_df.empty else 0.0

        overall_ratio = round(viirs_total / max(1, modis_total), 3) if modis_total > 0 else None
        area_ratio = round(viirs_area / max(0.001, modis_area), 3) if modis_area > 0 else None

        # Calculate monthly historical medians per sensor
        monthly_modis = modis_df.groupby(["year", "month"]).size().reset_index(name="modis_count")
        monthly_viirs = viirs_df.groupby(["year", "month"]).size().reset_index(name="viirs_count")

        merged = pd.merge(monthly_modis, monthly_viirs, on=["year", "month"], how="outer").fillna(0)

        # Baseline medians by calendar month
        modis_month_medians = merged.groupby("month")["modis_count"].median().to_dict()
        viirs_month_medians = merged.groupby("month")["viirs_count"].median().to_dict()

        monthly_rfai = []
        for _, row in merged.sort_values(by=["year", "month"]).iterrows():
            y = int(row["year"])
            m = int(row["month"])
            mc = float(row["modis_count"])
            vc = float(row["viirs_count"])

            m_base = modis_month_medians.get(m, 1.0) or 1.0
            v_base = viirs_month_medians.get(m, 1.0) or 1.0

            rfai_modis = round(mc / m_base, 3)
            rfai_viirs = round(vc / v_base, 3)
            # Harmonized composite: average of normalized relative activity indices
            rfai_composite = round((rfai_modis + rfai_viirs) / 2.0, 3)

            monthly_rfai.append({
                "year": y,
                "month": m,
                "year_month": f"{y}-{m:02d}",
                "modis_count": int(mc),
                "viirs_count": int(vc),
                "detection_ratio": round(vc / max(1.0, mc), 2) if mc > 0 else None,
                "rfai_modis": rfai_modis,
                "rfai_viirs": rfai_viirs,
                "rfai_harmonized": rfai_composite
            })

        return {
            "overall_ratio": overall_ratio,
            "area_ratio": area_ratio,
            "modis_total": modis_total,
            "viirs_total": viirs_total,
            "modis_total_area_km2": round(modis_area, 1),
            "viirs_total_area_km2": round(viirs_area, 1),
            "monthly_rfai": monthly_rfai
        }


harmonization_service = HarmonizationService()
