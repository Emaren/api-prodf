#!/bin/bash

SESSION="aoe2-dev"

# Kill existing session
tmux kill-session -t $SESSION 2>/dev/null

# Start new session with frontend on the left
tmux new-session -d -s $SESSION -n dev "cd ~/projects/aoe2hd-frontend && npm run dev"

# Split horizontally (right = backend)
tmux split-window -h -t $SESSION:0 "cd ~/projects/aoe2hd-parsing && uvicorn app:app --reload --host 0.0.0.0 --port 8002"

# Rename panes
tmux select-pane -t $SESSION:0.0 -T "Frontend"
tmux select-pane -t $SESSION:0.1 -T "Backend"

# 🔥 Inject the keybinding directly into this tmux session
tmux send-keys -t $SESSION:0 "tmux bind r run-shell '~/projects/aoe2hd-parsing/restart-dev.sh' \; display-message '🔄 Dev session restarted'" C-m

# Attach
tmux attach -t $SESSION
