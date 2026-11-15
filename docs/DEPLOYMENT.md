# PyroNexa 26 — Production Deployment Guide

## 1. Local Development Run

### Prerequisites
- Python 3.11+
- Virtual environment (`venv`)

### Installation & Run Steps
```bash
# Clone the repository
git clone https://github.com/your-org/PyroNexa.git
cd PyroNexa

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Configure NASA FIRMS API key
cp .env.example .env
# Edit .env and set FIRMS_MAP_KEY=your_key_here

# Run the application
python3 run.py
```
Access the application at `http://127.0.0.1:5000`.

---

## 2. Running Automated Tests
```bash
# Execute full test suite
python3 -m pytest backend/tests -v
```

---

## 3. Containerized Deployment (Docker)

PyroNexa includes a production-ready `Dockerfile` and `.dockerignore`.

```bash
# Build the Docker image
docker build -t pyronexa:latest .

# Run container with optional NASA FIRMS key
docker run -d -p 5000:5000 \
  -e FIRMS_MAP_KEY=your_map_key_here \
  -e FLASK_ENV=production \
  --name pyronexa_app \
  pyronexa:latest
```

The container includes a built-in health check polling `http://localhost:5000/api/health`.

---

## 4. Cloud Platform Deployments

### Render / Railway / Heroku
The workspace contains a `Procfile`:
```
web: gunicorn run:app --bind 0.0.0.0:$PORT --workers 3 --timeout 120
```

#### Steps for Render:
1. Connect your GitHub repository to Render.
2. Select **Web Service** and choose **Python 3**.
3. Build Command: `pip install -r requirements.txt && python3 -m backend.services.sample_data_generator`
4. Start Command: `gunicorn run:app --bind 0.0.0.0:$PORT --workers 3 --timeout 120`
5. Under **Environment Variables**, add:
   - `FLASK_ENV`: `production`
   - `FIRMS_MAP_KEY`: *(Your 32-character NASA FIRMS Map Key, optional)*
6. Deploy.

---

## 5. Security & Secret Management
- **Never commit `.env` or API credentials to version control.**
- The application automatically verifies that `FIRMS_MAP_KEY` is not exposed in HTML views, client-side JavaScript, or HTTP response headers.
- Safe CSV generation protects against formula injection vulnerabilities.
