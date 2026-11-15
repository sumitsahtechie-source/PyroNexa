#!/usr/bin/env python3
"""PyroNexa 26 - Application Entry Point

Runs the local development server or serves as the WSGI callable for production.
"""

import os
from backend.app import create_app

env = os.environ.get("FLASK_ENV", os.environ.get("ENV", "production"))
is_dev = env in ("development", "dev") or os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true") or os.environ.get("DEBUG", "").lower() in ("1", "true")
config_key = "development" if is_dev else "production"
app = create_app(config_key)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "127.0.0.1")
    debug = is_dev
    if debug:
        print(f"🔥 Starting PyroNexa 26 on http://{host}:{port} [Mode: DEVELOPMENT, Debug: Active]")
    else:
        print(f"🔥 Starting PyroNexa 26 on http://{host}:{port} [Mode: PRODUCTION, Debug: Disabled (PIN & Tracebacks Protected)]")
    app.run(host=host, port=port, debug=debug)
