#!/bin/bash

# Start a tmux session for fullstack development
SESSION="aoe2-dev"

# Kill if already running
tmux kill-session -t $SESSION 2>/dev/null

# Start frontend (left pane)
tmux new-session -d -s $SESSION -n dev "cd ~/projects/aoe2hd-frontend && npm run dev"

# Start backend (right pane)
tmux split-window -h -t $SESSION:0 "cd ~/projects/aoe2hd-parsing && ENV=development uvicorn app:app --reload --host 0.0.0.0 --port 8002"

# Rename panes
tmux select-pane -t $SESSION:0.0 -T "Frontend"
tmux select-pane -t $SESSION:0.1 -T "Backend"

# Add hot reload shortcut (r key)
tmux send-keys -t $SESSION:0 "tmux bind r run-shell '~/projects/aoe2hd-parsing/restart-dev.sh' \; display-message '🔄 Dev session restarted'" C-m

# Attach to session
tmux attach -t $SESSION
