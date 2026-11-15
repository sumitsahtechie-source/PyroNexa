"""PyroNexa 26 - REST API Routes

Provides standard JSON endpoints for satellite active fire data,
overview statistics, time series analytics, burning activity calendar,
MODIS-VIIRS sensor comparison, anomaly detection, and CSV export.
"""

from datetime import datetime, timezone
import io
import logging
from flask import Blueprint, jsonify, request, Response, send_file
import pandas as pd

from backend.config import Config, PRESET_REGIONS, SENSOR_REGISTRY
from backend.services.firms_service import firms_service
from backend.services.harmonization_service import harmonization_service
from backend.services.analytics_service import analytics_service
from backend.services.cache_service import cache_service
from backend.utils.validators import parse_query_params, ValidationError

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({
        "success": False,
        "error": "Validation Error",
        "message": str(e)
    }), 400


@api_bp.errorhandler(Exception)
def handle_unexpected_error(e):
    logger.exception("API encountered an unexpected error")
    return jsonify({
        "success": False,
        "error": "Internal Server Error",
        "message": str(e)
    }), 500


def _get_harmonized_dataset(params: dict):
    """Retrieve raw fire data (live FIRMS or sample), standardize it, and filter."""
    bbox = params["bbox"]
    sensor = params["sensor"]
    start_date = params["start_date"]
    end_date = params["end_date"]
    confidence = params["confidence"]
    satellite = params.get("satellite")
    daynight = params.get("daynight")
    min_frp = params.get("min_frp")
    max_frp = params.get("max_frp")

    # Retrieve data
    raw_df, metadata = firms_service.get_fire_data(
        bbox=bbox,
        sensor=sensor,
        start_date=start_date,
        end_date=end_date,
        confidence=confidence
    )

    # Standardize schema and compute spatial attributes
    harmonized_df = harmonization_service.standardize_raw_dataframe(raw_df)

    # Apply strict user filters
    filtered_df = analytics_service.filter_data(
        harmonized_df,
        bbox=bbox,
        sensor=sensor,
        start_date=start_date,
        end_date=end_date,
        confidence=confidence,
        satellite=satellite,
        daynight=daynight,
        min_frp=min_frp,
        max_frp=max_frp
    )

    # Detect multi-sensor simultaneous coincident clusters
    filtered_df = harmonization_service.detect_coincident_clusters(filtered_df)

    metadata["satellite_filter"] = satellite
    metadata["daynight_filter"] = daynight
    metadata["min_frp"] = min_frp
    metadata["max_frp"] = max_frp
    metadata["total_records_returned"] = len(filtered_df)
    return filtered_df, metadata


@api_bp.route("/health", methods=["GET"])
def health_check():
    """Service health and diagnostics check."""
    firms_status = firms_service.check_api_status()
    cache_info = cache_service.get_info()

    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": "PyroNexa 26 - Satellite Fire Intelligence",
        "challenge": "2026 NASA Space Apps Challenge - Harmonization of MODIS and VIIRS Hot Spots",
        "nasa_firms": {
            "mode": firms_status["mode"],
            "configured": firms_status["configured"],
            "operational": firms_status["operational"],
            "message": firms_status["message"]
        },
        "cache": cache_info
    })


@api_bp.route("/data-availability", methods=["GET"])
def data_availability():
    """Return available sensors, preset regions, and FIRMS API status."""
    firms_status = firms_service.check_api_status()
    
    sensors_info = {
        k: {
            "display_name": v.display_name,
            "instrument": v.instrument,
            "platform": v.platform,
            "resolution_m": v.nominal_resolution_m,
            "confidence_type": v.confidence_type,
            "notes": v.notes,
            "active": v.active
        }
        for k, v in SENSOR_REGISTRY.items()
    }

    return jsonify({
        "success": True,
        "firms_status": firms_status,
        "sensors": sensors_info,
        "presets": PRESET_REGIONS,
        "default_region": Config.DEFAULT_REGION
    })


