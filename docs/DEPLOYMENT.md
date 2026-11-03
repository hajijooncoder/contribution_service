# Deployment & Operations Guide

## 1. Architectural Principle: Private Deployment Infrastructure
In accordance with MAHOUNN's security boundaries, all server addresses, production network topology, staging container orchestration configurations, and deployment scripts are maintained in a **Private Infrastructure Repository** and are deliberately excluded from this public codebase.

## 2. Containerized Execution
Both Backend and Frontend applications provide multi-stage, non-root Dockerfiles for containerization:

### Backend Container:
- Context: `backend/`
- Dockerfile: `backend/Dockerfile`
- Healthcheck: `GET /health`
- Exposed Port: `8080`

### Frontend Container:
- Context: `frontend/`
- Dockerfile: `frontend/Dockerfile`
- Build Output: Clean static files served via Nginx (non-root)
- Exposed Port: `80`

## 3. Standalone Local Development

### Backend Setup:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

### Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```
Accessible locally at `http://localhost:3000`.
