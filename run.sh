#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
VENV="$DIR/.venv"

if [[ ! -d "$VENV" ]]; then
    echo "Setting up environment (first run)..."
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install --quiet --upgrade pip
    "$VENV/bin/pip" install --quiet -e "$DIR"
    echo "Done."
fi

exec "$VENV/bin/python" -m pulse "$@"
