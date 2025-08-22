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

# Start the FastAPI server
exec python main.py
