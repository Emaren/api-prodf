#!/bin/bash

SESSION="aoe2dev"
tmux kill-session -t $SESSION 2>/dev/null

# ----------------------------
# Step 1: Create the main window ("dev") with Backend and Frontend side by side.
# ----------------------------
tmux new-session -d -s $SESSION -n dev 'cd ~/projects/aoe2hd-parsing && uvicorn main:app --reload --port=8002'
tmux split-window -h -t $SESSION:dev 'cd ~/projects/aoe2hd-parsing && python watch_replays.py'
tmux select-layout -t $SESSION:dev even-horizontal

# ----------------------------
# Step 2: Create a separate watcher window running the watcher.
# ----------------------------
tmux new-window -t $SESSION -n watcher 'cd ~/projects/aoe2hd-frontend && npm run dev'

# ----------------------------
# Step 3: Join the watcher pane into the main window as a full-width bottom pane.
# ----------------------------
tmux join-pane -v -s $SESSION:watcher.0 -t $SESSION:dev.0

# Kill the now empty watcher window.
tmux kill-window -t $SESSION:watcher

# ----------------------------
# Step 4: Force a tiled layout to ensure top panes stay side-by-side and the watcher spans full width.
# ----------------------------
tmux select-layout -t $SESSION:dev tiled

# (Optional) Force a large width on the watcher pane in case tmux doesn't expand it:
tmux resize-pane -x 2000 -t $SESSION:dev.2

# Focus on the backend pane (pane 0) for convenience.
tmux select-pane -t $SESSION:dev.0

# Attach to the session.
tmux attach-session -t $SESSION
