#!/bin/bash
# First install with constraints to ensure websockets is at the right version
pip install -c constraints.txt websockets==10.4
# Then install everything else
pip install -r requirements.txt 