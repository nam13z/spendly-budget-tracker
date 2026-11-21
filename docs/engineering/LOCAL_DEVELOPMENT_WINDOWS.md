# Native Windows Development

> **Status:** Windows remains suitable for editing and frontend work, but the current Smart App Control policy blocks the compiled Pydantic Core extension required by FastAPI. Keep Smart App Control enabled and use [GitHub Codespaces](CODESPACES.md) for backend and database development.

This legacy guide records the previous local Windows setup. It uses the existing Windows MySQL instance and must not be used to configure Codespaces. Never copy the Windows database password into a Codespace. Production and deployment guidance is separate in [DEPLOYMENT.md](DEPLOYMENT.md).

## Prerequisites

- Python 3.14.x and pip
- Node.js 26.x and npm
- MySQL Server 8.4 running locally
- Git

The application uses MySQL at `127.0.0.1:3307`, database `spendly`, application user `spendly_app`. The database password is supplied privately through a local environment file and must never be committed or printed.

## Configure the backend

From the repository root, create a private local `.env` from the safe template:

```powershell
Copy-Item .env.example .env
notepad .env
```

Set `DB_PASSWORD` in `.env` to the privately configured application password. Do not paste it into command lines, source files, logs, or support output. `.env` is ignored by Git.

Create a virtual environment and install the pinned backend dependencies:

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.lock
```

Start the API from the backend directory so the root `.env` is found explicitly through the configured path:

```powershell
Set-Location backend
$env:PYTHONPATH = (Get-Location).Path
$env:ENV_FILE = (Resolve-Path ..\.env).Path
uvicorn app.main:app --reload --env-file $env:ENV_FILE
```

The API is available at `http://127.0.0.1:8000`. `GET /health/live` checks that the process responds. `GET /health/ready` executes a read-only `SELECT 1` against MySQL and returns only a generic unavailable response if the connection fails.

## Start the frontend

In a second PowerShell window, from the repository root:

```powershell
Set-Location frontend
npm ci
$env:NEXT_TELEMETRY_DISABLED = "1"
npm run dev
```

Open `http://localhost:3000`. The server-rendered starting page checks `http://127.0.0.1:8000/health/live`. If the API uses a different URL, set `BACKEND_URL` in that PowerShell session before `npm run dev`.

## Quality checks

Backend (from repository root, with the venv activated):

```powershell
Set-Location backend
ruff check app tests
pytest
```

Frontend (from `frontend/`):

```powershell
npm run lint
npm run typecheck
$env:NEXT_TELEMETRY_DISABLED = "1"
npm run build
```

## Configuration reference

| Variable | Default/template | Purpose |
|---|---|---|
| `APP_ENV` | `development` | Runtime environment label |
| `DB_HOST` | `127.0.0.1` | MySQL host |
| `DB_PORT` | `3307` | MySQL port |
| `DB_NAME` | `spendly` | Database name |
| `DB_USER` | `spendly_app` | Least-privilege application account |
| `DB_PASSWORD` | Set privately in `.env` | MySQL credential; required by backend settings |
| `BACKEND_URL` | `http://127.0.0.1:8000` | Backend URL used by the frontend server-side health check |

The SQLAlchemy URL is built from individual validated fields, which safely handles special characters in the password. Credentials are not included in readiness responses.

## Troubleshooting

- **PowerShell blocks activation:** run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate the venv again. This only changes the current PowerShell process.
- **Settings validation reports a missing password:** confirm `DB_PASSWORD` is set in the repository root `.env`; never print the file to diagnose this.
- **Readiness returns 503:** confirm the MySQL Windows service is running, listening on port 3307, and the private application credentials match the configured database grants. The probe does not create or modify tables.
- **Frontend reports the API unavailable:** start the backend and check `http://127.0.0.1:8000/health/live`; set `BACKEND_URL` in the frontend terminal if using another backend address.
- **npm or pip install fails:** check network/proxy access and the displayed package compatibility error. Keep lockfiles intact and resolve package version changes through review.
- **Port is occupied:** identify the local process using port 8000 or 3000 and stop it, or use the framework's documented port option and update `BACKEND_URL` accordingly.

This phase does not create schema, models, migrations or seed data. MySQL must already contain the `spendly` database and the application account must have permission to connect.
