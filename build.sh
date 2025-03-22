#!/bin/bash
# A simpler build script that avoids the problematic dependencies

echo "Installing dependencies directly from requirements.txt..."
pip install -r requirements.txt

echo "Build completed successfully!" 