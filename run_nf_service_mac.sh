#!/bin/bash

# Change directory to the script's location
cd "$(dirname "$0")"

# Set terminal title
echo -ne "\033]0;NF Service running - Bot 1\007"

# Run your Python script
python3 main.py

# Print status message
echo "===== DONE ====="
echo "Press any key to exit..."
# Wait for a keypress
read -n 1 -s
