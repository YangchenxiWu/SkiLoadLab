#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
.venv/bin/python -m pip install --require-hashes -r requirements.txt
.venv/bin/python -m pip install pip-audit
.venv/bin/pip-audit --strict -r requirements.txt
