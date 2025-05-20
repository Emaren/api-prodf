#!/bin/bash

SESSION="aoe2-dev"

# Restart frontend (pane 0)
tmux respawn-pane -t $SESSION:0.0 -k \
  "cd ~/projects/aoe2hd-frontend && npm run dev"

# Restart backend (pane 1)
tmux respawn-pane -t $SESSION:0.1 -k \
  "cd ~/projects/aoe2hd-parsing && uvicorn app:app --reload --host 0.0.0.0 --port 8002"