@api_bp.route("/config/key", methods=["POST", "DELETE"])
def configure_key():
    """Dynamically set, test, or clear the NASA FIRMS MAP key for the current session."""
    if request.method == "DELETE":
        firms_service.map_key = ""
        cache_service.clear()
        status = firms_service.check_api_status()
        return jsonify({
            "success": True,
            "status": status,
            "mode": status["mode"],
            "operational": status["operational"],
            "message": "FIRMS API key removed. Switched to scientific simulation mode."
        })

    data = request.get_json(silent=True) or {}
    new_key = str(data.get("firms_map_key", "")).strip()

    firms_service.map_key = new_key
    # Clear cache so subsequent queries fetch fresh live data
    cache_service.clear()
    status = firms_service.check_api_status()

    return jsonify({
        "success": True,
        "status": status,
        "mode": status["mode"],
        "operational": status["operational"],
        "message": status["message"]
    })


@api_bp.route("/fires", methods=["GET"])
def get_fires():
    """Retrieve active fire observation points with pagination and spatial metadata."""
    params = parse_query_params(request.args)
    df, metadata = _get_harmonized_dataset(params)

    page = params["page"]
    per_page = params["per_page"]
    total = len(df)

    # Pagination slice
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_df = df.iloc[start_idx:end_idx]

    records = [
        {
            "latitude": round(float(r["latitude"]), 5),
            "longitude": round(float(r["longitude"]), 5),
            "brightness": round(float(r["brightness"]), 1),
            "scan": round(float(r["scan"]), 2),
            "track": round(float(r["track"]), 2),
            "acq_date": str(r["acq_date"]),
            "acq_time": str(r["acq_time"]),
            "satellite": str(r["satellite"]),
            "instrument": str(r["instrument"]),
            "confidence_raw": str(r["confidence_raw"]),
            "confidence_cat": str(r["confidence_cat"]),
            "confidence_pct": round(float(r["confidence_pct"]), 1),
            "frp": round(float(r["frp"]), 1),
            "daynight": str(r["daynight"]),
            "footprint_area_km2": round(float(r["footprint_area_km2"]), 3),
            "grid_cell_id": str(r["grid_cell_id"]),
            "is_coincident": bool(r.get("is_coincident", False)),
            "cluster_id": str(r.get("cluster_id", "") or "")
        }
        for _, r in page_df.iterrows()
    ]

    return jsonify({
        "success": True,
        "metadata": metadata,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_records": total,
            "total_pages": max(1, (total + per_page - 1) // per_page)
        },
        "data": records
    })


@api_bp.route("/analytics/overview", methods=["GET"])
def analytics_overview():
    """Return high-level summary KPIs and sensor distribution metrics."""
    params = parse_query_params(request.args)
    df, metadata = _get_harmonized_dataset(params)
    kpis = analytics_service.get_overview_kpis(df, metadata)

    return jsonify({
        "success": True,
        "data": kpis
    })


@api_bp.route("/analytics/monthly", methods=["GET"])
def analytics_monthly():
    """Return monthly aggregated time series across multi-year record."""
    params = parse_query_params(request.args)
    df, metadata = _get_harmonized_dataset(params)
    monthly_data = harmonization_service.compute_monthly_aggregation(df)

    return jsonify({
        "success": True,
        "metadata": metadata,
        "data": monthly_data.to_dict(orient="records") if not monthly_data.empty else []
    })


@api_bp.route("/analytics/yearly", methods=["GET"])
def analytics_yearly():
    """Return yearly aggregated trends stratified by sensor."""
    params = parse_query_params(request.args)
    df, metadata = _get_harmonized_dataset(params)
    yearly_data = harmonization_service.compute_yearly_aggregation(df)

    return jsonify({
        "success": True,
        "metadata": metadata,
        "data": yearly_data.to_dict(orient="records") if not yearly_data.empty else []
    })


