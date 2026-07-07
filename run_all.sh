#!/bin/bash

tmux new-session -d -s invigilation

tmux send-keys -t invigilation "cd backend && source venv/bin/activate && uvicorn main:app --reload" C-m

tmux split-window -h -t invigilation
tmux send-keys -t invigilation "cd frontend/AI && npm install && npm run dev" C-m

tmux split-window -v -t invigilation
tmux send-keys -t invigilation "cd ai && python main.py" C-m

tmux attach -t invigilation
