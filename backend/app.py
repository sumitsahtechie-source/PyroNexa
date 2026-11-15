"""PyroNexa 26 - Flask Application Factory

Initializes the Flask application, registers API and view blueprints,
configures static and template paths, and applies security headers.
"""

import os
from pathlib import Path
from flask import Flask
from backend.config import config_by_name, Config
from backend.routes.api import api_bp
from backend.routes.views import views_bp


def create_app(config_name: str = "default") -> Flask:
    """Create and configure a Flask application instance."""
    base_dir = Path(__file__).resolve().parent.parent
    template_dir = base_dir / "frontend" / "templates"
    static_dir = base_dir / "frontend" / "static"

    app = Flask(
        __name__,
        template_folder=str(template_dir),
        static_folder=str(static_dir)
    )

    # Load configuration
    cfg = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(cfg)

    # Register Blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(views_bp)

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    return app


if __name__ == "__main__":
    app = create_app("development")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
