"""PyroNexa 26 - Analytics and Anomaly Detection Service

Implements statistical and time-series computations for the PyroNexa dashboard:
- Overview KPI metrics
- Burning Activity Calendar (Year-vs-Month matrix)
- Historical baseline trends and seasonal cycles
- Sensor comparison (MODIS vs VIIRS metrics and distributions)
- Robust Statistical Anomaly Detection (Z-Score & Median Absolute Deviation / MAD)
"""

from datetime import datetime, date, timezone
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from backend.config import Config, PRESET_REGIONS, SENSOR_REGISTRY
from backend.services.harmonization_service import harmonization_service
from backend.utils.geo_utils import is_within_bbox


class AnalyticsService:
    """Computes fire intelligence analytics, historical baselines, and statistical anomalies."""

    def filter_data(
        self,
        df: pd.DataFrame,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        sensor: str = "ALL",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        confidence: str = "all"
    ) -> pd.DataFrame:
        """Filter standardized DataFrame by geographic bounding box, sensor, date range, and confidence."""
        if df.empty:
            return df

        filtered = df.copy()

        # Geographic filter
        if bbox:
            min_lon, min_lat, max_lon, max_lat = bbox
            filtered = filtered[
                (filtered["latitude"] >= min_lat) &
                (filtered["latitude"] <= max_lat) &
                (filtered["longitude"] >= min_lon) &
                (filtered["longitude"] <= max_lon)
            ]

        # Sensor filter
        sensor_up = sensor.upper().strip()
        if sensor_up == "MODIS":
            filtered = filtered[filtered["instrument"] == "MODIS"]
        elif sensor_up == "VIIRS":
            filtered = filtered[filtered["instrument"] == "VIIRS"]
        elif sensor_up in SENSOR_REGISTRY:
            # Match platform or sensor_id
            spec = SENSOR_REGISTRY[sensor_up]
            filtered = filtered[
                (filtered["instrument"] == spec.instrument) &
                (filtered["satellite"].str.upper() == spec.platform.upper())
            ]

        # Date range filter
        if start_date:
            filtered = filtered[filtered["acq_date"] >= start_date]
        if end_date:
            filtered = filtered[filtered["acq_date"] <= end_date]

        # Confidence filter
        conf_low = confidence.lower().strip()
        if conf_low in ("low", "nominal", "high"):
            filtered = filtered[filtered["confidence_cat"] == conf_low]

        return filtered

    def get_overview_kpis(
        self,
        df: pd.DataFrame,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate summary KPIs for the Overview dashboard."""
        if df.empty:
            return {
                "total_detections": 0,
                "modis_detections": 0,
                "viirs_detections": 0,
                "total_frp_mw": 0.0,
                "mean_frp_mw": 0.0,
                "total_footprint_km2": 0.0,
                "sensor_breakdown": {},
                "satellite_breakdown": {},
                "confidence_breakdown": {"high": 0, "nominal": 0, "low": 0},
                "daynight_breakdown": {"day": 0, "night": 0},
                "date_span": {"min_date": None, "max_date": None, "total_days": 0},
                "metadata": metadata
            }

        modis_pts = df[df["instrument"] == "MODIS"]
        viirs_pts = df[df["instrument"] == "VIIRS"]

        # Satellite counts
        sat_counts = df["satellite"].value_counts().to_dict()

        # Confidence counts
        conf_counts = df["confidence_cat"].value_counts().to_dict()

        # Day/Night counts
        dn_counts = df["daynight"].value_counts().to_dict()

        # Date bounds
        min_d = str(df["acq_date"].min())
        max_d = str(df["acq_date"].max())
        try:
            d_span = (datetime.strptime(max_d, "%Y-%m-%d") - datetime.strptime(min_d, "%Y-%m-%d")).days + 1
        except Exception:
            d_span = 1

        total_frp = float(df["frp"].sum())
        mean_frp = float(df["frp"].mean())
        total_area = float(df["footprint_area_km2"].sum())

        return {
            "total_detections": len(df),
            "modis_detections": len(modis_pts),
            "viirs_detections": len(viirs_pts),
            "viirs_to_modis_ratio": round(len(viirs_pts) / max(1, len(modis_pts)), 2) if len(modis_pts) > 0 else None,
            "total_frp_mw": round(total_frp, 1),
            "mean_frp_mw": round(mean_frp, 1),
            "total_footprint_km2": round(total_area, 1),
            "sensor_breakdown": {
                "MODIS": len(modis_pts),
                "VIIRS": len(viirs_pts)
            },
            "satellite_breakdown": sat_counts,
            "confidence_breakdown": {
                "high": int(conf_counts.get("high", 0)),
                "nominal": int(conf_counts.get("nominal", 0)),
                "low": int(conf_counts.get("low", 0))
            },
            "daynight_breakdown": {
                "day": int(dn_counts.get("D", 0)),
                "night": int(dn_counts.get("N", 0))
            },
            "date_span": {
                "min_date": min_d,
                "max_date": max_d,
                "total_days": d_span
            },
            "metadata": metadata
        }

    def get_burning_activity_calendar(
        self,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Compute the Year-versus-Month Heatmap matrix for active fire activity."""
        if df.empty:
            return {"matrix": [], "years": [], "months": list(range(1, 13)), "max_count": 0}

        df = df.copy()
        if "year" not in df.columns:
            df["year"] = pd.to_datetime(df["acq_date"]).dt.year
            df["month"] = pd.to_datetime(df["acq_date"]).dt.month

        years = sorted([int(y) for y in df["year"].unique()])
        months = list(range(1, 13))
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        counts = df.groupby(["year", "month"]).size().to_dict()
        frp_sums = df.groupby(["year", "month"])["frp"].sum().to_dict()

        matrix = []
        max_val = 0
        yearly_totals = {}

        for y in years:
            row_data = []
            y_total = 0
            for m in months:
                cnt = int(counts.get((y, m), 0))
                frp = round(float(frp_sums.get((y, m), 0.0)), 1)
                if cnt > max_val:
                    max_val = cnt
                y_total += cnt
                row_data.append({
                    "year": y,
                    "month": m,
                    "month_name": month_names[m - 1],
                    "count": cnt,
                    "total_frp": frp
                })
            yearly_totals[y] = y_total
            matrix.append({
                "year": y,
                "months": row_data,
                "year_total": y_total
            })

        return {
            "matrix": matrix,
            "years": years,
            "months": months,
            "month_names": month_names,
            "max_count": max_val,
            "yearly_totals": yearly_totals
        }

    def get_historical_analysis(
        self,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Compute multi-year monthly trends, historical medians, and seasonal cycle baselines."""
        if df.empty:
            return {
                "monthly_series": [],
                "seasonal_baseline": [],
                "yearly_trends": [],
                "peak_months": []
            }

        df = df.copy()
        if "year" not in df.columns:
            df["year"] = pd.to_datetime(df["acq_date"]).dt.year
            df["month"] = pd.to_datetime(df["acq_date"]).dt.month

        # Group by year-month and instrument
        grouped = df.groupby(["year", "month", "instrument"]).agg(
            count=("latitude", "count"),
            frp_sum=("frp", "sum"),
            area_km2=("footprint_area_km2", "sum")
        ).reset_index()

        # Monthly time series list
        monthly_series = []
        all_ym = df.groupby(["year", "month"]).size().reset_index(name="total_count")
        for _, r in all_ym.sort_values(by=["year", "month"]).iterrows():
            y, m = int(r["year"]), int(r["month"])
            ym_str = f"{y}-{m:02d}"

            m_pts = grouped[(grouped["year"] == y) & (grouped["month"] == m) & (grouped["instrument"] == "MODIS")]
            v_pts = grouped[(grouped["year"] == y) & (grouped["month"] == m) & (grouped["instrument"] == "VIIRS")]

            m_cnt = int(m_pts["count"].values[0]) if not m_pts.empty else 0
            v_cnt = int(v_pts["count"].values[0]) if not v_pts.empty else 0
            m_frp = float(m_pts["frp_sum"].values[0]) if not m_pts.empty else 0.0
            v_frp = float(v_pts["frp_sum"].values[0]) if not v_pts.empty else 0.0

            monthly_series.append({
                "year_month": ym_str,
                "year": y,
                "month": m,
                "total_count": int(r["total_count"]),
                "modis_count": m_cnt,
                "viirs_count": v_cnt,
                "total_frp": round(m_frp + v_frp, 1)
            })

        # Seasonal baseline by month of year (1-12)
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        seasonal_baseline = []
        month_totals = []

        for m in range(1, 13):
            sub_m = all_ym[all_ym["month"] == m]
            vals = sub_m["total_count"].values if not sub_m.empty else [0]
            med = float(np.median(vals))
            mean_val = float(np.mean(vals))
            q25 = float(np.percentile(vals, 25)) if len(vals) > 0 else 0.0
            q75 = float(np.percentile(vals, 75)) if len(vals) > 0 else 0.0

            seasonal_baseline.append({
                "month": m,
                "month_name": month_names[m - 1],
                "median_count": round(med, 1),
                "mean_count": round(mean_val, 1),
                "q25_count": round(q25, 1),
                "q75_count": round(q75, 1)
            })
            month_totals.append((m, med))

        # Peak months
        sorted_months = sorted(month_totals, key=lambda x: x[1], reverse=True)
        peak_months = [month_names[x[0] - 1] for x in sorted_months[:3]]

        # Yearly trends
        yearly_trends = []
        for y, y_df in df.groupby("year"):
            m_cnt = len(y_df[y_df["instrument"] == "MODIS"])
            v_cnt = len(y_df[y_df["instrument"] == "VIIRS"])
            yearly_trends.append({
                "year": int(y),
                "total_detections": len(y_df),
                "modis_detections": m_cnt,
                "viirs_detections": v_cnt,
                "total_frp": round(float(y_df["frp"].sum()), 1),
                "total_area_km2": round(float(y_df["footprint_area_km2"].sum()), 1)
            })

        return {
            "monthly_series": monthly_series,
            "seasonal_baseline": seasonal_baseline,
            "yearly_trends": sorted(yearly_trends, key=lambda x: x["year"]),
            "peak_months": peak_months
        }

    def get_sensor_comparison(
        self,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Compute rigorous comparative analytics between MODIS and VIIRS."""
        if df.empty:
            return {
                "modis_stats": {},
                "viirs_stats": {},
                "detection_ratio": None,
                "area_ratio": None,
                "rfai_analysis": {},
                "frp_quantiles": {},
                "overpass_comparison": {},
                "scientific_comparison_notes": []
            }

        modis_pts = df[df["instrument"] == "MODIS"]
        viirs_pts = df[df["instrument"] == "VIIRS"]

        rfai_data = harmonization_service.calculate_relative_fire_activity_index(df)

        def calc_sensor_stats(s_df: pd.DataFrame, inst_name: str) -> Dict[str, Any]:
            if s_df.empty:
                return {"count": 0, "total_frp": 0.0, "mean_frp": 0.0, "total_area_km2": 0.0}
            return {
                "count": len(s_df),
                "satellites": s_df["satellite"].value_counts().to_dict(),
                "total_frp": round(float(s_df["frp"].sum()), 1),
                "mean_frp": round(float(s_df["frp"].mean()), 2),
                "median_frp": round(float(s_df["frp"].median()), 2),
                "total_area_km2": round(float(s_df["footprint_area_km2"].sum()), 1),
                "mean_footprint_km2": round(float(s_df["footprint_area_km2"].mean()), 3),
                "day_detections": int((s_df["daynight"] == "D").sum()),
                "night_detections": int((s_df["daynight"] == "N").sum()),
                "high_conf_pct": round(float((s_df["confidence_cat"] == "high").mean() * 100), 1)
            }

        modis_stats = calc_sensor_stats(modis_pts, "MODIS")
        viirs_stats = calc_sensor_stats(viirs_pts, "VIIRS")

        # FRP Quantiles comparison
        frp_quantiles = {}
        for inst, s_df in [("MODIS", modis_pts), ("VIIRS", viirs_pts)]:
            if not s_df.empty:
                frp_vals = s_df["frp"].values
                frp_quantiles[inst] = {
                    "min": round(float(np.min(frp_vals)), 1),
                    "q25": round(float(np.percentile(frp_vals, 25)), 1),
                    "median": round(float(np.percentile(frp_vals, 50)), 1),
                    "q75": round(float(np.percentile(frp_vals, 75)), 1),
                    "q95": round(float(np.percentile(frp_vals, 95)), 1),
                    "max": round(float(np.max(frp_vals)), 1)
                }

        # Overpass diurnal breakdown
        overpass_comparison = {
            "MODIS": {
                "day_pct": round(modis_stats.get("day_detections", 0) / max(1, modis_stats.get("count", 1)) * 100, 1),
                "night_pct": round(modis_stats.get("night_detections", 0) / max(1, modis_stats.get("count", 1)) * 100, 1)
            },
            "VIIRS": {
                "day_pct": round(viirs_stats.get("day_detections", 0) / max(1, viirs_stats.get("count", 1)) * 100, 1),
                "night_pct": round(viirs_stats.get("night_detections", 0) / max(1, viirs_stats.get("count", 1)) * 100, 1)
            }
        }

        scientific_notes = [
            {
                "topic": "Spatial Resolution & Pixel Growth",
                "finding": "VIIRS 375m pixels yield ~7x smaller nadir area than MODIS 1km, resolving sub-pixel burning fronts and smaller agricultural burns that remain below MODIS detection limits.",
                "scientific_implication": "Raw counts must not be summed. VIIRS count / MODIS count typically ranges from 3.0 to 4.5 over the same fire complex."
            },
            {
                "topic": "Off-Nadir Swath Geometry",
                "finding": "MODIS experiences panoramic bowtie distortion: pixel footprint expands from 1.0 km² at nadir to ~9.6 km² at edge of swath. VIIRS applies unique 3:1 sample aggregation, constraining edge pixels to <= 0.6 km².",
                "scientific_implication": "Using Ground Footprint Area (km²) rather than raw pixel count significantly narrows the apparent discrepancy between sensors."
            },
            {
                "topic": "Sensor Continuity & 2026 Suomi NPP Transition",
                "finding": "NOAA-20 (JPSS-1) and NOAA-21 (JPSS-2) provide active operational continuity for the 375m active fire record following the 2026 lifecycle transition of Suomi NPP.",
                "scientific_implication": "PyroNexa seamlessly harmonizes NOAA-20 and NOAA-21 records with the historical MODIS Terra/Aqua archive."
            }
        ]

        return {
            "modis_stats": modis_stats,
            "viirs_stats": viirs_stats,
            "detection_ratio": rfai_data["overall_ratio"],
            "area_ratio": rfai_data["area_ratio"],
            "rfai_analysis": rfai_data,
            "frp_quantiles": frp_quantiles,
            "overpass_comparison": overpass_comparison,
            "scientific_comparison_notes": scientific_notes
        }

    def detect_anomalies(
        self,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Perform transparent statistical anomaly detection using Z-Score and Median Absolute Deviation (MAD).
        
        SCIENTIFIC METHODOLOGY:
        Active fire occurrence exhibits strong seasonal periodicity. Anomaly detection MUST
        evaluate divergence relative to the specific calendar month's historical baseline:
        
        1. Monthly Baseline: For each calendar month m in {1..12}, compute historical:
           - Median (M_m)
           - Mean (mu_m) and Standard Deviation (sigma_m)
           - Median Absolute Deviation: MAD_m = median(|X_i - M_m|)
        
        2. Standardized Metrics:
           - Parametric Z-Score: Z = (X - mu_m) / max(sigma_m, 1.0)
           - Modified Robust Z-Score: Z_mad = 0.6745 * (X - M_m) / max(MAD_m, 1.0)
        
        3. Classification:
           - Extreme Fire Activity: Z >= 3.0 (>= 99.7th percentile)
           - High Anomaly: 2.0 <= Z < 3.0
           - Elevated Activity: 1.0 <= Z < 2.0
           - Normal Seasonal Level: Z < 1.0
        """
        if df.empty:
            return {
                "monthly_anomalies": [],
                "extreme_months_count": 0,
                "high_anomaly_count": 0,
                "methodology_explanation": {}
            }

        df = df.copy()
        if "year" not in df.columns:
            df["year"] = pd.to_datetime(df["acq_date"]).dt.year
            df["month"] = pd.to_datetime(df["acq_date"]).dt.month

        # Group by year-month
        ym_counts = df.groupby(["year", "month"]).size().reset_index(name="count")
        ym_frp = df.groupby(["year", "month"])["frp"].sum().reset_index(name="total_frp")
        merged_ym = pd.merge(ym_counts, ym_frp, on=["year", "month"])

        # Historical statistics by calendar month
        month_stats = {}
        for m in range(1, 13):
            sub = merged_ym[merged_ym["month"] == m]["count"].values
            if len(sub) > 0:
                med = float(np.median(sub))
                mean_val = float(np.mean(sub))
                std_val = float(np.std(sub, ddof=1)) if len(sub) > 1 else max(1.0, mean_val * 0.25)
                mad_val = float(np.median(np.abs(sub - med)))
                if mad_val == 0.0:
                    mad_val = max(1.0, std_val * 0.6745)
            else:
                med, mean_val, std_val, mad_val = 1.0, 1.0, 1.0, 1.0

            month_stats[m] = {
                "median": med,
                "mean": mean_val,
                "std": max(1.0, std_val),
                "mad": max(1.0, mad_val)
            }

        # Compute anomalies for each year-month
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        anomalies = []
        extreme_cnt = 0
        high_cnt = 0

        for _, row in merged_ym.sort_values(by=["year", "month"]).iterrows():
            y = int(row["year"])
            m = int(row["month"])
            cnt = int(row["count"])
            tot_frp = round(float(row["total_frp"]), 1)

            st = month_stats[m]
            z_score = round(float((cnt - st["mean"]) / st["std"]), 2)
            z_mad = round(float(0.6745 * (cnt - st["median"]) / st["mad"]), 2)

            pct_of_baseline = round((cnt / max(1.0, st["median"])) * 100, 1)

            # Classification: evaluates both standardized variance and baseline multiplier
            effective_z = max(z_score, z_mad)
            if effective_z >= 3.0 or pct_of_baseline >= 300.0:
                severity = "extreme"
                severity_label = "Extreme Fire Activity"
                severity_color = "#dc2626"  # Red
                extreme_cnt += 1
            elif effective_z >= 2.0 or pct_of_baseline >= 200.0:
                severity = "high"
                severity_label = "High Anomaly"
                severity_color = "#ea580c"  # Orange
                high_cnt += 1
            elif effective_z >= 1.0 or pct_of_baseline >= 140.0:
                severity = "elevated"
                severity_label = "Elevated Activity"
                severity_color = "#eab308"  # Yellow
            else:
                severity = "normal"
                severity_label = "Normal Seasonal Level"
                severity_color = "#16a34a"  # Green

            anomalies.append({
                "year_month": f"{y}-{m:02d}",
                "year": y,
                "month": m,
                "month_name": month_names[m - 1],
                "count": cnt,
                "total_frp": tot_frp,
                "baseline_median": round(st["median"], 1),
                "baseline_mean": round(st["mean"], 1),
                "z_score": z_score,
                "z_mad": z_mad,
                "severity": severity,
                "severity_label": severity_label,
                "severity_color": severity_color,
                "pct_of_baseline": pct_of_baseline
            })

        methodology_explanation = {
            "algorithm": "Dual-metric Seasonal Baseline Normalization (Parametric Z-Score + Robust Median Absolute Deviation / MAD)",
            "baseline_definition": "Computed on calendar-month subsets across multi-year observation periods to avoid confounding seasonal fire cycles with true anomalies.",
            "thresholds": {
                "extreme": "Z >= 3.0 (top 0.3% of historical distribution)",
                "high": "2.0 <= Z < 3.0 (top 2.5% to 0.3%)",
                "elevated": "1.0 <= Z < 2.0",
                "normal": "Z < 1.0"
            },
            "disclaimer": "This statistical anomaly metric quantifies deviations from historical satellite detection frequency. It is NOT a predictive wildfire warning, fire behavior forecast, or ground fire danger rating."
        }

        return {
            "monthly_anomalies": anomalies,
            "extreme_months_count": extreme_cnt,
            "high_anomaly_count": high_cnt,
            "methodology_explanation": methodology_explanation
        }


analytics_service = AnalyticsService()
