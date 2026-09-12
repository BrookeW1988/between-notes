#!/bin/bash
set -e
cd "$(dirname "$0")"
if [ -x .venv/bin/python ]; then
  runtime=.venv/bin/python
else
  echo 'Run setup.sh first. See README.md for instructions.'
  exit 1
fi
printf 'Open http://127.0.0.1:%s in your browser. Keep this window open. Press Control+C to stop.\n' "${PORT:-5179}"
exec "$runtime" app.py
