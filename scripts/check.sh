#!/usr/bin/env bash
set -euo pipefail

python3 manage.py makemigrations --check --dry-run
python3 manage.py test
