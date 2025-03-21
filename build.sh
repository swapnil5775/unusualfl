#!/bin/bash
# Exit on error
set -e

echo "Installing system dependencies..."
apt-get update -y || true
apt-get install -y python3-dev python3.9-dev build-essential || true

echo "Installing binary packages first..."
pip install -r requirements-binary.txt || echo "Failed to install some binary packages, continuing anyway"

echo "Installing remaining dependencies..."
pip install -r requirements.txt

echo "Build completed successfully!" 