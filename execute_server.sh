#!/usr/bin/env bash
set -euo pipefail

# Initialize conda (works for both Miniconda/Anaconda)
if command -v conda >/dev/null 2>&1; then
source "$(conda info --base)/etc/profile.d/conda.sh"
elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
source "$HOME/anaconda3/etc/profile.d/conda.sh"
else
echo "Conda initialization script not found. Install Miniconda/Anaconda or ensure 'conda' is in PATH." >&2
exit 1
fi

# Activate conda environment
conda activate web

# Navigate to server directory
cd "/Users/estebanamaya/Documents/amayini/server-upload"

# Ensure required deps are installed (idempotent)
python - <<'PY'
import subprocess, sys
pkgs = [
    ("fastapi", None),
    ("uvicorn", None),
    ("jinja2", None),
    ("aiofiles", None),
]
for name, ver in pkgs:
    try:
        __import__(name)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", name + ("=="+ver if ver else "")])
PY

# Start the FastAPI server with multiple workers and tuned backlog
exec uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers "${UVICORN_WORKERS:-2}" \
  --backlog 2048 \
  --timeout-keep-alive 75
