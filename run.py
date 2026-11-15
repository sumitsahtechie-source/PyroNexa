#!/usr/bin/env python3
"""PyroNexa 26 - Application Entry Point

Runs the local development server or serves as the WSGI callable for production.
"""

import os
from backend.app import create_app

env = os.environ.get("FLASK_ENV", "development")
app = create_app(env)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "127.0.0.1")
    debug = env == "development"
    print(f"🔥 Starting PyroNexa 26 Satellite Fire Intelligence Platform on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
