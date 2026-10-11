# Devops Assignment 1 - ACEest Fitness & Gym: CI/CD Pipeline

A Flask REST API for fitness-programme and client management, built incrementally
(v1.0 to v3.0) and delivered through an automated CI/CD pipeline.

## Local setup

1. Python 3.11+ and Git installed.
2. Create and activate a virtual environment:
   - Windows: `python -m venv .venv` then `.\.venv\Scripts\Activate.ps1`
   - Linux/macOS: `python3 -m venv .venv && source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `python app.py` serves the API at http://localhost:5000

## Run the tests manually

    pytest

## Run with Docker

    docker build -t aceest-fitness .
    docker run -d -p 5000:5000 aceest-fitness

## API overview

| Method | Route | Purpose |
|---|---|---|
| GET | /health | Liveness check |
| GET | /programs, /programs/<id> | Programme catalogue |
| POST | /client | Create/update a client and estimate calories |
| GET | /client/<name>, /clients, /clients/export | Read clients, CSV export |
| POST | /progress | Log weekly adherence |
| GET | /client/<name>/progress, /progress-chart | Adherence history / PNG chart |
| POST | /login | Authenticate (default admin / admin123) |
| GET | /client/<name>/report | PDF client report |

## Version history (Git branches and tags)

| Tag | Branch | Feature |
|---|---|---|
| v1.0 | feat/catalog | Programme catalogue |
| v1.1 | feat/client-profile | Client input and calorie estimate |
| v1.2 | feat/multi-client-export | In-memory clients and CSV export |
| v2.0 | feat/sqlite-persistence | SQLite persistence and progress logging |
| v2.1 | feat/progress-chart | Progress history and chart |
| v3.0 | feat/login-and-report | Login and PDF report |

## CI/CD

### GitHub Actions (`.github/workflows/main.yml`)
Runs on every push and pull request: install dependencies, build and lint
(`py_compile`, `flake8`), run Pytest, build the Docker image, and run Pytest
again inside the container.

### Jenkins (`Jenkinsfile`)
Job type: Pipeline, "Pipeline script from SCM", branch `*/main`.
Trigger: Poll SCM (`H/2 * * * *`). A webhook is not used because the Jenkins
host is not reachable from GitHub.

Stages: Checkout, Clean Build, Unit Tests (JUnit report), Docker Build,
Deploy to Staging (port 5001), manual approval, Deploy to Production
(port 5002) with a health check and automatic rollback.

Deployment strategy: staged promotion with health-check-gated rollback.

## Environments

| Environment | URL |
|---|---|
| Development | http://localhost:5000 |
| Staging | http://10.3.26.245:5001 |
| Production | http://10.3.26.245:5002 |

## Evidence

- **Screenshots and Recording:** [DevOps Assignment 1 Evidence Repository](https://github.com/poorva-bits/assignment-1-devops-evidence)
- **Recording on Drive:** [View Video on Google Drive](https://drive.google.com/file/d/1SjpRs1_K90hQR__GEqAsGhZDABTnsPKQ/view?usp=sharing)
