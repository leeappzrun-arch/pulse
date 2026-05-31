#!/usr/bin/env bash
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$DIR/.venv"

if [[ ! -d "$VENV" ]]; then
    echo "Run ./run.sh first to create the environment."
    exit 1
fi

"$VENV/bin/pip" install --quiet "pytest>=8.0" "pytest-asyncio>=0.23"
exec "$VENV/bin/pytest" "$@"
