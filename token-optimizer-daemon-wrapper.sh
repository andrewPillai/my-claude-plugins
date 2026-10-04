#!/bin/bash
# Wrapper script for token-optimizer daemon with proper environment

export PATH="/Users/appi/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

# Debug: print environment
echo "[$(date)] Starting token-optimizer daemon" >> /Users/appi/.claude/logs/token-optimizer-daemon-debug.log
echo "  PATH=$PATH" >> /Users/appi/.claude/logs/token-optimizer-daemon-debug.log

# Run the daemon with explicit python path (NOT exec, so we can capture output)
/Users/appi/homebrew/bin/python3 -u /Users/appi/my-claude-plugins/token-optimizer-daemon.py >> /Users/appi/.claude/logs/token-optimizer-daemon.log 2>> /Users/appi/.claude/logs/token-optimizer-daemon.error.log
