#!/usr/bin/env bash
set -euo pipefail

python -m venv backend/.venv
backend/.venv/bin/python -m pip install --disable-pip-version-check -r backend/requirements.lock
npm --prefix frontend ci --no-audit --no-fund
