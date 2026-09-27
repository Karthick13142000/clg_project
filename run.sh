#!/usr/bin/env bash
# Set up a virtualenv, install dependencies, and start EduGenie.
set -euo pipefail

cd "$(dirname "$0")"

PYTHON="${PYTHON:-}"

# Pick the newest Python 3.9+ on this machine. Ubuntu 20.04 ships python3.8 by
# default, which google-generativeai does not support, so fall back through the
# versioned names before giving up.
if [ -z "$PYTHON" ]; then
  for candidate in python3.13 python3.12 python3.11 python3.10 python3.9 python3 \
                   "$HOME/.local/share/python/python/bin/python3.11" \
                   "$HOME/.local/share/python/python/bin/python3" \
                   "$HOME/.local/share/python/bin/python3"; do
    if command -v "$candidate" >/dev/null 2>&1 &&
       "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' 2>/dev/null; then
      PYTHON="$candidate"
      break
    fi
  done
fi

if [ -z "$PYTHON" ]; then
  echo "Python 3.9+ not found. Install it, e.g. on Ubuntu 20.04:" >&2
  echo "  sudo add-apt-repository -y ppa:deadsnakes/ppa" >&2
  echo "  sudo apt install -y python3.11 python3.11-venv" >&2
  echo "Then re-run ./run.sh, or set PYTHON=/path/to/python3.11 ./run.sh" >&2
  exit 1
fi

echo "Using $PYTHON ($("$PYTHON" --version 2>&1))"

if [ ! -d .venv ]; then
  echo "Creating virtualenv in .venv ..."
  "$PYTHON" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Installing dependencies ..."
python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example - add your GEMINI_API_KEY there."
fi

echo "Starting EduGenie on http://127.0.0.1:${PORT:-5000}"
python app.py
