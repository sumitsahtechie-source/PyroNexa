"""PyroNexa 26 - Web Application View Routes

Renders the main single-page dashboard application.
"""

from flask import Blueprint, render_template
from backend.config import Config, PRESET_REGIONS, SENSOR_REGISTRY
from backend.services.firms_service import firms_service

views_bp = Blueprint("views", __name__)


@views_bp.route("/", methods=["GET"])
def index():
    """Render the PyroNexa main interactive dashboard."""
    firms_status = firms_service.check_api_status()
    
    return render_template(
        "index.html",
        preset_regions=PRESET_REGIONS,
        sensors=SENSOR_REGISTRY,
        firms_status=firms_status,
        default_region=Config.DEFAULT_REGION
    )
