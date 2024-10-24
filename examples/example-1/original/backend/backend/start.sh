#! /usr/bin/env sh
set -e

./prestart.sh

python3 -m uvicorn app.main:app --host "0.0.0.0" --port 8000
