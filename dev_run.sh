#!/bin/bash
# dev_run.sh
# Helper script to run Python scripts locally with local Postgres override

export APP_PG_HOST=localhost

if [ $# -eq 0 ]; then
  echo "Usage: ./dev_run.sh <script.py> [args...]"
  exit 1
fi

python "$@"
