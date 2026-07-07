# Invigilation Duty Anomaly Detection

AI-powered exam monitoring system with:
- FastAPI backend
- AI detection engine
- React frontend dashboard
- SQLite persistence
- PDF report generation

## Backend

Run from the `backend/` folder:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

API:
- `GET /`
- `GET /health`
- `POST /detect`
- `GET /alerts`
- `GET /risk-score`
- `GET /report`
- `DELETE /alerts`

## AI Engine

Run from the `ai/` folder:

```bash
cd ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

The AI dispatcher posts anomaly payloads to:

```text
http://127.0.0.1:8000/detect
```

## Frontend

Run from the `frontend/` folder:

```bash
cd frontend
npm install
npm run dev
```

The wrapper workspace runs the Vite app in `frontend/AI/`.

## Flow

Camera -> AI Engine -> Backend `/detect` -> SQLite -> Frontend Dashboard -> PDF Report