@api_bp.route("/analytics/calendar", methods=["GET"])
def analytics_calendar():
    """Return Year-vs-Month matrix for the Burning Activity Calendar."""
    params = parse_query_params(request.args)
    df, metadata = _get_harmonized_dataset(params)
    calendar_data = analytics_service.get_burning_activity_calendar(df)

    return jsonify({
        "success": True,
        "metadata": metadata,
        "data": calendar_data
    })


@api_bp.route("/analytics/historical", methods=["GET"])
def analytics_historical():
    """Return historical seasonal baselines, monthly trends, and peak activity months."""
    params = parse_query_params(request.args)
    df, metadata = _get_harmonized_dataset(params)
    hist_data = analytics_service.get_historical_analysis(df)

    return jsonify({
        "success": True,
        "metadata": metadata,
        "data": hist_data
    })


@api_bp.route("/analytics/comparison", methods=["GET"])
def analytics_comparison():
    """Return detailed MODIS vs VIIRS sensor comparison, RFAI index, and quantiles."""
    params = parse_query_params(request.args)
    df, metadata = _get_harmonized_dataset(params)
    comp_data = analytics_service.get_sensor_comparison(df)

    return jsonify({
        "success": True,
        "metadata": metadata,
        "data": comp_data
    })


@api_bp.route("/analytics/anomalies", methods=["GET"])
def analytics_anomalies():
    """Return statistical anomaly detection results (Z-Score & MAD)."""
    params = parse_query_params(request.args)
    df, metadata = _get_harmonized_dataset(params)
    anomaly_data = analytics_service.detect_anomalies(df)

    return jsonify({
        "success": True,
        "metadata": metadata,
        "data": anomaly_data
    })


@api_bp.route("/export/csv", methods=["GET"])
def export_csv():
    """Export the filtered, harmonized dataset as a downloadable CSV."""
    params = parse_query_params(request.args)
    df, metadata = _get_harmonized_dataset(params)

    # Prepare export dataframe with clean headers
    export_cols = [
        "latitude", "longitude", "brightness", "scan", "track",
        "acq_date", "acq_time", "satellite", "instrument",
        "confidence_raw", "confidence_cat", "confidence_pct",
        "bright_t31", "frp", "daynight", "footprint_area_km2", "grid_cell_id",
        "is_coincident", "cluster_id"
    ]
    available_cols = [c for c in export_cols if c in df.columns]
    export_df = df[available_cols]

    # Convert to CSV in memory
    output = io.StringIO()
    # Add attribution header
    output.write(f"# PyroNexa 26 - Satellite Fire Intelligence Harmonized Export\n")
    output.write(f"# NASA FIRMS Attribution: {metadata['attribution']}\n")
    now_utc = datetime.now(timezone.utc)
    output.write(f"# Export Date: {now_utc.isoformat()}\n")
    output.write(f"# Region Preset: {params.get('region', 'custom')}\n")
    output.write(f"# Sensor Filter: {params.get('sensor', 'ALL')}\n")
    output.write(f"# Satellite Filter: {params.get('satellite', 'all')}\n")
    output.write(f"# Confidence Filter: {params.get('confidence', 'all')}\n")
    output.write(f"# Day/Night Filter: {params.get('daynight', 'all')}\n")
    if params.get('min_frp') is not None or params.get('max_frp') is not None:
        output.write(f"# FRP Filter: min={params.get('min_frp')}, max={params.get('max_frp')} MW\n")
    export_df.to_csv(output, index=False)

    mem = io.BytesIO()
    mem.write(output.getvalue().encode("utf-8"))
    mem.seek(0)

    filename = f"pyronexa_fires_{params.get('region', 'custom')}_{now_utc.strftime('%Y%m%d_%H%M%S')}.csv"

    return send_file(
        mem,
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename
    )
