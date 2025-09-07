#!/bin/bash

# Get directory of script
SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR"

# Check for poetry
if command -v poetry >/dev/null 2>&1; then
    echo "Activating poetry environment..."
    POETRY_PATH=$(poetry env info --path)
    source "${POETRY_PATH}/bin/activate"
fi

# Start the bot with nohup
echo "Starting bot..."
nohup python3 bot.py > bot.log 2>&1 &

# Save the process ID
echo $! > bot.pid
echo "Bot started with PID $(cat bot.pid)"
echo "Logs are being written to bot.log"