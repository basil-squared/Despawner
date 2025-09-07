#!/bin/bash

# Get directory of script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

if [ -f bot.pid ]; then
    PID=$(cat bot.pid)
    echo "Stopping bot process (PID: $PID)..."
    kill $PID
    rm bot.pid
    echo "Bot stopped"
else
    echo "No bot.pid file found"
fi