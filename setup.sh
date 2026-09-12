#!/bin/bash
set -e
cd "$(dirname "$0")"
# Python 3.12 is a stable target for Presidio, spaCy and local OCR dependencies.
"${PYTHON_BIN:-python3.12}" -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m spacy download en_core_web_sm
printf 'Setup complete. Run ./start.command and open http://127.0.0.1:5179\n'
