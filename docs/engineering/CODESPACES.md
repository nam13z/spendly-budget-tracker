# GitHub Codespaces Development

Spendly's supported development environment is a Linux GitHub Codespace. It runs the Next.js frontend and FastAPI backend in one workspace container, with MySQL 8.4 in a separate Compose service on the same private container network. Production deployment remains covered separately in [DEPLOYMENT.md](DEPLOYMENT.md).

## Create or rebuild a Codespace

1. Push the approved branch containing `.devcontainer/` configuration to GitHub.
2. On the repository page, select **Code → Codespaces → Create codespace on `feature/native-windows-foundation`**.
3. Wait for the Dev Container to build and its post-create setup to finish. It creates `backend/.venv`, installs the pinned Python lockfile and runs `npm ci` for the frontend.
4. For an existing Codespace, run **Codespaces: Rebuild Container** to apply configuration changes. A full rebuild is only needed when the base image or image-build instructions change.

The workspace image pins Python 3.14.10 and Node.js 26.13.1. The same versions are used by CI. The Codespace Compose project starts MySQL 8.4.9, waits for its health check, and provides the application settings `DB_HOST=mysql` and `DB_PORT=3306`.

## Start the applications

Open two integrated terminals at the repository root.

Terminal 1 — FastAPI:

```bash
backend/.venv/bin/uvicorn --app-dir backend app.main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 — Next.js:

```bash
npm --prefix frontend run dev -- --hostname 0.0.0.0
```

Open the forwarded **Spendly frontend** port (3000). Its server-side health check calls FastAPI at `http://127.0.0.1:8000`; the browser is not given internal service addresses.

## Check application and database health

From another Codespace terminal:

```bash
curl --fail http://127.0.0.1:8000/health/live
curl --fail http://127.0.0.1:8000/health/ready
```

Liveness confirms the API process responds. Readiness performs a read-only `SELECT 1` using the Compose service host and port. The frontend page also shows whether the API liveness check succeeds.

To open a MySQL client in the database container:

```bash
docker compose -f .devcontainer/docker-compose.yml exec mysql mysql --user=spendly_app --password spendly
```

The client prompts for the disposable development password. It is declared in `.devcontainer/docker-compose.yml` for isolated Codespaces development only. The app user and container root password are publicly visible development credentials, not secrets; never reuse them for Windows MySQL, production, or another service. No Codespaces secret is needed for this disposable database. Future external-service credentials must use Codespaces secrets at runtime, not image build arguments or Dockerfiles.

MySQL is available only to Compose services on the Codespace network. Its port is neither published nor forwarded.

## Forwarded ports

| Port | Service | Visibility |
|---|---|---|
| 3000 | Next.js frontend | Private; browser access |
| 8000 | FastAPI API | Private; optional API debugging |
| 3306 | MySQL | Not forwarded or published |

The Dev Container configuration marks both application ports private explicitly. GitHub Codespaces supports automatic port forwarding and private visibility for forwarded ports. [GitHub port-forwarding guidance](https://docs.github.com/en/codespaces/developing-in-a-codespace/forwarding-ports-in-your-codespace)

## Stop, resume, and reset

- **Stop:** use the Codespaces menu to stop the Codespace. This stops compute while preserving the Codespace and its named MySQL volume.
- **Resume:** reopen that Codespace from the repository's Codespaces menu. Compose restarts the services and reuses the existing MySQL volume.
- **Reset only the disposable database:** this permanently removes all development database contents. From the workspace terminal, run:

  ```bash
  docker compose -f .devcontainer/docker-compose.yml stop mysql
  docker compose -f .devcontainer/docker-compose.yml rm --force mysql
  docker volume rm spendly-codespaces-mysql-data
  docker compose -f .devcontainer/docker-compose.yml up --detach mysql
  docker compose -f .devcontainer/docker-compose.yml ps
  ```

  Wait for the MySQL health check to pass, then restart FastAPI so it opens a fresh connection pool. The Docker-outside-of-Docker Dev Container feature provides the Docker CLI/socket needed for this reset operation.

## Windows local development

Native Windows backend and frontend verification has passed in the owner's environment. Keep Smart App Control enabled; use Codespaces when a local policy blocks a compiled dependency. Do not connect Codespaces to the Windows MySQL instance or copy its password into the Codespace.

The native setup guide is in [LOCAL_DEVELOPMENT_WINDOWS.md](LOCAL_DEVELOPMENT_WINDOWS.md). Its local MySQL settings are Windows-only; Codespaces overrides them with the internal MySQL service address and disposable development credentials.

The database-foundation migration creates the application schema and seeds `LKR` and `USD` in the configured disposable Codespaces MySQL database. FX rates remain excluded until precision is approved. This is not a production deployment configuration.
