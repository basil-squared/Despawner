#!/bin/bash

# Get directory of script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Activate poetry environment if it exists
if command -v poetry &> /dev/null; then
    echo "Activating poetry environment..."
    eval "$(poetry env info --path)/bin/activate"
fi

# Start the bot with nohup
echo "Starting bot..."
nohup python3 bot.py > bot.log 2>&1 &

# Save the process ID
echo $! > bot.pid
echo "Bot started with PID $(cat bot.pid)"
echo "Logs are being written to bot.log"