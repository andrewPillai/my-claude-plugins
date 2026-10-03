#!/bin/bash
# token-optimizer shell initialization
# Source this in your ~/.zshrc or ~/.bashrc to auto-load memories when starting Claude Code

# Configuration
TOKEN_OPTIMIZER_CLI="/Users/appi/.claude/plugins/marketplaces/claude-plugins-official/plugins/token-optimizer/skills/token-optimizer/token_optimizer.py"
AUTO_LOAD_ON_CLAUDE_START=true

# Function to run token-optimizer auto-load
token_optimizer_auto_load() {
    if [[ "$AUTO_LOAD_ON_CLAUDE_START" == "true" ]] && [[ -f "$TOKEN_OPTIMIZER_CLI" ]]; then
        # Run auto-load in background to not delay shell startup
        (python3 "$TOKEN_OPTIMIZER_CLI" load > /dev/null 2>&1) &
    fi
}

# Alias for claude command that auto-loads first
if [[ -n "$ZSH_VERSION" ]]; then
    # Zsh: use preexec hook
    autoload -Uz add-zsh-hook
    _token_optimizer_claude_hook() {
        if [[ "$1" == "claude"* ]] || [[ "$1" == *"claude-code"* ]]; then
            token_optimizer_auto_load
        fi
    }
    add-zsh-hook preexec _token_optimizer_claude_hook
elif [[ -n "$BASH_VERSION" ]]; then
    # Bash: use DEBUG trap or alias
    alias claude='token_optimizer_auto_load; command claude'
    alias claude-code='token_optimizer_auto_load; command claude-code'
fi

# Manual command for testing
alias to-load='python3 "$TOKEN_OPTIMIZER_CLI" load'
alias to-budget='python3 "$TOKEN_OPTIMIZER_CLI" budget'
alias to-mindmap='python3 "$TOKEN_OPTIMIZER_CLI" mindmap'
alias to-stats='python3 "$TOKEN_OPTIMIZER_CLI" stats'
alias to-reset='python3 "$TOKEN_OPTIMIZER_CLI" reset'

echo "🔧 token-optimizer shell init loaded"
echo "   Aliases: to-load, to-budget, to-mindmap, to-stats, to-reset"
echo "   Auto-load on 'claude' command: $AUTO_LOAD_ON_CLAUDE_START"
